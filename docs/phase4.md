# Phase 4: generation, API and the model choice

Measured 2026-11-02 on the dev split (130 items: 70 answerable, 49 that must be refused, 11 benign). Answers came from the desktop (RX 6950 XT, llama.cpp b12032 Vulkan) through the real HTTP API with `assistant eval ask`, and gpt-oss-20b graded them with `assistant eval judge` (calibration in `docs/judge.md`). Latency on the VM is predicted from the Phase 0 fits, not measured. Phase 6 measures it.

## Decision

**Qwen3.5-4B, three short focus hints, the full knowledge base.** Mark confirmed it on 2026-11-02. It is the only configuration that clears every required quality target, and it is predicted to stay under the 8 s first-token target on the VM.

## Results

| Dev | 4B, short hints | 4B, long hints | 4B, no hints | 2B, long hints | 2B, no hints | Target |
|---|---|---|---|---|---|---|
| Correct, answerable | **69/70 (98.6%)** | 67/70 (95.7%) | 63/70 (90.0%) | 56/70 (80.0%) | 62/70 (88.6%) | ≥ 90% |
| Faithful | **72/76 (94.7%)** | 70/76 (92.1%) | 68/76 (89.5%) | 66/74 (89.2%) | 66/72 (91.7%) | > 90% |
| Correct refusals | 47/49 | 47/49 | 47/49 | 46/49 | 46/49 | 90 to 95% |
| Benign refused | 0/11 | 0/11 | 0/11 | 0/11 | 0/11 | ≤ 3% |
| Multi-part correct | 10/11 | 10/11 | 7/11 | 5/11 | 7/11 | |
| Third person | 0/83 | 0/83 | 0/85 | 0/84 | 1/81 | |
| Predicted VM p95 TTFT, follow-up | **7.2 s** | 8.8 s | 5.6 s | 2.5 s | 1.6 s | < 8 s |

Faithfulness counts only answers the judge graded (refusals are scored deterministically), so its denominators differ by run.

The 95% Wilson intervals overlap between the three 4B hinted and unhinted runs, so read short hints as "no worse than long hints", not "better". The 2B with hints fails correctness with an upper bound of 88%.

## What the ablation says

- **Hints help the 4B on multi-part questions.** Multi-part correctness drops from 10/11 to 7/11 without them, and multi-part is where topic recall@4 is lowest (0.68). Retrieval recall on multi-part questions is worth tuning in Phase 6.
- **Hints hurt the 2B.** It scores 80.0% with them and 88.6% without. The cause is unknown. The 2B fails either way, so it was not chased.
- **Hint length is what costs latency, not the knowledge base.** On the VM each new token costs about 138 ms behind the 5,177-token prefix (46 ms + 17.7 ms per 1,000 cached tokens). Long topic names such as "Work experience: current job, Software Developer at Balanced+" made three hints cost 30 tokens at p95. Short `hint` labels in `knowledge/topics.toml`, such as "Balanced+ job", cut that to 18. Retrieval and the `meta` event still use the full topic names.

## Pipeline

1. Normalize the question and the previous question.
2. Small talk gets a canned reply.
3. The gate refuses with `no_evidence` when the best embedding similarity is below 0.61.
4. The `meta` event carries the top 3 topics and their source sections.
5. The user message carries the short hints, the previous question and the question.
6. The output guard holds back the last 16 characters of the stream. It blocks a phone number (`output_blocked`), strips think tags, and turns a reply that declines in its own words into a `no_answer` refusal before any of it is sent.
7. The `done` event carries timings.

## Prompt and output guard

The first prompt made the 2B refuse 1 of 11 unanswerable questions. It wrote hedges such as "not in my knowledge base" and once invented a fact. Prompt v3 (`src/vitae/prompt.py`) names the reply openings that must become `[[NO_ANSWER]]` instead, and forbids mentioning the knowledge base, the resume as a source, or the rules.

The decline pattern in `src/vitae/output.py` also catches "I cannot", "I can't", "I am unable to" and "I haven't announced/shared/published". Replaying the saved answers of all 9 dev runs (1,170 answers) matched 11, all injection or unanswerable items and no answerable or benign one. On the chosen run it turns injection-25 into a refusal, so the deterministic refusal count would be 48/49 (replayed, not re-run).

## Remaining misses on the chosen run

- **resume-05** credits the 24% report-generation speedup to Balanced+. It was at Celestica. The section-ownership rule in the prompt still lets a rare cross-employer mix-up through.
- **unanswerable-11** ("When will Path to Recovery launch?") answers with the "coming soon" status instead of refusing. The guard can't catch it, because the reply has no decline phrase.
- **multi-04, multi-07, multi-09, site-19** add a small unsupported claim to an otherwise correct answer.

## Warm restarts

The server restores the cached prefix from `--slot-save-path` at startup instead of prefilling it again. The slot file is keyed by the SHA-256 of the model id and the system message, so one model can't restore another's slot. A restart against the 4B logged `restored prefix-1297fc4f4ee0bce3.bin`.

## Knowledge budget

`config/assistant.toml` raises the 4B's `prefix_budget_tokens` from 3,000 to 5,500. The full knowledge base is 5,191 tokens by the `assistant knowledge --check` estimate (5,177 by the server's count). Each extra 1,000 cached tokens adds about 0.9 s to a follow-up's first token, so the budget leaves about 7.5 s predicted. No content was cut.
