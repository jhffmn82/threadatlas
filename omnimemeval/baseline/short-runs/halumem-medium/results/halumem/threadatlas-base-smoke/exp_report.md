# OmniMemEval Experiment Report — threadatlas-base-smoke

> Generated: 2026-11-16 06:49:09

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | HaluMem |
| Memory Framework | threadatlas |
| Version | base-smoke |
| Run Time | 2026-11-16 06:03:43 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 1 |
| LLM_WORKERS | 10 |
| TOPK | 20 |
| VARIANT | medium |
| NUM_RUNS | 1 |
| SAVE_MODEL_INPUT | 0 |
| CLEAR | 0 |
| WAIT_AFTER_INGEST | 0 |
| ALLOW_EMPTY_SEARCH | 1 |
| SKIP_FAILED_SEARCH | 0 |
| SKIP_FAILED_ANSWER | 0 |
| SKIP_FAILED_JUDGE | 0 |
| Results Directory | `results/halumem/threadatlas-base-smoke` |

**Reproduce:**

```bash
./scripts/run_halumem_eval.sh --replay results/halumem/threadatlas-base-smoke
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
| Answer API Calls | 164 |
| Context Tokens (avg) | 3042.6 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| QA Accuracy (LLM-as-Judge) | 0.8476 ± 0.0000 |
| F1 | 0.2103 |
| ROUGE-1 | 0.1684 |
| ROUGE-2 | 0.0669 |
| ROUGE-L | 0.1411 |
| BLEU-1 | 0.1087 |
| BLEU-4 | 0.0274 |
| METEOR | 0.2864 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### By Question Type (QA Accuracy)

| Question Type | QA Accuracy | Questions |
|---------------|-------------|-----------|
| Basic Fact Recall | 0.8250 | 40 |
| Memory Boundary | 0.9487 | 39 |
| Memory Conflict | 0.8205 | 39 |
| Generalization & Application | 0.8065 | 31 |
| Multi-hop Inference | 0.8889 | 9 |
| Dynamic Update | 0.6667 | 6 |

### By Difficulty

| Difficulty | QA Accuracy | Questions |
|------------|-------------|-----------|
| easy | 0.8842 | 95 |
| hard | 0.5000 | 2 |
| medium | 0.8060 | 67 |

### Pipeline Status

| Stage | Failed Users | Failed Questions | Skipped Records | Status Counts |
|-------|--------------|------------------|-----------------|---------------|
| search | 0 | 0 | 0 | success=164 |
| answer | 0 | 0 | 0 | success=164 |
| eval | 0 | 0 | 0 | success=164 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 40354.9 | 36269.8 | 68219.7 |
| Search Latency | 102.4 | 95.0 | 137.0 |
