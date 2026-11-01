# Phase 0: latency on Oracle A1 (2 OCPU / 12 GB)

Measured 2026-11-01. Every number here comes from a run in `bench/results/` or a `llama-bench` table below.

## Setup

| | |
|---|---|
| VM | Oracle A1, 2 OCPU (2 Neoverse-N1 cores, `asimddp`), 11 GiB usable, Ubuntu 24.04.5 aarch64 |
| Runtime | llama.cpp `v0.8.0` (commit `8642541`), built on the VM with `GGML_NATIVE=ON` |
| Models | bartowski `Qwen_Qwen3.5-4B-Q4_0.gguf` (SHA-256 `3e977de3…a49b`), `Qwen_Qwen3.5-2B-Q4_0.gguf` (`91c102fc…36f6`) |
| Server | `llama-server -t 2 -c 8192 --parallel 1`, thinking off via `chat_template_kwargs` |
| Desktop reference | i5-12600K, Docker `--cpus 2`, `llama-server -t 2`, image `ghcr.io/ggml-org/llama.cpp:server` (commit `1052f7e1d`, not identical to the VM build) |

## Raw throughput (`llama-bench`, 2 threads)

| Model | Test | tok/s |
|---|---|---|
| 4B | pp32 / pp96 | 21.75 / 21.91 |
| 4B | pp300 / pp600 / pp900 / pp1200 | 22.13 / 21.66 / 21.45 / 21.30 |
| 4B | tg128 | 5.83 |
| 4B | pp32 @ depth 2,500 / 5,300 (`-fa 1`) | 12.33 / 7.13 |
| 4B | pp32 @ depth 5,300, `q8_0` K and V | 7.62 |
| 2B | pp32 / pp900 | 54.79 / 54.86 |
| 2B | tg128 | 11.26 |
| 2B | pp32 @ depth 3,000 / 5,300 (`-fa 1`) | 34.13 / 25.11 |

### What limits it

- **Prefill is compute-bound.** 4B at 21.5 tok/s is about 185 GOPS of int8 work. That is roughly half of what I estimate two N1 cores can peak at (inferred, not measured). More threads are not available, and doubling to 4 OCPU would roughly halve times, not fix them.
- **Prefill slows linearly with cached context.**
  - 4B: about **46 ms per new token + 17.7 ms per 1,000 cached tokens**.
  - 2B: about **18 ms + 4.1 ms per 1,000**.
  - This fits the probe below within ~10%.
  - Flash attention made no difference. A `q8_0` KV cache helped ~7%.

## End-to-end TTFT (`bench/latency.py`, `bench/cag_probe.py`)

### A. Classic RAG prompt (~897 tokens: system + 5 sections + question), 4B

`bench/results/vm-4b-rag.json`, 8 runs with the context order and question varied per run:

| TTFT p50 | TTFT p95 | Prompt tokens cached | Prompt tokens processed | Decode |
|---|---|---|---|---|
| **32.0 s** | **33.4 s** | 220 (system prompt), sometimes 380 | 514 to 679 | 5.5 tok/s |

Prefix reuse works for Qwen3.5 on this build. It does not matter, because the per-request context is what costs. **Fails the 8 s target by ~4×.**

Desktop with 2 CPUs on the same harness (`bench/results/desktop-2cpu.json`, 30 runs): TTFT p50 23.2 s, prefill 30.9 tok/s, decode 5.7 tok/s.

**Desktop-to-VM ratio: prefill ×1.46, decode ×1.05.** Use it to translate local tuning numbers.

### B. Whole knowledge base as a cached prefix, 4B

`bench/results/vm-4b-cag.json`. The prefix is system prompt + raw site text + resume (no phone), **5,368 tokens**. Requests add only `Relevant sections: …` and the question. Every third request carries one previous turn.

| | Value |
|---|---|
| Cold start (whole prefix, once per server start) | 296 s |
| Prefix tokens reused per warm request | 5,333 (all 10 runs) |
| First-turn questions (35 to 40 tokens processed) | TTFT **5.2 to 6.0 s** |
| Follow-ups with one previous turn (87 to 93 tokens) | TTFT **12.8 to 13.9 s** |
| Decode at that depth | 4.1 tok/s |

With `-fa on` (`vm-4b-cag-fa.json`) the results were the same within noise.

## Predicted TTFT by design (from the per-token fits above)

The fits match measured runs within ~10%. Rows marked *predicted* have not been run end to end.

| Design | First turn | Follow-up | Status |
|---|---|---|---|
| 4B, classic RAG, ~675 tokens processed | 32 s | 32 s+ | measured, fails |
| 4B, cached prefix 5,300 tok, 40 / 90-token turns | 5.5 s | 13.5 s | measured, follow-ups fail |
| 4B, cached prefix **≤ 3,000** tok, 40 / 60-token turns (previous question only, no previous answer) | ~4.0 s | ~5.9 s | *predicted* |
| 2B, classic RAG, ~400 tokens processed | ~7.5 s | ~8 s | *predicted*, borderline |
| 2B, cached prefix 5,300 tok, 40 / 90-token turns | ~1.6 s | ~3.6 s | *predicted* |
| 2B, cached prefix 10,000 tok, 40 / 90-token turns | ~2.4 s | ~5.3 s | *predicted* |

## Observations

- Thinking stayed off: 0 of 48 answers contained a `think>` tag.
- One probe answer attributed Balanced+'s "500+ tests" to Celestica. The probe used random hints and raw text dumps, so this is not a quality measurement. It is a real risk of putting the whole knowledge base in context, and the Phase 2 evals must cover cross-entity mix-ups.
- Restarting `llama-server` costs the full cold prefill (296 s for 4B). Saving and restoring the slot state to disk (`--slot-save-path`) should avoid that. Not yet tested.

## Reproduce

```bash
# on the VM, after building llama.cpp v0.8.0 and downloading the models
./llama.cpp/build/bin/llama-bench -m models/Qwen_Qwen3.5-4B-Q4_0.gguf -t 2 -p 300,600,900,1200 -n 128 -r 3
./llama.cpp/build/bin/llama-server -m models/Qwen_Qwen3.5-4B-Q4_0.gguf -t 2 -c 8192 --parallel 1 --port 8080 &
python3 latency.py --runs 8 --max-tokens 40 --out vm-4b-rag.json
python bench/build_prefix.py ../portfolio/src/data knowledge/sources/ResumeMarkBarbuto.pdf kb_prefix.txt   # on the desktop
python3 cag_probe.py --prefix kb_prefix.txt --runs 10 --out vm-4b-cag.json
```
