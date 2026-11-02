# Judge and calibration

The eval judge is `gpt-oss-20b` running locally on the desktop GPU (RX 6950 XT, 16 GB) through llama.cpp's Vulkan build. It grades answerable golden items for correctness, using the reference answer as a guide, and for claim-level faithfulness against the whole knowledge base.

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

## How the judge decides correctness

The judge never outputs `correct` directly. It fills in `asks_for`, `answered` (the reference is one good answer, not a checklist) and `wrong_on_asked` (something false in the very thing asked for), and `Verdict.correct` is `answered and not wrong_on_asked`. A wrong side detail counts only against faithfulness.

## Calibration results

Mark labelled the 40 answers blind. Two labels were corrected after review: resume-09 (Celestica gave the People Driven Award, not the Award of Excellence) and multi-05 (Green P.I. did use SQL Server). Each rubric was scored on the same 40 answers:

| Rubric | `correct` | `faithful` |
|---|---|---|
| One correct verdict, reference as main facts | 28/40 (kappa 0.36) | 39/40 (0.92) |
| Same, reworded: reference is not a checklist | 32/40 (0.53) | 38/40 (0.86) |
| Separate fields plus an `off_topic` list | 24/40 (0.28) | 39/40 (0.93) |
| Separate fields, no `off_topic` (current) | 36/40 (0.75) | 38/40 (0.86) |

The current rubric passes the gate at exactly 90%. Known limits:

- **Padding.** The judge cannot tell useful extra detail from padding. With an `off_topic` field it flagged harmless extras on 13 correct answers and still missed the two Mark objected to (benign-07, resume-07). Answer focus and length belong to Phase 4's prompt and output checks.
- **Run-to-run noise.** Verdicts on followup-11, multi-01 and multi-05 changed between runs when only unrelated rubric text changed.
- **Overfitting.** The rubric was chosen on these 40 answers, so 90% overstates it. A fresh blind batch confirms it.

## Why kappa as well as agreement

Raw agreement can look high when most answers are correct: a judge that always says "correct" agrees with a 90%-correct set 90% of the time. Kappa corrects for chance agreement, so a lazy judge scores near 0. The gate stays on raw agreement, as the plan states, and kappa is reported next to it.
