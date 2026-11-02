from pathlib import Path

import pytest

from vitae.config import parse_config
from vitae.knowledge import budget_rows, load_knowledge, render_self

CONFIG = """
active_model = "small"
system_prompt_tokens = 300

[models."small"]
name = "Qwen3.5-4B"
file = "a.gguf"
quantization = "Q4_0"
prefix_budget_tokens = 3000

[models."large"]
name = "Qwen3.5-2B"
file = "b.gguf"
quantization = "Q4_0"
prefix_budget_tokens = 10000

[tokenizer]
url = "https://example.invalid/tokenizer.json"
sha256 = "0"

[runtime]
name = "llama.cpp"
version = "v0.8.0"

[host]
provider = "Oracle Cloud"
shape = "an Ampere A1 virtual machine"

[retrieval]
embedder = "BAAI/bge-small-en-v1.5"
keyword = "BM25"
fusion = "reciprocal rank fusion"
reranker = "a cross-encoder reranker"
embedder_repo = "Qdrant/bge-small-en-v1.5-onnx-Q"
embedder_revision = "aa8f8b06"
reranker_repo = "Xenova/ms-marco-MiniLM-L-6-v2"
reranker_revision = "a0914435"
refuse_below = 0.0

[benchmark]
classic_rag_ttft_seconds = 32
cached_ttft_seconds = 5.5
"""


def test_self_doc_describes_the_active_model_and_host():
    text = render_self(parse_config(CONFIG))

    assert "It runs Qwen3.5-4B (Q4_0) on llama.cpp v0.8.0, self-hosted on Oracle Cloud as an Ampere A1 virtual machine." in text
    assert "took about 32 seconds" in text
    assert "down to about 5.5 seconds" in text


def test_unknown_active_model_is_rejected():
    with pytest.raises(ValueError, match="active_model 'tiny'"):
        parse_config(CONFIG.replace('active_model = "small"', 'active_model = "tiny"'))


def test_knowledge_skips_reports_and_sources_and_strips_frontmatter(tmp_path: Path):
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "notes.md").write_text("private", encoding="utf-8")
    (tmp_path / "_conflicts.md").write_text("report", encoding="utf-8")
    (tmp_path / "site").mkdir()
    (tmp_path / "site" / "projects.md").write_text("---\nsource: x\n---\n\n# Projects\n", encoding="utf-8")
    (tmp_path / "about.md").write_text("# About me\r\n", encoding="utf-8")

    docs = load_knowledge(tmp_path)

    assert [(doc.path, doc.body) for doc in docs] == [("about.md", "# About me"), ("site/projects.md", "# Projects")]


def test_budget_rows_add_the_system_prompt_and_flag_overruns():
    rows = budget_rows(parse_config(CONFIG), knowledge_tokens=2800)

    assert [(row.model, row.prefix_tokens, row.fits) for row in rows] == [("small", 3100, False), ("large", 3100, True)]
