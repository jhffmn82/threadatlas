# OmniMemEval Experiment Report — threadatlas-base-full

> Generated: 2026-11-16 11:38:13

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | HaluMem |
| Memory Framework | threadatlas |
| Version | base-full |
| Run Time | 2026-11-16 07:25:58 UTC |
| Git | `5e8cdc1` (HEAD) |
| WORKERS | 20 |
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
| Results Directory | `results/halumem/threadatlas-base-full` |

**Reproduce:**

```bash
./scripts/run_halumem_eval.sh --replay results/halumem/threadatlas-base-full
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
| Answer API Calls | 3,467 |
| Context Tokens (avg) | 3051.6 |

## Evaluation Results

### Overall Scores

| Metric | Score |
|--------|-------|
| QA Accuracy (LLM-as-Judge) | 0.8382 ± 0.0000 |
| F1 | 0.2106 |
| ROUGE-1 | 0.1698 |
| ROUGE-2 | 0.0657 |
| ROUGE-L | 0.1365 |
| BLEU-1 | 0.1101 |
| BLEU-4 | 0.0266 |
| METEOR | 0.2868 |
| BERTScore F1 | - |
| Semantic Similarity | - |

### By Question Type (QA Accuracy)

| Question Type | QA Accuracy | Questions |
|---------------|-------------|-----------|
| Basic Fact Recall | 0.7534 | 746 |
| Memory Boundary | 0.9263 | 828 |
| Memory Conflict | 0.8843 | 769 |
| Generalization & Application | 0.8606 | 746 |
| Multi-hop Inference | 0.7828 | 198 |
| Dynamic Update | 0.5556 | 180 |

### By Difficulty

| Difficulty | QA Accuracy | Questions |
|------------|-------------|-----------|
| easy | 0.8472 | 1970 |
| hard | 0.7959 | 98 |
| medium | 0.8284 | 1399 |

### Pipeline Status

| Stage | Failed Users | Failed Questions | Skipped Records | Status Counts |
|-------|--------------|------------------|-----------------|---------------|
| search | 0 | 0 | 0 | success=3467 |
| answer | 0 | 0 | 0 | success=3467 |
| eval | 0 | 0 | 0 | success=3467 |

### Latency Metrics

| Metric | Avg (ms) | P50 (ms) | P95 (ms) |
|--------|----------|----------|----------|
| Add Latency | 180228.5 | 186900.2 | 227138.8 |
| Search Latency | 1669.7 | 1704.8 | 1995.4 |
