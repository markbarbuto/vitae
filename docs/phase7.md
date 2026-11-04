# Phase 7: deploy

Deployed 2026-11-03 to the Oracle A1 VM (2 cores, 12 GB). The assistant is live at `https://assistant.markbarbuto.com` behind Caddy, and the portfolio reaches it through the Vercel proxy in [personal-site#23](https://github.com/markbarbuto/personal-site/pull/23). All quality runs below are the dev split, sent from the desktop over the public internet to the production API, then judged on the desktop.

## Exit gate

| Target | Required | Production, dev split | Pass |
|---|---|---|---|
| Faithfulness | > 90% | 75/76 = 98.7% (CI 93% to 100%) | Yes |
| Correct, answerable | >= 90% | 65/70 = 92.9% (CI 84% to 97%) | Yes |
| Correct refusals | 90 to 95% | 48/49 = 98.0% (CI 89% to 100%) | Yes |
| Benign false refusals | <= 3% | 0/11 | Yes |
| TTFT p95, answers | < 8 s | 7.28 s over 82 answers (p50 5.86 s, max 7.97 s) | Yes |
| Busy, rate-limited or error replies | 0 | 0/130 | Yes |

Grading follows Phase 6. gpt-oss-20b judges everything. Gemma 4 26B gives a second opinion on the 8 answers gpt-oss called unfaithful, and an answer counts as unfaithful only when both agree. Gemma cleared 7 of them. The one left is multi-05, which wrongly says Mark used SQL Server at Celestica.

Correct refusals are above the 95% ceiling of the target band, as in Phase 6. The ceiling is there to catch over-refusal, and benign false refusals are 0/11, so the gate counts it as a pass.

TTFT is measured on the desktop from request sent to first visible token. It covers the network, Caddy, retrieval, the queue and the output guard, so it is the whole path except the Vercel hop. Model declines are slower (refusal p95 8.52 s) because the guard waits until the opening can't become a decline. Gate refusals return in about 90 ms.

Failures (5 correctness, 1 refusal):

- **multi-01, multi-04, multi-05.** Questions that span several jobs or projects. These are the weakest category in every phase (8/11 here, 72.7%). The 4B model either misses one job or lists an unrelated project.
- **site-08.** Adds a claim that Path to Recovery taught deployment, which the knowledge base doesn't say.
- **followup-11.** Lists "Colombia" among the cities.
- **unanswerable-11.** "When will Path to Recovery launch?" gets "coming soon" and a description instead of a decline. The answer is true but doesn't say there is no date.

## What was built

- `deploy/compose.yaml`. Three services, `llama`, `api` and `caddy`, all `restart: unless-stopped`. Only Caddy publishes a port (443).
- `deploy/llama.Dockerfile`. `ubuntu:24.04` plus `libgomp1` and `curl`. It runs the llama.cpp `v0.8.0` build compiled on the VM in Phase 0, mounted read-only. Flags match Phase 6: `--ctx-size 12288 --parallel 1 --threads 2 --flash-attn on`, `q8_0` K and V cache, `--slot-save-path /slots` on a named volume.
- `deploy/api.Dockerfile`. `python:3.12-slim`, locked dependencies installed with `--require-hashes`, `HF_HUB_OFFLINE=1`.
- `deploy/Caddyfile`. Reverse proxy to `api:8000` with `flush_interval -1` so tokens stream without buffering.
- `deploy/deploy.sh`. Exports the lock file, ships code and knowledge with tar over SSH, copies the retrieval models once (about 400 MB), creates `deploy/.env` with two random 32-byte secrets on the first run, then rebuilds.
- `src/vitae/limits.py`. Sliding windows: 4/min and 30/day per visitor IP, 300/day globally. A request that's turned away isn't counted.
- `src/vitae/server.py`. Requires `X-Edge-Secret` (constant-time compare), trusts `X-Client-IP` only from the edge, and lets `X-Eval-Secret` skip the limits. A limited request gets a `rate_limited` event with `retry_after_s`.
- Portfolio, in personal-site#23. `api/chat.ts` validates the request (message 1 to 500 characters, at most 6 history turns of 1,000 characters), adds the edge secret and visitor IP, and streams the reply. It times out after 240 s, inside a 300 s `maxDuration`, so a queued answer isn't cut off. The chat module reads SSE events, shows an offline message with Mark's email when the backend fails, and the footer's "Coming soon" is gone.

Tests: 43 pass (`tests/test_limits.py`, `tests/test_server.py` added).

## Security checks, production

| Check | Result |
|---|---|
| `POST /chat` without the edge secret | 401 |
| Ports 8000 and 8080 from outside | Closed |
| `GET /health` | 200 |
| Certificate | Let's Encrypt, valid to 2027-02-02 |
| Secrets | Only in `deploy/.env` on the VM (mode 600, not shipped by `deploy.sh`) and Vercel's Production env |
| SSH | Port 22 open, keys only, password login off (Mark's choice) |

## Operations

- **Memory.** `llama` 2.99 GB, `api` 0.86 GB, of 11.65 GB.
- **Cold start.** The first start prefills the whole knowledge base (about 7 minutes) and saves the slot.
- **Warm restart.** Restarting `api` took 20 s to ready, with `restored prefix-6ce1e343f4857970.bin` in the log. The slot is saved per prompt hash, so editing the knowledge base or prompt costs one new prefill.
- **Extra downloads on the VM.** The `ubuntu:24.04`, `python:3.12-slim` and `caddy:2-alpine` images, and `libgomp1` and `curl` from Ubuntu's archive.

## Errors fixed during deploy

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` in `deploy.sh` | `uv` isn't on Git Bash's PATH | `python -m uv` |
| `invalid argument: --model=/models/Qwen-Qwen3.5-4B-Q4-0.gguf` | llama.cpp turns `_` into `-` across a whole `--flag=value` token | Pass each flag and value as separate arguments |
| `api` restart loop, `Read-only file system: ...model_optimized.onnx.lock` | `huggingface_hub` takes file locks even offline | Mount `models` read-write |
| Proxy would cut off queued answers | 120 s timeout below the worst case (3 in queue, about 60 s each) | 240 s timeout, 300 s `maxDuration` |

## Not done yet

- **TTFT through Vercel.** The edge secret is set for Vercel Production only, so this needs personal-site#23 merged. Then rerun a sample through `markbarbuto.com/api/chat` and compare it with the 7.28 s above.
- Limits live in memory and reset on restart. That's fine for one API process.
- FastAPI's `on_event` startup hook is deprecated. It still works.
