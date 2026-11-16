# OmniMemEval Experiment Report — threadatlas-base-smoke

> Generated: 2026-11-16 06:12:38

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | BEAM |
| Memory Framework | threadatlas |
| Version | base-smoke |
| Run Time | 2026-11-16 06:02:42 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 1 |
| LLM_WORKERS | 10 |
| TOPK | 20 |
| SCALE | 100k |
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
| SKIP_FAILED_JUDGE | 0 |
| SKIP_FAILED_STREAMING | 0 |
| Results Directory | `results/beam/threadatlas-base-smoke` |

**Reproduce:**

```bash
./scripts/run_beam_eval.sh --replay results/beam/threadatlas-base-smoke
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
| Answer API Calls | 20 |
| Context Tokens (avg) | 7341.8 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| Nugget Score | 0.6737 ± 0.3699 |
| Questions | 20 |

### By Conversation Scale

| Scale | Nugget Score | Questions |
|-------|-------------|-----------|
| 100k | 0.6737 ± 0.3699 | 20 |

### By Question Dimension

| Dimension | Nugget Score | Questions |
|-----------|-------------|-----------|
| abstention | 1.0000 ± 0.0000 | 2 |
| contradiction_resolution | 0.4375 ± 0.0625 | 2 |
| event_ordering | 0.0000 ± 0.0000 | 2 |
| information_extraction | 1.0000 ± 0.0000 | 2 |
| instruction_following | 0.7500 ± 0.2500 | 2 |
| knowledge_update | 0.5000 ± 0.5000 | 2 |
| multi_session_reasoning | 0.6250 ± 0.1250 | 2 |
| preference_following | 1.0000 ± 0.0000 | 2 |
| summarization | 0.8000 ± 0.1000 | 2 |
| temporal_reasoning | 0.6250 ± 0.3750 | 2 |

### By Difficulty

| Difficulty | Nugget Score | Questions |
|------------|-------------|-----------|
| clear | 0.4375 ± 0.0625 | 2 |
| easy | 0.6875 ± 0.3698 | 8 |
| hard | 1.0000 ± 0.0000 | 1 |
| medium | 0.6778 ± 0.3966 | 9 |

### Pipeline Status

| Stage | Failed Units | Skipped Records | Status Counts |
|-------|--------------|-----------------|---------------|
| search | 0 | 0 | success=20 |
| answer | 0 | 0 | success=20 |
| eval | 0 | 0 | success=20 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 184783.4 | 186150.9 | 211021.5 |
| Search Latency | 113.8 | 39.6 | 128.3 |
