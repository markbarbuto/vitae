import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from vitae.calibration import agreement, parse_sheet, render_sheet, sample
from vitae.config import load_config
from vitae.golden import Category, load_golden, problems, section_ids
from vitae.judge import judge
from vitae.llm import chat
from vitae.prompt import system_message, user_message
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


def golden(root: Path) -> int:
    items = load_golden(root / "eval" / "golden")
    counts = Counter((item.category, item.split) for item in items)
    for category in Category:
        print(f"{category.value:<13} dev {counts[(category, 'dev')]:>3}  test {counts[(category, 'test')]:>3}")
    print(f"{'total':<13} dev {sum(item.split == 'dev' for item in items):>3}  test {sum(item.split == 'test' for item in items):>3}")
    found = problems(items, section_ids(load_knowledge(root / "knowledge")))
    for problem in found:
        print(f"problem: {problem}")
    return 1 if found else 0


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def calibrate(root: Path, step: str, name: str, server: str) -> int:
    tune = root / "eval" / "calibration"
    folder = tune if name == "tune" else tune / name
    folder.mkdir(parents=True, exist_ok=True)
    docs = load_knowledge(root / "knowledge")
    items = {item.id: item for item in load_golden(root / "eval" / "golden")}
    answers = folder / "answers.jsonl"

    if step == "answers":
        config = load_config(root / "config" / "assistant.toml")
        rows = []
        exclude = frozenset() if name == "tune" else frozenset(row["id"] for row in read_jsonl(tune / "answers.jsonl"))
        for item in sample(list(items.values()), name, exclude):
            message = chat(
                server,
                [{"role": "system", "content": system_message(docs)}, {"role": "user", "content": user_message(item.turns)}],
                temperature=0.3,
                top_p=0.9,
                max_tokens=220,
                chat_template_kwargs={"enable_thinking": False},
            )
            rows.append({"id": item.id, "answer": message["content"].strip(), "source": config.active_model})
            print(f"{item.id}: {rows[-1]['answer']}")
        write_jsonl(answers, rows)
        return 0

    if step == "sheet":
        sheet = folder / "labels.md"
        if sheet.exists():
            print(f"{sheet} already exists; delete it first to start labelling over")
            return 1
        rows = read_jsonl(answers)
        random.Random(0).shuffle(rows)
        sheet.write_text(render_sheet([(items[row["id"]], row["answer"]) for row in rows], name), encoding="utf-8", newline="\n")
        print(f"wrote {sheet}")
        return 0

    if step == "judge":
        saved = folder / "judge.jsonl"
        rows = read_jsonl(saved) if saved.exists() else []
        done = {row["id"] for row in rows}
        for row in read_jsonl(answers):
            if row["id"] in done:
                continue
            verdict = judge(server, docs, items[row["id"]], row["answer"])
            rows.append({"id": row["id"], **asdict(verdict), "correct": verdict.correct, "faithful": verdict.faithful})
            write_jsonl(folder / "judge.jsonl", rows)
            print(f"{row['id']}: correct={verdict.correct} faithful={verdict.faithful}", flush=True)
        return 0

    labels = {label.item_id: label for label in parse_sheet((folder / "labels.md").read_text(encoding="utf-8"))}
    verdicts = {row["id"]: row for row in read_jsonl(folder / "judge.jsonl")}
    ids = sorted(labels)
    passed = True
    for field in ("correct", "faithful"):
        human = [getattr(labels[item_id], field) for item_id in ids]
        machine = [verdicts[item_id][field] for item_id in ids]
        result = agreement(human, machine)
        passed = passed and result.rate >= 0.9
        print(f"{field:<9} agree {result.agree}/{result.n} = {result.rate:.1%}  kappa {result.kappa:.2f}")
        for item_id, h, m in zip(ids, human, machine):
            if h != m:
                v = verdicts[item_id]
                why = f"answered={v['answered']} wrong_on_asked={v['wrong_on_asked']}"
                print(f"  {item_id}: Mark {'y' if h else 'n'}, judge {'y' if m else 'n'}: {why}. {v['reason']}")
    print("gate: pass" if passed else "gate: fail (needs >= 90% on both)")
    return 0 if passed else 1


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="assistant")
    commands = parser.add_subparsers(dest="command", required=True)
    knowledge_cmd = commands.add_parser("knowledge", help="regenerate self.md and report the prefix token budget")
    knowledge_cmd.add_argument("--root", type=Path, default=Path("."))
    knowledge_cmd.add_argument("--check", action="store_true", help="exit 1 if the active model's budget is exceeded")
    golden_cmd = commands.add_parser("golden", help="validate the golden set against the knowledge base")
    golden_cmd.add_argument("--root", type=Path, default=Path("."))
    calibrate_cmd = commands.add_parser("calibrate", help="calibrate the judge against Mark's labels")
    calibrate_cmd.add_argument("step", choices=["answers", "sheet", "judge", "score"])
    calibrate_cmd.add_argument("--set", dest="name", choices=["tune", "holdout"], default="tune")
    calibrate_cmd.add_argument("--root", type=Path, default=Path("."))
    calibrate_cmd.add_argument("--server", default="http://127.0.0.1:8080")
    args = parser.parse_args()
    if args.command == "golden":
        sys.exit(golden(args.root))
    if args.command == "calibrate":
        sys.exit(calibrate(args.root, args.step, args.name, args.server))
    sys.exit(knowledge(args.root, args.check))
