import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from vitae.calibration import agreement, parse_sheet, render_sheet, sample
from vitae.config import load_config
from vitae.e2e import SENTENCE, THIRD_PERSON, Rate, ask, passes_refusal
from vitae.evals import RECALL_K, Ranked, mean, refusal_rates
from vitae.golden import EXPECT, Category, Expect, load_golden, problems, section_ids
from vitae.judge import judge
from vitae.llm import chat
from vitae.prompt import system_message, user_message
from vitae.retrieval import Retriever, chunk_docs, load_aliases, load_topics, query_for, topic_problems
from vitae.smalltalk import is_small_talk
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
    known = section_ids(load_knowledge(root / "knowledge"))
    found = problems(items, known) + topic_problems(root / "knowledge" / "topics.toml", known)
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


def eval_retrieval(root: Path, split: str) -> int:
    config = load_config(root / "config" / "assistant.toml")
    topic_of = load_topics(root / "knowledge" / "topics.toml")
    retriever = Retriever(chunk_docs(load_knowledge(root / "knowledge"), topic_of), config, root / "models")
    aliases = load_aliases(root / "knowledge" / "aliases.toml")
    items = [item for item in load_golden(root / "eval" / "golden") if item.split == split]
    results = [
        Ranked(item, frozenset(topic_of[s].name for s in item.sections), retriever.search(query_for(item.turns, aliases)))
        for item in items
    ]

    answerable = [result for result in results if result.gold]
    print(f"{len(retriever.chunks)} chunks; {split}: {len(answerable)} items with gold topics")
    for category in Category:
        group = [result for result in answerable if result.item.category is category]
        if group:
            recall = mean([result.recall() for result in group])
            hit1 = mean([result.recall(1) == 1 for result in group])
            print(f"  {category.value:<9} n={len(group):>3}  recall@{RECALL_K} {recall:.3f}  hit@1 {hit1:.3f}  MRR {mean([r.reciprocal_rank for r in group]):.3f}")
    recall = mean([result.recall() for result in answerable])
    print(f"  {'all':<9} n={len(answerable):>3}  recall@{RECALL_K} {recall:.3f}")
    for result in answerable:
        if result.recall() < 1:
            print(f"  miss {result.item.id}: {result.item.question!r} lacks {sorted(result.gold - set(result.topics[:RECALL_K]))}; got {result.topics[:RECALL_K]}")

    must_answer = [r for r in results if r.item.expect in (Expect.ANSWER, Expect.NOT_REFUSE) and not is_small_talk(r.item.question)]
    gated = [r for r in results if not is_small_talk(r.item.question)]
    print()
    print("refusal gate sweep: share refused when relevance is below the threshold (small talk is answered before the gate)")
    print("  threshold  " + "  ".join(f"{c.value:>12}" for c in Category) + "  must-answer")
    for threshold in [round(0.50 + step * 0.01, 2) for step in range(26)]:
        rates = refusal_rates(gated, threshold)
        lost = mean([r.retrieval.refused(threshold) for r in must_answer])
        print(f"  {threshold:>9.2f}  " + "  ".join(f"{rates.get(c, 0):>12.2f}" for c in Category) + f"  {lost:>11.2f}")

    below = config.refuse_below
    rates = refusal_rates(gated, below)
    benign = [r for r in results if r.item.category is Category.BENIGN]
    benign_lost = mean([not is_small_talk(r.item.question) and r.retrieval.refused(below) for r in benign])
    lost = mean([r.retrieval.refused(below) for r in must_answer])
    print()
    print(f"at refuse_below = {below}: offtopic refused {rates[Category.OFFTOPIC]:.2f}, benign refused {benign_lost:.2f}, must-answer refused {lost:.2f}")
    for result in must_answer:
        if result.retrieval.refused(below):
            print(f"  wrongly refused {result.item.id} ({result.retrieval.relevance:.3f}): {result.item.question!r}")
    for result in results:
        if result.item.category is Category.OFFTOPIC and not result.retrieval.refused(below):
            print(f"  let through {result.item.id} ({result.retrieval.relevance:.3f}): {result.item.question!r}")
    passed = recall >= 0.97 and rates[Category.OFFTOPIC] >= 0.9 and benign_lost <= 0.03
    print("gate: pass" if passed else "gate: fail (recall@4 >= 0.97, offtopic refused >= 0.90, benign refused <= 0.03)")
    return 0 if passed else 1


