# OmniMemEval Experiment Report — threadatlas-base-full

> Generated: 2026-11-16 06:41:38

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | LoCoMo |
| Memory Framework | threadatlas |
| Version | base-full |
| Run Time | 2026-11-16 06:00:26 UTC |
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
| Context Tokens (avg) | 6213.1 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| LLM-as-Judge | 0.8890 ± 0.0000 |
| F1 | 0.2696 |
| ROUGE-1 | 0.2738 |
| ROUGE-2 | 0.1425 |
| ROUGE-L | 0.2553 |
| BLEU-1 | 0.1656 |
| BLEU-4 | 0.0617 |
| METEOR | 0.4126 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### Category Breakdown

| Category | LLM-Judge | Questions |
|----------|-----------|-----------|
| multi hop | 0.8511 | 282 |
| temporal reasoning | 0.8629 | 321 |
| open domain | 0.7083 | 96 |
| single hop | 0.9322 | 841 |

### Pipeline Status

| Stage | Failed Groups | Skipped Records | Status Counts |
|-------|---------------|-----------------|---------------|
| search | 0 | 0 | success=1540 |
| answer | 0 | 0 | success=1540 |
| eval | 0 | 0 | success=1540 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 34066.0 | 34612.1 | 46015.3 |
| Search Latency | 499.8 | 498.8 | 574.2 |
