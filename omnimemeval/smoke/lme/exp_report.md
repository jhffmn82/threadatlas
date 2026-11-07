# OmniMemEval Experiment Report — threadatlas-smoke

> Generated: 2026-11-07 09:56:29

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LongMemEval |
| Memory Framework | threadatlas |
| Version | smoke |
| Run Time | 2026-11-07 09:52:24 UTC |
| Git | `7c79d46` (HEAD) (dirty) |
| WORKERS | 4 |
| LLM_WORKERS | 10 |
| TOPK | 20 |
| NUM_RUNS | 1 |
| SAVE_MODEL_INPUT | 0 |
| STREAMING | 0 |
| START_IDX | 0 |
| END_IDX |  |
| ALLOW_EMPTY_SEARCH | 1 |
| SKIP_FAILED_SEARCH | 0 |
| SKIP_FAILED_ANSWER | 0 |
| SKIP_FAILED_JUDGE | 0 |
| SKIP_FAILED_STREAMING | 0 |
| Results Directory | `results/lme/threadatlas-smoke` |

**Reproduce:**

```bash
./scripts/run_lme_eval.sh --replay results/lme/threadatlas-smoke
```

### Environment Variables (snapshot_eval.env)

| Variable | Value |
|----------|-------|
| `THREADATLAS_REPO` | `/kaggle/working/kit` |
| `THREADATLAS_STATE_DIR` | `/kaggle/working/state` |
| `THREADATLAS_STORE_DIR` | `/kaggle/input/threadatlas-global-chunks` |
| `THREADATLAS_STEP0_DIR` | `/kaggle/input/datasets/jhffmn/it494-threadatlas-step0` |
| `THREADATLAS_SOURCE` | `/kaggle/input/datasets/jhffmn/it494-narrative-corpora-raw/longmemeval/longmemeval_s.json` |
| `THREADATLAS_READ_MODEL` | `gpt-5.6-luna` |
| `LLM_WORKERS` | `10` |
| `TOPK` | `20` |
| `ANSWER_MODEL` | `gpt-4.1-mini-2025-04-14` |
| `EVAL_MODEL` | `gpt-4o-mini-2024-07-18` |

## Context Tokens

> Context Tokens are answer-stage prompt/input tokens. They are used as an approximate proxy for retrieved search-result length and should be compared only under the same benchmark, answer model, and prompt template.

| Metric | Value |
|--------|-------|
| Answer Model | gpt-4.1-mini-2025-04-14 |
| Answer API Calls | 20 |
| Context Tokens (avg) | 4568.0 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 1.0000 ± 0.0000 |
| F1 | 0.2894 |
| ROUGE-1 | 0.2868 |
| ROUGE-2 | 0.1694 |
| ROUGE-L | 0.2868 |
| BLEU-1 | 0.1701 |
| BLEU-4 | 0.0665 |
| METEOR | 0.5231 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| single-session-user | 1.0000 | 20 |

### Pipeline Status

| Stage | Failed Users | Skipped Records | Status Counts |
|-------|--------------|-----------------|---------------|
| search | 0 | 0 | success=20 |
| answer | 0 | 0 | success=20 |
| eval | 0 | 0 | success=20 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 696.7 | 421.4 | 864.9 |
| Search Latency | 1549.4 | 494.2 | 5894.6 |
