"""Phase 0 probe: whole knowledge base as a cached prefix.

The system message holds the system prompt plus every knowledge section, and
never changes. Each request adds only retrieval hints and the question, so a
warm server should process tens of tokens instead of hundreds. The first
request pays for the full prefix; its timing is reported separately.

Usage: python3 cag_probe.py --prefix kb_prefix.txt --runs 10 --out results.json
"""

import argparse
import json
import random
import statistics
import time

from latency import QUESTIONS, run_once, pct

HINTS = [
    "Experience > Balanced+", "Experience > Celestica", "Experience > Green P.I.",
    "Projects > Indigenous Supports from KHP", "Projects > Path to Recovery",
    "Projects > Vitae AI", "Skills", "Interests > Travel", "Interests > Arsenal",
]


def messages(prefix: str, rng: random.Random, follow_up: bool) -> list[dict]:
    hints = ", ".join(rng.sample(HINTS, 2))
    turn = [{"role": "user", "content": f"Relevant sections: {hints}\n\nQuestion: {rng.choice(QUESTIONS)}"}]
    if follow_up:
        turn = [
            {"role": "user", "content": "Relevant sections: Experience > Celestica\n\nQuestion: Tell me about Celestica."},
            {"role": "assistant", "content": "At Celestica I built and maintained a global .NET manufacturing SaaS product and won the People Driven Award for a defect tracking tool."},
        ] + turn
    return [{"role": "system", "content": prefix}] + turn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    prefix = open(args.prefix, encoding="utf-8").read()
    rng = random.Random(11)
    t0 = time.perf_counter()
    cold = run_once(args.url, messages(prefix, rng, False), 8)
    cold["wall_s"] = time.perf_counter() - t0

    warm = [run_once(args.url, messages(prefix, rng, i % 3 == 2), 40) for i in range(args.runs)]
    ttfts = [r["ttft_s"] for r in warm]
    summary = {
        "cold_prompt_tokens": (cold["prompt_tokens_processed"] or 0) + (cold["prompt_tokens_cached"] or 0),
        "cold_wall_s": cold["wall_s"],
        "warm_runs": len(warm),
        "warm_ttft_p50_s": statistics.median(ttfts),
        "warm_ttft_p95_s": pct(ttfts, 0.95),
        "warm_processed_tokens": [r["prompt_tokens_processed"] for r in warm],
        "warm_cached_tokens": [r["prompt_tokens_cached"] for r in warm],
        "warm_ttft_s": [round(t, 2) for t in ttfts],
        "decode_tps_p50": statistics.median(r["decode_tps"] or 0 for r in warm),
        "sample_answers": [r["answer"] for r in warm[:3]],
    }
    json.dump({"summary": summary, "cold": cold, "warm": warm}, open(args.out, "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
