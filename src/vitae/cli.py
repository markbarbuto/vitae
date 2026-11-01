import argparse
import sys
from pathlib import Path

from vitae.config import load_config
from vitae.knowledge import (
    QwenTokenizer,
    budget_rows,
    fetch_tokenizer,
    load_knowledge,
    prefix_text,
    render_self,
)


def knowledge(root: Path, check: bool) -> int:
    config = load_config(root / "config" / "assistant.toml")
    self_doc = root / "knowledge" / "generated" / "self.md"
    self_doc.parent.mkdir(parents=True, exist_ok=True)
    self_doc.write_text(render_self(config), encoding="utf-8", newline="\n")

    tokenizer = QwenTokenizer(fetch_tokenizer(config, root / ".cache" / "tokenizer"))
    docs = load_knowledge(root / "knowledge")
    for doc in docs:
        print(f"{tokenizer.count(doc.body):>6}  {doc.path}")
    knowledge_tokens = tokenizer.count(prefix_text(docs))
    print(f"{knowledge_tokens:>6}  knowledge total")
    print(f"{config.system_prompt_tokens:>6}  system prompt (estimate)")

    rows = budget_rows(config, knowledge_tokens)
    for row in rows:
        marker = "*" if row.model == config.active_model else " "
        verdict = "fits" if row.fits else f"over by {row.prefix_tokens - row.budget}"
        print(f"{marker} {row.model:<12} prefix {row.prefix_tokens} / budget {row.budget}: {verdict}")

    active = next(row for row in rows if row.model == config.active_model)
    return 1 if check and not active.fits else 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="assistant")
    commands = parser.add_subparsers(dest="command", required=True)
    knowledge_cmd = commands.add_parser("knowledge", help="regenerate self.md and report the prefix token budget")
    knowledge_cmd.add_argument("--root", type=Path, default=Path("."))
    knowledge_cmd.add_argument("--check", action="store_true", help="exit 1 if the active model's budget is exceeded")
    args = parser.parse_args()
    sys.exit(knowledge(args.root, args.check))
