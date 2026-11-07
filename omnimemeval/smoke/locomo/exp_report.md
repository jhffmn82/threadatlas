# OmniMemEval Experiment Report — threadatlas-smoke

> Generated: 2026-11-07 10:35:23

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LoCoMo |
| Memory Framework | threadatlas |
| Version | smoke |
| Run Time | 2026-11-07 09:56:29 UTC |
| Git | `7c79d46` (HEAD) (dirty) |
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
| Results Directory | `results/locomo/threadatlas-smoke` |

**Reproduce:**

```bash
./scripts/run_locomo_eval.sh --replay results/locomo/threadatlas-smoke
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
| Answer API Calls | 152 |
| Context Tokens (avg) | 6608.0 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 0.9276 ± 0.0000 |
| F1 | 0.2927 |
| ROUGE-1 | 0.2987 |
| ROUGE-2 | 0.1409 |
| ROUGE-L | 0.2707 |
| BLEU-1 | 0.1813 |
| BLEU-4 | 0.0637 |
| METEOR | 0.4120 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| multi hop | 0.9375 | 32 |
| temporal reasoning | 0.9459 | 37 |
| open domain | 0.7692 | 13 |
| single hop | 0.9429 | 70 |

### Pipeline Status

| Stage | Failed Groups | Skipped Records | Status Counts |
|-------|---------------|-----------------|---------------|
| search | 0 | 0 | success=152 |
| answer | 0 | 0 | success=152 |
| eval | 0 | 0 | success=152 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 58054.0 | 55564.6 | 95678.3 |
| Search Latency | 601.6 | 503.0 | 1834.6 |
