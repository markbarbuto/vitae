# Judge and calibration

The eval judge is `gpt-oss-20b` running locally on the desktop GPU (RX 6950 XT, 16 GB) through llama.cpp's Vulkan build. It grades answerable golden items for correctness against the reference answer and for claim-level faithfulness against the whole knowledge base.

## Files

| Path | What it is |
|---|---|
| `models/gpt-oss-20b-MXFP4.gguf` | Judge weights, 12.1 GB, from `ggml-org/gpt-oss-20b-GGUF` at revision `15dcfc7e`, sha256 `27cd6c43…5901`. Gitignored. |
| `models/llama-b12032-vulkan/` | llama.cpp build `b12032`, Windows Vulkan x64, sha256 `19a8bbf2…cc32`. Gitignored. |
| `src/vitae/judge.py` | Rubric, JSON schema and verdict parsing. |
| `eval/calibration/answers.jsonl` | 40 dev answers to calibrate on. 31 come from Qwen3.5-4B (Q4_0, draft prompt, no focus hints). 9 are deliberately flawed (`source: perturbed`), so the set contains enough failures to test the judge. |
| `eval/calibration/labels.md` | Mark's hand labels. Filled in without seeing the judge's output. |
| `eval/calibration/judge.jsonl` | The judge's verdicts on the same 40 answers. |

## Run it

Start the judge (Git Bash, from the repo root):

```bash
models/llama-b12032-vulkan/llama-server.exe -m models/gpt-oss-20b-MXFP4.gguf --device Vulkan0 -ngl 99 -ncmoe 99 -t 6 -fa on -c 16384 --parallel 1 --jinja --port 8080
```

Then:

```bash
uv run assistant calibrate judge
uv run assistant calibrate score
```

`score` prints agreement and Cohen's kappa for `correct` and `faithful`, lists every disagreement with the judge's reason, and exits 1 unless both agreements are at least 90%.

To redo calibration from scratch, start Qwen3.5-4B the same way on port 8081, then run `uv run assistant calibrate answers --server http://127.0.0.1:8081`, re-apply the perturbed answers, delete `labels.md`, and run `uv run assistant calibrate sheet`.

## Speed

`-ncmoe 99` keeps the mixture-of-experts weights on the CPU and everything else on the GPU. On the RX 6950 XT with AMD's Windows Vulkan driver, the MXFP4 expert kernels are slow: `llama-bench` measured 12.9 tok/s decode with all layers on the GPU, 12.4 tok/s on the CPU alone, and 18.2 tok/s split this way. Qwen3.5-4B runs at 140 tok/s on the same GPU, so the GPU itself is fine. `--parallel 1` keeps one slot, so the 5,100-token knowledge prefix stays cached: after the first call each verdict reprocesses about 150 tokens and spends 35 to 50 s on reasoning. The 40 calibration verdicts take about 30 minutes.

`judge.jsonl` is written after every verdict, and `calibrate judge` skips items it already has, so an interrupted run resumes. The schema caps claim, evidence and reason lengths; a verdict that still comes back empty is retried once at temperature 0.3.

## Why kappa as well as agreement

Raw agreement can look high when most answers are correct: a judge that always says "correct" agrees with a 90%-correct set 90% of the time. Kappa corrects for chance agreement, so a lazy judge scores near 0. The gate stays on raw agreement, as the plan states, and kappa is reported next to it.
