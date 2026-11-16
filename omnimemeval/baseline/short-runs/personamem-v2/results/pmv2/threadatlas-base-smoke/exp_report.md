# OmniMemEval Experiment Report — threadatlas-base-smoke

> Generated: 2026-11-16 06:11:15

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | PersonaMem v2 |
| Memory Framework | threadatlas |
| Version | base-smoke |
| Run Time | 2026-11-16 06:05:56 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 2 |
| LLM_WORKERS | 10 |
| TOPK | 20 |
| NUM_RUNS | 1 |
| SAVE_MODEL_INPUT | 0 |
| CLEAR | 0 |
| WAIT_AFTER_INGEST | 0 |
| STREAMING | 0 |
| START_IDX | 0 |
| END_IDX |  |
| ALLOW_EMPTY_SEARCH | 1 |
| SKIP_FAILED_SEARCH | 0 |
| SKIP_FAILED_ANSWER | 0 |
| SKIP_FAILED_STREAMING | 0 |
| ALLOW_MISSING_DATA | 0 |
| Results Directory | `results/pmv2/threadatlas-base-smoke` |

**Reproduce:**

```bash
./scripts/run_pmv2_eval.sh --replay results/pmv2/threadatlas-base-smoke
```

### Environment Variables (snapshot_eval.env)

| Variable | Value |
|----------|-------|
| `THREADATLAS_REPO` | `/kaggle/working/threadatlas` |
| `THREADATLAS_STATE_DIR` | `/kaggle/working/state` |
| `THREADATLAS_READ_MODEL` | `gpt-4.1-mini-2025-04-14` |
| `THREADATLAS_EMBED_DEVICE` | `cpu` |
| `LLM_WORKERS` | `10` |
| `TOPK` | `20` |
| `ANSWER_MODEL` | `gpt-4.1-mini-2025-04-14` |
| `EVAL_MODEL` | `gpt-4o-mini-2024-07-18` |

## Context Tokens

> Context Tokens are answer-stage prompt/input tokens. They are used as an approximate proxy for retrieved search-result length and should be compared only under the same benchmark, answer model, and prompt template.

| Metric | Value |
|--------|-------|
| Answer Model | gpt-4.1-mini-2025-04-14 |
| Answer API Calls | 56 |
| Context Tokens (avg) | 4418.8 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| Precision (Accuracy) | 0.4286 ± 0.0000 |
| Questions | 56 |
| Total Runs | 56 |

### Category Breakdown

| Category | Precision | Questions |
|----------|-----------|-----------|
| anti_stereotypical_pref | 0.3846 ± 0.0000 | 13 |
| ask_to_forget | 0.3636 ± 0.0000 | 11 |
| health_and_medical_conditions | 0.6667 ± 0.0000 | 6 |
| neutral_preferences | 0.2857 ± 0.0000 | 7 |
| sensitive_info | 0.5000 ± 0.0000 | 4 |
| stereotypical_pref | 0.2000 ± 0.0000 | 5 |
| therapy_background | 0.6000 ± 0.0000 | 10 |

### Pipeline Status

| Stage | Failed Units | Skipped Records | Status Counts |
|-------|--------------|-----------------|---------------|
| search | 0 | 0 | success=56 |
| answer | 0 | 0 | success=56 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 24046.2 | 25453.2 | 42480.1 |
| Search Latency | 67.8 | 39.5 | 93.8 |
