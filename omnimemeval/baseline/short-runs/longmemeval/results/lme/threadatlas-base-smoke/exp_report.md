# OmniMemEval Experiment Report — threadatlas-base-smoke

> Generated: 2026-11-16 06:34:39

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LongMemEval |
| Memory Framework | threadatlas |
| Version | base-smoke |
| Run Time | 2026-11-16 06:06:52 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 20 |
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
| Results Directory | `results/lme/threadatlas-base-smoke` |

**Reproduce:**

```bash
./scripts/run_lme_eval.sh --replay results/lme/threadatlas-base-smoke
```

### Environment Variables (snapshot_eval.env)

| Variable | Value |
|----------|-------|
| `THREADATLAS_REPO` | `/kaggle/working/threadatlas` |
| `THREADATLAS_STATE_DIR` | `/kaggle/working/state` |
| `THREADATLAS_READ_MODEL` | `gpt-4.1-mini-2025-04-14` |
| `THREADATLAS_EMBED_DEVICE` | `cuda` |
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
| Context Tokens (avg) | 4237.6 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 1.0000 ± 0.0000 |
| F1 | 0.2893 |
| ROUGE-1 | 0.2904 |
| ROUGE-2 | 0.1767 |
| ROUGE-L | 0.2904 |
| BLEU-1 | 0.1739 |
| BLEU-4 | 0.0728 |
| METEOR | 0.5083 |
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
| Add Latency | 28101.4 | 23154.1 | 62629.3 |
| Search Latency | 2189.1 | 2196.4 | 2727.1 |
