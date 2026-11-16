# OmniMemEval Experiment Report — threadatlas-base-full

> Generated: 2026-11-16 08:48:34

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | BEAM |
| Memory Framework | threadatlas |
| Version | base-full |
| Run Time | 2026-11-16 07:13:29 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 20 |
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
| Results Directory | `results/beam/threadatlas-base-full` |

**Reproduce:**

```bash
./scripts/run_beam_eval.sh --replay results/beam/threadatlas-base-full
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
| Answer API Calls | 400 |
| Context Tokens (avg) | 5663.8 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| Nugget Score | 0.7312 ± 0.3441 |
| Questions | 400 |

### By Conversation Scale

| Scale | Nugget Score | Questions |
|-------|-------------|-----------|
| 100k | 0.7312 ± 0.3441 | 400 |

### By Question Dimension

| Dimension | Nugget Score | Questions |
|-----------|-------------|-----------|
| abstention | 0.8625 ± 0.2497 | 40 |
| contradiction_resolution | 0.7688 ± 0.2045 | 40 |
| event_ordering | 0.2445 ± 0.2206 | 40 |
| information_extraction | 0.8656 ± 0.2613 | 40 |
| instruction_following | 0.8938 ± 0.2228 | 40 |
| knowledge_update | 0.5875 ± 0.4594 | 40 |
| multi_session_reasoning | 0.6547 ± 0.3502 | 40 |
| preference_following | 0.8875 ± 0.2433 | 40 |
| summarization | 0.7657 ± 0.2073 | 40 |
| temporal_reasoning | 0.7812 ± 0.3499 | 40 |

### By Difficulty

| Difficulty | Nugget Score | Questions |
|------------|-------------|-----------|
| clear | 0.7688 ± 0.2045 | 40 |
| easy | 0.6720 ± 0.3987 | 124 |
| hard | 0.8617 ± 0.2109 | 42 |
| medium | 0.7325 ± 0.3444 | 193 |

### Pipeline Status

| Stage | Failed Units | Skipped Records | Status Counts |
|-------|--------------|-----------------|---------------|
| search | 0 | 0 | success=400 |
| answer | 0 | 0 | success=400 |
| eval | 0 | 0 | success=400 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 1002513.4 | 940297.0 | 1421644.1 |
| Search Latency | 1103.3 | 1065.4 | 1676.2 |
