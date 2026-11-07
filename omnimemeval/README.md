# ThreadAtlas on OmniMemEval

ThreadAtlas's runs of [OmniMemEval](https://github.com/MemTensor/OmniMemEval)'s User Memory track: LoCoMo and
LongMemEval, run on 2026-11-07 by Justin Hoffman. This folder holds every record the harness wrote, the notebook that
ran it, and the checksums. The memory itself is [`threadatlas_memory/`](../threadatlas_memory/) at the root of this
repository, and the adapter is on the branch
[`threadatlas-adapter`](https://github.com/jhffmn82/OmniMemEval/tree/threadatlas-adapter) of a fork of the harness.

## Results

LLM-as-judge accuracy with the harness's own answer and judge models, one run each, every question scored.

| Benchmark | ThreadAtlas reading model | Accuracy | Questions | Context tokens | Search, avg | Add, avg |
|---|---|---:|---:|---:|---:|---:|
| LoCoMo | `gpt-5.6-luna` | 89.22 | 1,540 | 6,190 | 0.46 s | 76.2 s |
| LoCoMo | `gpt-4.1-mini-2025-04-14` | 88.44 | 1,540 | 6,200 | 0.54 s | 28.9 s |
| LongMemEval | `gpt-5.6-luna`, read before the run | 87.40 | 500 | 4,332 | 0.64 s | 0.20 s |

### LoCoMo by category

| Reading model | Single-Hop | Multi-Hop | Temporal | Open-Domain | Overall |
|---|---:|---:|---:|---:|---:|
| `gpt-5.6-luna` | 94.17 | 83.69 | 86.29 | 71.88 | 89.22 |
| `gpt-4.1-mini-2025-04-14` | 92.27 | 85.46 | 86.60 | 69.79 | 88.44 |

### LongMemEval by question type

| Knowledge update | Multi-session | Single-session assistant | Single-session preference | Single-session user | Temporal reasoning | Overall |
|---:|---:|---:|---:|---:|---:|---:|
| 89.74 | 79.70 | 96.43 | 86.67 | 100.00 | 83.46 | 87.40 |

## What ran

| | |
|---|---|
| Harness | MemTensor/OmniMemEval at commit [`7c79d46`](https://github.com/MemTensor/OmniMemEval/tree/7c79d46e31dd85f3da2509b430bba9406656dd28), with the adapter's files from [`jhffmn82/OmniMemEval@67941d5`](https://github.com/jhffmn82/OmniMemEval/commit/67941d5) copied over it (the reports' "dirty" flag counts those files) |
| Adapter | `threadatlas`, in-process; `THREADATLAS_REPO` is the root of this repository |
| Package | each run used the copy of [`threadatlas_memory/`](../threadatlas_memory/) in the Kaggle dataset [`jhffmn/threadatlas-omni-kit`](https://www.kaggle.com/datasets/jhffmn/threadatlas-omni-kit): version 2 for LoCoMo with `gpt-5.6-luna` (notebook version 6), version 3 for LongMemEval (notebook version 8), version 4 for LoCoMo with `gpt-4.1-mini-2025-04-14` (notebook version 10). Version 3 added a database connection per thread and version 4 the `THREADATLAS_READ_MODEL` setting; the copy here is version 4 with comments updated |
| LoCoMo | `locomo10.json` from snap-research/locomo, SHA-256 `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`; categories 1 to 4, 1,540 questions |
| LongMemEval | `longmemeval_s_cleaned.json`, SHA-256 `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`; 500 questions |
| Answer model | `gpt-4.1-mini-2025-04-14`, OpenAI API |
| Judge model | `gpt-4o-mini-2024-07-18`, OpenAI API |
| Embeddings | `BAAI/bge-small-en-v1.5` through fastembed, on the machine running the harness |
| Retrieval | `top_k` 20: the packet's header and up to 19 records; 40 hits from each of vector and keyword search, fused by rank; two hops through the graph; a cap of 100,000 tokens |
| Workers | LoCoMo 10, LongMemEval 4; `LLM_WORKERS` 10; one run each (`NUM_RUNS` 1) |
| Machine | Kaggle CPU notebook [`jhffmn/threadatlas-omnimemeval`](https://www.kaggle.com/code/jhffmn/threadatlas-omnimemeval) |

**How a session gets into memory.** Each `add()` is one session. ThreadAtlas reads it into dated facts, each tied to
the words of the turn it came from, and writes it into that user's own store with its 256-token chunks of text, its
keyword rows and its vectors. The reading model is `gpt-5.6-luna` unless `THREADATLAS_READ_MODEL` names another.

The LoCoMo sessions were read during the run. The LongMemEval sessions had all been read before it: ThreadAtlas's
pipeline read every `longmemeval_s` history into its global store, the Kaggle dataset
[`jhffmn/threadatlas-global-chunks`](https://www.kaggle.com/datasets/jhffmn/threadatlas-global-chunks). For each
LongMemEval session, `add()` finds that session in the store by its turns and its minute and copies its rows and vectors
into the user's store, so no LongMemEval session was read during the run. A user's store holds that user's sessions
alone.

**Coverage.** Every stage finished every record: no failed, skipped, timed-out or excluded items in search, answer or
judging. Each accuracy is over every question.

**Scoring.** The harness's own judge marks each answer right or wrong, and each accuracy is the share of
questions marked right, so the LongMemEval overall weights each type by its question count. One run per benchmark
and setting; no run is combined with another.

**Context tokens** are the harness's own count of prompt tokens sent to the answer model, averaged per question. The
totals and call counts are in each run's `token_usage_answer.json`.

## Every run

Each full run of the harness on ThreadAtlas, in order. The scores above are the runs of versions 6 (LoCoMo,
`gpt-5.6-luna`), 8 (LongMemEval) and 10 (LoCoMo, `gpt-4.1-mini-2025-04-14`).

| Date (UTC) | Benchmark | Notebook version | What changed | Result |
|---|---|---:|---|---|
| 2026-11-06 | LongMemEval | 4 | retrieval without chunks; each user's store built at the first search | 87.20 |
| 2026-11-06 | LoCoMo | 4 | the same | 89.35 |
| 2026-11-07 | LoCoMo | 6 | chunks; each `add()` writes into the user's store | 89.22 |
| 2026-11-07 | LongMemEval | 6 | the same | not used: 258 of 500 conversations had sessions fail at ingestion, because parallel adds shared one database connection |
| 2026-11-07 | LongMemEval | 8 | each thread opens its own connection | 87.40 |
| 2026-11-07 | LoCoMo | 10 | sessions read with `gpt-4.1-mini-2025-04-14` | 88.44 |

## Reproducing a run

On Kaggle, the notebook in [`run/`](run/) does every step; attach the datasets it names and an `OPENAI_API_KEY` secret.
Its first cell picks the run: `BENCHMARKS`, `LABEL` and `READ_MODEL`. Version 6 ran `["lme", "locomo"]` and version 8
`["lme"]`, both with the label `ta021` and the default reading model; version 10, the copy here, ran `["locomo"]` with
the label `ta021-41mini` and `gpt-4.1-mini-2025-04-14`.
On any machine:

```bash
git clone https://github.com/MemTensor/OmniMemEval.git
cd OmniMemEval
git checkout 7c79d46e31dd85f3da2509b430bba9406656dd28
git fetch https://github.com/jhffmn82/OmniMemEval.git threadatlas-adapter
git checkout FETCH_HEAD -- scripts docs env_examples
pip install -r requirements_user_memory.txt fastembed tiktoken
python data/longmemeval/prepare_longmemeval.py
python data/locomo/prepare_locomo.py
cp env_examples/.env.threadatlas .env.threadatlas      # then set the paths in it
bash scripts/run_locomo_eval.sh --lib threadatlas --env .env.threadatlas --version ta021-full --workers 10
bash scripts/run_lme_eval.sh --lib threadatlas --env .env.threadatlas --version ta021-full --workers 4
```

`.env.threadatlas` names this repository, a folder for the users' stores, the global store
([`jhffmn/threadatlas-global-chunks`](https://www.kaggle.com/datasets/jhffmn/threadatlas-global-chunks)), Step 0's export
([`jhffmn/it494-threadatlas-step0`](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0)) and
`longmemeval/longmemeval_s.json` from
[`jhffmn/it494-narrative-corpora-raw`](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw). For the
`gpt-4.1-mini-2025-04-14` run, add `THREADATLAS_READ_MODEL="gpt-4.1-mini-2025-04-14"`. The answer and judge settings
are those of [`run/snapshot.env`](run/snapshot.env). API keys come from the environment.

## Data licenses

The records quote the benchmarks' own text. LoCoMo ([snap-research/locomo](https://github.com/snap-research/locomo),
Maharana et al., 2024) is licensed CC BY-NC 4.0, so its records are for non-commercial use with attribution to the
LoCoMo authors. LongMemEval ([xiaowu0162/LongMemEval](https://github.com/xiaowu0162/LongMemEval), Wu et al., 2024)
is licensed MIT.

## Files

| Path | What it holds |
|---|---|
| `results/locomo/threadatlas-ta021-full/` | the LoCoMo run with `gpt-5.6-luna` reading: search results, responses, judged answers, grades, status files, token usage, report |
| `results/locomo/threadatlas-ta021-41mini-full/` | the LoCoMo run with `gpt-4.1-mini-2025-04-14` reading, the same files |
| `results/lme/threadatlas-ta021-full/` | the LongMemEval run, the same files |
| `run/threadatlas-omnimemeval.ipynb` | the Kaggle notebook |
| `run/snapshot.env` | the harness settings of versions 6 and 8, without keys; version 10's adds `THREADATLAS_READ_MODEL` |
| `SHA256SUMS` | a checksum for every file in `results/` and `run/` |
