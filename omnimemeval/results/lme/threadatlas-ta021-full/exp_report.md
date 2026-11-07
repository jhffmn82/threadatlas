# OmniMemEval Experiment Report — threadatlas-ta021-full

> Generated: 2026-11-07 02:30:56

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LongMemEval |
| Memory Framework | threadatlas |
| Version | ta021-full |
| Run Time | 2026-11-07 02:05:53 UTC |
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
| Results Directory | `results/lme/threadatlas-ta021-full` |

**Reproduce:**

```bash
./scripts/run_lme_eval.sh --replay results/lme/threadatlas-ta021-full
```

### Environment Variables (snapshot_eval.env)

| Variable | Value |
|----------|-------|
| `THREADATLAS_REPO` | `/kaggle/working/kit` |
| `THREADATLAS_STATE_DIR` | `/kaggle/working/state` |
| `THREADATLAS_STORE_DIR` | `/kaggle/input/threadatlas-global-chunks` |
| `THREADATLAS_STEP0_DIR` | `/kaggle/input/datasets/jhffmn/it494-threadatlas-step0` |
| `THREADATLAS_SOURCE` | `/kaggle/input/datasets/jhffmn/it494-narrative-corpora-raw/longmemeval/longmemeval_s.json` |
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
| Context Tokens (avg) | 4332.0 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 0.8740 ± 0.0000 |
| F1 | 0.1603 |
| ROUGE-1 | 0.1322 |
| ROUGE-2 | 0.0647 |
| ROUGE-L | 0.1181 |
| BLEU-1 | 0.0760 |
| BLEU-4 | 0.0257 |
| METEOR | 0.2348 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| knowledge-update | 0.8974 | 78 |
| multi-session | 0.7970 | 133 |
| single-session-assistant | 0.9643 | 56 |
| single-session-preference | 0.8667 | 30 |
| single-session-user | 1.0000 | 70 |
| temporal-reasoning | 0.8346 | 133 |

### Pipeline Status

| Stage | Failed Users | Skipped Records | Status Counts |
|-------|--------------|-----------------|---------------|
| search | 0 | 0 | success=500 |
| answer | 0 | 0 | success=500 |
| eval | 0 | 0 | success=500 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 202.0 | 133.5 | 545.7 |
| Search Latency | 639.9 | 533.4 | 1291.4 |
