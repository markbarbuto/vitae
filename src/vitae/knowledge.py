import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from vitae.config import Config


@dataclass(frozen=True)
class KnowledgeDoc:
    path: str
    body: str


@dataclass(frozen=True)
class BudgetRow:
    model: str
    budget: int
    prefix_tokens: int

    @property
    def fits(self) -> bool:
        return self.prefix_tokens <= self.budget


class Tokenizer(Protocol):
    def count(self, text: str) -> int: ...


def render_self(config: Config) -> str:
    model = config.model
    return f"""---
source: config/assistant.toml
visibility: public
generated: true
---

# This assistant

## How this assistant works

I built this assistant, Vitae AI, to answer questions about my career, projects and interests. It runs {model.name} ({model.quantization}) on {config.runtime} {config.runtime_version}, self-hosted on {config.host_provider} as {config.host_shape}. It doesn't send questions to a third-party AI service.

## Architecture

The assistant uses cache-augmented generation. My whole knowledge base, which is my resume, my website's content and answers I wrote myself, sits in the model's cached context. Hybrid retrieval combines {config.embedder} embeddings with {config.keyword} keyword search, fuses them with {config.fusion}, and reranks the results with {config.reranker}. Retrieval picks the most relevant sections as focus hints, refuses questions my knowledge base can't answer, and records which sources were used.

## Why not classic retrieval-augmented generation

On the 2-core host, a classic RAG prompt took about {config.classic_rag_ttft_seconds:g} seconds before the first word appeared. Keeping the whole knowledge base cached brought first answers down to about {config.cached_ttft_seconds:g} seconds, so I chose cache-augmented generation.
"""


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text.strip()
    end = text.index("\n---\n", 4)
    return text[end + 5 :].strip()


def load_knowledge(root: Path) -> list[KnowledgeDoc]:
    docs = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if relative.parts[0] == "sources" or path.name.startswith("_"):
            continue
        body = strip_frontmatter(path.read_text(encoding="utf-8").replace("\r\n", "\n"))
        docs.append(KnowledgeDoc(path=relative.as_posix(), body=body))
    return docs


def prefix_text(docs: list[KnowledgeDoc]) -> str:
    return "\n\n".join(doc.body for doc in docs)


def budget_rows(config: Config, knowledge_tokens: int) -> list[BudgetRow]:
    prefix = config.system_prompt_tokens + knowledge_tokens
    return [
        BudgetRow(model=key, budget=model.prefix_budget_tokens, prefix_tokens=prefix)
        for key, model in config.models.items()
    ]


class QwenTokenizer:
    def __init__(self, path: Path) -> None:
        from tokenizers import Tokenizer as HfTokenizer

        self._tokenizer = HfTokenizer.from_file(str(path))

    def count(self, text: str) -> int:
        return len(self._tokenizer.encode(text, add_special_tokens=False).ids)


def fetch_tokenizer(config: Config, cache_dir: Path) -> Path:
    path = cache_dir / f"{config.tokenizer_sha256}.json"
    if not path.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        data = urllib.request.urlopen(config.tokenizer_url, timeout=60).read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != config.tokenizer_sha256:
            raise ValueError(f"tokenizer sha256 {digest} does not match config {config.tokenizer_sha256}")
        path.write_bytes(data)
    return path
