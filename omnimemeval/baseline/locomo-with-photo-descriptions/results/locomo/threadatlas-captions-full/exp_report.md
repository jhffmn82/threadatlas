# OmniMemEval Experiment Report — threadatlas-captions-full

> Generated: 2026-11-16 19:01:54

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LoCoMo |
| Memory Framework | threadatlas |
| Version | captions-full |
| Run Time | 2026-11-16 18:12:58 UTC |
| Git | `05513bf` (HEAD) |
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
| Results Directory | `results/locomo/threadatlas-captions-full` |

**Reproduce:**

```bash
./scripts/run_locomo_eval.sh --replay results/locomo/threadatlas-captions-full
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
| Answer API Calls | 1,540 |
| Context Tokens (avg) | 6317.1 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 0.8942 ± 0.0000 |
| F1 | 0.2742 |
| ROUGE-1 | 0.2794 |
| ROUGE-2 | 0.1461 |
| ROUGE-L | 0.2606 |
| BLEU-1 | 0.1690 |
| BLEU-4 | 0.0646 |
| METEOR | 0.4203 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| multi hop | 0.8475 | 282 |
| temporal reasoning | 0.8474 | 321 |
| open domain | 0.6146 | 96 |
| single hop | 0.9596 | 841 |

### Pipeline Status

| Stage | Failed Groups | Skipped Records | Status Counts |
|-------|---------------|-----------------|---------------|
| search | 0 | 0 | success=1540 |
| answer | 0 | 0 | success=1540 |
| eval | 0 | 0 | success=1540 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 41640.4 | 42235.3 | 54648.1 |
| Search Latency | 550.1 | 544.4 | 642.6 |
