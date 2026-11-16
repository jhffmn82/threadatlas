# OmniMemEval Experiment Report — threadatlas-base-full

> Generated: 2026-11-16 12:04:51

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | PersonaMem v2 |
| Memory Framework | threadatlas |
| Version | base-full |
| Run Time | 2026-11-16 07:16:12 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 20 |
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
| Results Directory | `results/pmv2/threadatlas-base-full` |

**Reproduce:**

```bash
./scripts/run_pmv2_eval.sh --replay results/pmv2/threadatlas-base-full
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
| Answer API Calls | 5,000 |
| Context Tokens (avg) | 4267.6 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| Precision (Accuracy) | 0.3692 ± 0.0000 |
| Questions | 5000 |
| Total Runs | 5000 |

### Category Breakdown

| Category | Precision | Questions |
|----------|-----------|-----------|
| anti_stereotypical_pref | 0.3029 ± 0.0000 | 855 |
| ask_to_forget | 0.4742 ± 0.0000 | 1048 |
| health_and_medical_conditions | 0.3609 ± 0.0000 | 568 |
| neutral_preferences | 0.3415 ± 0.0000 | 858 |
| sensitive_info | 0.3151 ± 0.0000 | 511 |
| stereotypical_pref | 0.3696 ± 0.0000 | 533 |
| therapy_background | 0.3732 ± 0.0000 | 627 |

### Pipeline Status

| Stage | Failed Units | Skipped Records | Status Counts |
|-------|--------------|-----------------|---------------|
| search | 0 | 0 | success=5000 |
| answer | 0 | 0 | success=5000 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 132118.4 | 132373.7 | 162501.3 |
| Search Latency | 811.4 | 791.9 | 1043.8 |
