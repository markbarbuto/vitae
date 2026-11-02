import re
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from vitae.config import Config
from vitae.knowledge import KnowledgeDoc

MAX_WORDS = 260
CANDIDATES = 20
RERANK = 12
RERANK_WORDS = 120
RRF_K = 60
FOLD = [(r"\byour(s)?\b", "Mark's"), (r"\b(you|yourself)\b", "Mark"), (r"\bu\b(?! of\b)", "Mark")]


@dataclass(frozen=True)
class Topic:
    name: str
    keywords: str


@dataclass(frozen=True)
class Chunk:
    topic: Topic
    section: str
    breadcrumb: str
    text: str

    @property
    def search_text(self) -> str:
        return "\n".join(part for part in (self.topic.name, self.topic.keywords, self.breadcrumb, self.text) if part)


@dataclass(frozen=True)
class Hit:
    topic: str
    score: float


@dataclass(frozen=True)
class Retrieval:
    relevance: float
    hits: tuple[Hit, ...]

    def refused(self, below: float) -> bool:
        return self.relevance < below


def load_topics(path: Path) -> dict[str, Topic]:
    topics = tomllib.loads(path.read_text(encoding="utf-8"))["topics"]
    return {section: Topic(name, entry.get("keywords", "")) for name, entry in topics.items() for section in entry["sections"]}


def topic_problems(path: Path, known_sections: set[str]) -> list[str]:
    topics = tomllib.loads(path.read_text(encoding="utf-8"))["topics"]
    listed = Counter(section for entry in topics.values() for section in entry["sections"])
    return (
        [f"{section} is in no topic" for section in sorted(known_sections - set(listed))]
        + [f"{section} is in a topic but not the knowledge base" for section in sorted(set(listed) - known_sections)]
        + [f"{section} is in {count} topics" for section, count in sorted(listed.items()) if count > 1]
    )


def _packs(paragraphs: list[str]) -> list[str]:
    packs, current = [], []
    for paragraph in paragraphs:
        if current and len(" ".join(current + [paragraph]).split()) > MAX_WORDS:
            packs.append("\n\n".join(current))
            current = []
        current.append(paragraph)
    return packs + ["\n\n".join(current)] if current else packs


def chunk_docs(docs: list[KnowledgeDoc], topic_of: dict[str, Topic]) -> list[Chunk]:
    chunks = []
    for doc in docs:
        title = next((line[2:].strip() for line in doc.body.splitlines() if line.startswith("# ")), doc.path)
        for block in doc.body.split("\n## ")[1:]:
            heading, _, body = block.partition("\n")
            section, crumb = f"{doc.path}#{heading.strip()}", f"Mark Barbuto > {title} > {heading.strip()}"
            topic = topic_of[section]
            if len(body.split()) <= MAX_WORDS:
                chunks.append(Chunk(topic, section, crumb, body.strip()))
                continue
            intro, *subsections = body.split("\n### ")
            parts = [("", intro)] + [(sub.partition("\n")[0].strip(), sub.partition("\n")[2]) for sub in subsections]
            for sub, text in parts:
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                for pack in _packs(paragraphs):
                    chunks.append(Chunk(topic, section, f"{crumb} > {sub}" if sub else crumb, pack))
    return chunks


def load_aliases(path: Path) -> dict[str, str]:
    return tomllib.loads(path.read_text(encoding="utf-8"))["aliases"]


def query_for(turns: tuple[str, ...], aliases: dict[str, str]) -> str:
    query = " ".join(turns[-2:])
    expansions = [full for short, full in aliases.items() if re.search(rf"\b{re.escape(short)}\b", query, re.IGNORECASE)]
    query = " ".join([query, *expansions])
    for pattern, replacement in FOLD:
        query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
    return query


def fetch_model(repo: str, revision: str, models_dir: Path) -> Path:
    from huggingface_hub import snapshot_download

    target = models_dir / f"{repo.replace('/', '--')}-{revision[:8]}"
    snapshot_download(repo, revision=revision, local_dir=target, allow_patterns=["*.json", "*.txt", "*.onnx"])
    return target


class Retriever:
    def __init__(self, chunks: list[Chunk], config: Config, models_dir: Path) -> None:
        import bm25s
        from fastembed import TextEmbedding
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.chunks = chunks
        self._embedder = TextEmbedding(
            config.embedder, specific_model_path=str(fetch_model(config.embedder_repo, config.embedder_revision, models_dir))
        )
        self._reranker = TextCrossEncoder(
            config.reranker_repo, specific_model_path=str(fetch_model(config.reranker_repo, config.reranker_revision, models_dir))
        )
        texts = [chunk.search_text for chunk in chunks]
        self._vectors = np.array(list(self._embedder.embed(texts)))
        self._bm25 = bm25s.BM25()
        self._bm25.index(bm25s.tokenize(texts, stopwords="en", show_progress=False), show_progress=False)
        self._tokenize = lambda text: bm25s.tokenize([text], stopwords="en", return_ids=False, show_progress=False)

    def _keyword(self, query: str) -> list[int]:
        tokens = self._tokenize(query)
        if not tokens[0]:
            return []
        ids, scores = self._bm25.retrieve(tokens, k=min(CANDIDATES, len(self.chunks)), show_progress=False)
        return [int(i) for i, score in zip(ids[0], scores[0]) if score > 0]

    def search(self, query: str, refuse_below: float = float("-inf")) -> Retrieval:
        similarity = self._vectors @ next(iter(self._embedder.query_embed(query)))
        relevance = float(similarity.max())
        if relevance < refuse_below:
            return Retrieval(relevance, ())
        fused: dict[int, float] = {}
        for ranking in (np.argsort(-similarity)[:CANDIDATES].tolist(), self._keyword(query)):
            for rank, index in enumerate(ranking):
                fused[index] = fused.get(index, 0.0) + 1 / (RRF_K + rank + 1)
        top = sorted(fused, key=fused.get, reverse=True)[:RERANK]
        best: dict[str, float] = {}
        for index, score in zip(top, self._reranker.rerank(query, [" ".join(self.chunks[i].search_text.split()[:RERANK_WORDS]) for i in top])):
            topic = self.chunks[index].topic.name
            best[topic] = max(best.get(topic, float("-inf")), float(score))
        return Retrieval(relevance, tuple(Hit(t, s) for t, s in sorted(best.items(), key=lambda item: item[1], reverse=True)))