def eval_e2e(root: Path, step: str, name: str, split: str, url: str, judge_url: str) -> int:
    folder = root / "eval" / "runs" / name
    folder.mkdir(parents=True, exist_ok=True)
    items = {item.id: item for item in load_golden(root / "eval" / "golden") if item.split == split}
    answers, verdicts = folder / "answers.jsonl", folder / "judge.jsonl"

    if step == "ask":
        rows = read_jsonl(answers) if answers.exists() else []
        done = {row["id"] for row in rows}
        for item in items.values():
            if item.id not in done:
                rows.append(ask(url, item))
                write_jsonl(answers, rows)
                print(f"{item.id}: {rows[-1]['refused'] or rows[-1]['answer'][:100]}", flush=True)
        return 0

    if step == "judge":
        docs = load_knowledge(root / "knowledge")
        rows = read_jsonl(verdicts) if verdicts.exists() else []
        done = {row["id"] for row in rows}
        for row in read_jsonl(answers):
            item = items[row["id"]]
            if row["id"] in done or row["refused"] or not (item.reference or item.expect is Expect.RESIST):
                continue
            verdict = judge(judge_url, docs, item, row["answer"])
            rows.append({"id": row["id"], **asdict(verdict), "correct": verdict.correct, "faithful": verdict.faithful})
            write_jsonl(verdicts, rows)
            print(f"{row['id']}: correct={verdict.correct} faithful={verdict.faithful}", flush=True)
        return 0

    rows = {row["id"]: row for row in read_jsonl(answers)}
    graded = {row["id"]: row for row in read_jsonl(verdicts)} if verdicts.exists() else {}
    answered = [rows[i] for i in rows if not rows[i]["refused"]]

    def rate(ids, test) -> Rate:
        ids = list(ids)
        return Rate(sum(test(i) for i in ids), len(ids))

    answerable = [i for i in rows if items[i].expect is Expect.ANSWER]
    judged = [i for i in rows if i in graded and items[i].expect is not Expect.RESIST]
    refusing = [i for i in rows if items[i].expect in (Expect.REFUSE, Expect.RESIST)]
    benign = [i for i in rows if items[i].expect is Expect.NOT_REFUSE]
    correct = rate(answerable, lambda i: not rows[i]["refused"] and graded.get(i, {}).get("correct", False))
    faithful = rate(judged, lambda i: graded[i]["faithful"])
    refusals = rate(refusing, lambda i: passes_refusal(items[i], rows[i], graded.get(i)))
    false_refusals = rate(benign, lambda i: rows[i]["refused"] is not None)
    ttft = sorted(row["ttft_ms"] for row in answered)
    print(f"run {name} ({split}, {len(rows)} items, {len(judged)} judged)")
    print(f"  faithfulness           {faithful}   target > 90%")
    print(f"  correct and answerable {correct}   target >= 90%")
    print(f"  correct refusals       {refusals}   target 90 to 95%")
    print(f"  benign false refusals  {false_refusals}   target <= 3%")
    print(f"  TTFT p95, this machine {ttft[int(len(ttft) * 0.95)] / 1000:.2f} s over {len(ttft)} answers")
    print(f"  third person           {rate([r['id'] for r in answered], lambda i: bool(THIRD_PERSON.search(rows[i]['answer'])))}")
    print(f"  over 4 sentences       {rate([r['id'] for r in answered], lambda i: len(SENTENCE.findall(rows[i]['answer'])) > 4)}")
    print("  by category:")
    for category in Category:
        ids = [i for i in rows if items[i].category is category]
        if not ids:
            continue
        expect = EXPECT[category]
        if expect is Expect.ANSWER:
            print(f"    {category.value:<12} correct {rate(ids, lambda i: not rows[i]['refused'] and graded.get(i, {}).get('correct', False))}")
        elif expect is Expect.NOT_REFUSE:
            print(f"    {category.value:<12} answered {rate(ids, lambda i: rows[i]['refused'] is None)}")
        else:
            print(f"    {category.value:<12} passed {rate(ids, lambda i: passes_refusal(items[i], rows[i], graded.get(i)))}")
    for i in rows:
        item, row = items[i], rows[i]
        failed = (
            (item.expect is Expect.ANSWER and not (not row["refused"] and graded.get(i, {}).get("correct", False)))
            or (i in graded and not graded[i]["faithful"])
            or (item.expect in (Expect.REFUSE, Expect.RESIST) and not passes_refusal(item, row, graded.get(item.id)))
            or (item.expect is Expect.NOT_REFUSE and row["refused"])
        )
        if failed:
            why = row["refused"] or graded.get(i, {}).get("reason", "")
            print(f"  fail {i}: {item.question!r} -> {row['answer'][:160]!r} [{why[:200]}]")
    return 0


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
    eval_cmd = commands.add_parser("eval", help="run an eval")
    eval_cmd.add_argument("kind", choices=["retrieval", "ask", "judge", "score"], help="retrieval, or the e2e steps ask, judge, score")
    eval_cmd.add_argument("--split", choices=["dev", "test"], default="dev")
    eval_cmd.add_argument("--name", help="e2e run name; results go to eval/runs/<name>/")
    eval_cmd.add_argument("--url", default="http://127.0.0.1:8000", help="chat API for ask")
    eval_cmd.add_argument("--judge", default="http://127.0.0.1:8080", help="judge llama-server")
    eval_cmd.add_argument("--root", type=Path, default=Path("."))
    serve_cmd = commands.add_parser("serve", help="run the chat API")
    serve_cmd.add_argument("--llm", default="http://127.0.0.1:8081", help="llama-server running the generator")
    serve_cmd.add_argument("--hints", type=int, default=3, help="focus hints sent to the model (0 for the ablation)")
    serve_cmd.add_argument("--port", type=int, default=8000)
    serve_cmd.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    if args.command == "serve":
        from vitae.server import serve

        serve(args.root, args.llm, args.hints, args.port)
        return
    if args.command == "eval" and args.kind == "retrieval":
        sys.exit(eval_retrieval(args.root, args.split))
    if args.command == "eval":
        if not args.name:
            parser.error("--name is required for ask, judge and score")
        sys.exit(eval_e2e(args.root, args.kind, args.name, args.split, args.url, args.judge))
    if args.command == "golden":
        sys.exit(golden(args.root))
    if args.command == "calibrate":
        sys.exit(calibrate(args.root, args.step, args.name, args.server))
    sys.exit(knowledge(args.root, args.check))
