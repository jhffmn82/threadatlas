# OmniMemEval Experiment Report — threadatlas-base-full

> Generated: 2026-11-16 11:18:20

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LongMemEval |
| Memory Framework | threadatlas |
| Version | base-full |
| Run Time | 2026-11-16 07:18:22 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 60 |
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
| Results Directory | `results/lme/threadatlas-base-full` |

**Reproduce:**

```bash
./scripts/run_lme_eval.sh --replay results/lme/threadatlas-base-full
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
| Answer API Calls | 500 |
| Context Tokens (avg) | 4350.8 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 0.8700 ± 0.0000 |
| F1 | 0.1626 |
| ROUGE-1 | 0.1340 |
| ROUGE-2 | 0.0668 |
| ROUGE-L | 0.1205 |
| BLEU-1 | 0.0773 |
| BLEU-4 | 0.0260 |
| METEOR | 0.2363 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| knowledge-update | 0.8718 | 78 |
| multi-session | 0.7744 | 133 |
| single-session-assistant | 0.9643 | 56 |
| single-session-preference | 0.9333 | 30 |
| single-session-user | 1.0000 | 70 |
| temporal-reasoning | 0.8421 | 133 |

### Pipeline Status

| Stage | Failed Users | Skipped Records | Status Counts |
|-------|--------------|-----------------|---------------|
| search | 0 | 0 | success=500 |
| answer | 0 | 0 | success=500 |
| eval | 0 | 0 | success=500 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 32947.9 | 28560.5 | 72624.1 |
| Search Latency | 4272.5 | 4375.8 | 4968.4 |
