# OmniMemEval Experiment Report — threadatlas-base-full

> Generated: 2026-11-16 04:58:12

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LoCoMo |
| Memory Framework | threadatlas |
| Version | base-full |
| Run Time | 2026-11-16 04:20:29 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 10 |
| LLM_WORKERS | 10 |
| TOPK | 20 |
| NUM_RUNS | 1 |
| SAVE_MODEL_INPUT | 0 |
| CLEAR | 0 |
| WAIT_AFTER_INGEST | 0 |
| ALLOW_EMPTY_SEARCH | 1 |
| SKIP_FAILED_SEARCH | 0 |
| SKIP_FAILED_ANSWER | 0 |
| SKIP_FAILED_JUDGE | 0 |
| Results Directory | `results/locomo/threadatlas-base-full` |

**Reproduce:**

```bash
./scripts/run_locomo_eval.sh --replay results/locomo/threadatlas-base-full
```

### Environment Variables (snapshot_eval.env)

| Variable | Value |
|----------|-------|
| `THREADATLAS_REPO` | `/kaggle/working/threadatlas` |
| `THREADATLAS_STATE_DIR` | `/kaggle/working/state` |
| `THREADATLAS_READ_MODEL` | `gpt-4.1-mini-2025-04-14` |
| `LLM_WORKERS` | `10` |
| `TOPK` | `20` |
| `ANSWER_MODEL` | `gpt-4.1-mini-2025-04-14` |
| `EVAL_MODEL` | `gpt-4o-mini-2024-07-18` |

## Context Tokens

> Context Tokens are answer-stage prompt/input tokens. They are used as an approximate proxy for retrieved search-result length and should be compared only under the same benchmark, answer model, and prompt template.

| Metric | Value |
|--------|-------|
| Answer Model | gpt-4.1-mini-2025-04-14 |
| Answer API Calls | 1,540 |
| Context Tokens (avg) | 6218.1 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 0.8968 ± 0.0000 |
| F1 | 0.2718 |
| ROUGE-1 | 0.2751 |
| ROUGE-2 | 0.1429 |
| ROUGE-L | 0.2568 |
| BLEU-1 | 0.1673 |
| BLEU-4 | 0.0627 |
| METEOR | 0.4125 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| multi hop | 0.8511 | 282 |
| temporal reasoning | 0.8785 | 321 |
| open domain | 0.7083 | 96 |
| single hop | 0.9405 | 841 |

### Pipeline Status

| Stage | Failed Groups | Skipped Records | Status Counts |
|-------|---------------|-----------------|---------------|
| search | 0 | 0 | success=1540 |
| answer | 0 | 0 | success=1540 |
| eval | 0 | 0 | success=1540 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 30978.1 | 30488.4 | 46745.4 |
| Search Latency | 505.5 | 497.2 | 597.8 |
