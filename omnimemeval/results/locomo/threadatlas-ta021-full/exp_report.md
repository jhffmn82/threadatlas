# OmniMemEval Experiment Report — threadatlas-ta021-full

> Generated: 2026-11-07 01:30:51

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LoCoMo |
| Memory Framework | threadatlas |
| Version | ta021-full |
| Run Time | 2026-11-07 00:03:40 UTC |
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
| Results Directory | `results/locomo/threadatlas-ta021-full` |

**Reproduce:**

```bash
./scripts/run_locomo_eval.sh --replay results/locomo/threadatlas-ta021-full
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
| Answer API Calls | 1,540 |
| Context Tokens (avg) | 6189.8 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 0.8922 ± 0.0000 |
| F1 | 0.2716 |
| ROUGE-1 | 0.2754 |
| ROUGE-2 | 0.1421 |
| ROUGE-L | 0.2571 |
| BLEU-1 | 0.1666 |
| BLEU-4 | 0.0632 |
| METEOR | 0.4100 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| multi hop | 0.8369 | 282 |
| temporal reasoning | 0.8629 | 321 |
| open domain | 0.7188 | 96 |
| single hop | 0.9417 | 841 |

### Pipeline Status

| Stage | Failed Groups | Skipped Records | Status Counts |
|-------|---------------|-----------------|---------------|
| search | 0 | 0 | success=1540 |
| answer | 0 | 0 | success=1540 |
| eval | 0 | 0 | success=1540 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 76243.7 | 69939.6 | 129012.0 |
| Search Latency | 460.4 | 425.1 | 748.8 |
