import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Model:
    name: str
    file: str
    quantization: str
    prefix_budget_tokens: int


@dataclass(frozen=True)
class Config:
    active_model: str
    contact_email: str
    models: dict[str, Model]
    system_prompt_tokens: int
    tokenizer_url: str
    tokenizer_sha256: str
    runtime: str
    runtime_version: str
    host_provider: str
    host_shape: str
    embedder: str
    keyword: str
    fusion: str
    reranker: str
    embedder_repo: str
    embedder_revision: str
    reranker_repo: str
    reranker_revision: str
    refuse_below: float
    classic_rag_ttft_seconds: float
    cached_ttft_seconds: float

    @property
    def model(self) -> Model:
        return self.models[self.active_model]


def parse_config(text: str) -> Config:
    raw = tomllib.loads(text)
    models = {key: Model(**value) for key, value in raw["models"].items()}
    if raw["active_model"] not in models:
        raise ValueError(f"active_model {raw['active_model']!r} is not one of {sorted(models)}")
    return Config(
        active_model=raw["active_model"],
        contact_email=raw["contact_email"],
        models=models,
        system_prompt_tokens=raw["system_prompt_tokens"],
        tokenizer_url=raw["tokenizer"]["url"],
        tokenizer_sha256=raw["tokenizer"]["sha256"],
        runtime=raw["runtime"]["name"],
        runtime_version=raw["runtime"]["version"],
        host_provider=raw["host"]["provider"],
        host_shape=raw["host"]["shape"],
        embedder=raw["retrieval"]["embedder"],
        keyword=raw["retrieval"]["keyword"],
        fusion=raw["retrieval"]["fusion"],
        reranker=raw["retrieval"]["reranker"],
        embedder_repo=raw["retrieval"]["embedder_repo"],
        embedder_revision=raw["retrieval"]["embedder_revision"],
        reranker_repo=raw["retrieval"]["reranker_repo"],
        reranker_revision=raw["retrieval"]["reranker_revision"],
        refuse_below=raw["retrieval"]["refuse_below"],
        classic_rag_ttft_seconds=raw["benchmark"]["classic_rag_ttft_seconds"],
        cached_ttft_seconds=raw["benchmark"]["cached_ttft_seconds"],
    )


def load_config(path: Path) -> Config:
    return parse_config(path.read_text(encoding="utf-8"))
