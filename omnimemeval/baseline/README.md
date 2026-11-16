# ThreadAtlas on OmniMemEval: the baseline runs

ThreadAtlas's runs of all five benchmarks of [OmniMemEval](https://github.com/MemTensor/OmniMemEval)'s User Memory
track with the leaderboard's baseline models, run on 2026-11-16 by Justin Hoffman. This folder holds every record the
harness wrote, the reading model's call log, the notebooks that ran them, and the checksums.

Every session is read during the run. `add()` hands ThreadAtlas one session, ThreadAtlas reads it with
`gpt-4.1-mini-2025-04-14` and writes it into that user's own store, and `search()` runs on that store alone. Nothing
is prepared beforehand.

## Results

One full run per benchmark, every question scored.

| Benchmark | Score | Questions | Right | Context tokens | Stores | `add()` calls | Run time |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoCoMo | 88.90 | 1,540 | 1,369 | 6,213 | 20 | 544 | 41 min |
| LongMemEval | 87.00 | 500 | 435 | 4,351 | 500 | 23,867 | 4 h 00 min |
| BEAM 100K | 73.12 | 400 | | 5,664 | 20 | 90 | 1 h 35 min |
| PersonaMem v2 | 36.92 | 5,000 | 1,846 | 4,268 | 200 | 2,426 | 4 h 49 min |
| HaluMem-Medium | 83.82 | 3,467 | 2,906 | 3,052 | 20 | 1,387 | 4 h 12 min |

LoCoMo, LongMemEval and HaluMem are LLM-as-judge accuracy. BEAM is the mean nugget score over its questions, times
100, with a per-question standard deviation of 34.41. PersonaMem v2 is rule-matching accuracy.

### LoCoMo by category

| Single-Hop | Multi-Hop | Temporal | Open-Domain | Overall |
|---:|---:|---:|---:|---:|
| 93.22 | 85.11 | 86.29 | 70.83 | 88.90 |

### LongMemEval by question type

| Single-session user | Single-session assistant | Single-session preference | Temporal reasoning | Multi-session | Knowledge update | Overall |
|---:|---:|---:|---:|---:|---:|---:|
| 100.00 | 96.43 | 93.33 | 84.21 | 77.44 | 87.18 | 87.00 |

### BEAM 100K by dimension

Mean nugget score, 40 questions each.

| Abstention | Contradiction resolution | Event ordering | Information extraction | Instruction following | Knowledge update | Multi-session reasoning | Preference following | Summarization | Temporal reasoning |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.8625 | 0.7688 | 0.2445 | 0.8656 | 0.8938 | 0.5875 | 0.6547 | 0.8875 | 0.7657 | 0.7812 |

### PersonaMem v2 by preference type

| Anti-stereotypical | Ask to forget | Health and medical | Neutral | Sensitive | Stereotypical | Therapy | Overall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 30.29 | 47.42 | 36.09 | 34.15 | 31.51 | 36.96 | 37.32 | 36.92 |

### HaluMem-Medium by question type

| Basic fact recall | Memory boundary | Memory conflict | Generalization and application | Multi-hop inference | Dynamic update | Overall |
|---:|---:|---:|---:|---:|---:|---:|
| 75.34 | 92.63 | 88.43 | 86.06 | 78.28 | 55.56 | 83.82 |

## What ran

| | |
|---|---|
| Harness | MemTensor/OmniMemEval at commit [`5e8cdc1`](https://github.com/MemTensor/OmniMemEval/tree/5e8cdc115b2eff391e72192dbfe3786ebadc9005), unchanged. Every run's `experiment_config.sh` records `git_dirty=0` |
| Adapter | `threadatlas`, in-process, part of the harness at that commit |
| Package | [`threadatlas_memory/`](../../threadatlas_memory/) at commit [`015143c`](https://github.com/jhffmn82/threadatlas/tree/015143cdb995497022b88878c8ebc8c5223d1eee/threadatlas_memory), unchanged. Each run's `provenance.json` records both commits |
| Reading model | `gpt-4.1-mini-2025-04-14`, OpenAI API (`THREADATLAS_READ_MODEL`). No store built beforehand: `THREADATLAS_STORE_DIR`, `THREADATLAS_STEP0_DIR` and `THREADATLAS_SOURCE` were not set, and the notebook stops if one is attached |
| Answer model | `gpt-4.1-mini-2025-04-14`, OpenAI API |
| Judge model | `gpt-4o-mini-2024-07-18`, OpenAI API |
| Embeddings | `BAAI/bge-small-en-v1.5` through fastembed, on the machine running the harness |
| Retrieval | `top_k` 20: the packet's header and up to 19 records; 40 hits from each of vector and keyword search, fused by rank; two hops through the graph |
| Data | prepared by the harness's own prepare scripts. Each run's `provenance.json` holds the SHA-256 of its prepared file |
| Workers | users read side by side: LoCoMo 10, LongMemEval 60, BEAM 20, PersonaMem v2 20, HaluMem 20. One user's sessions are added in order. `LLM_WORKERS` 10; one run each (`NUM_RUNS` 1) |
| Machine | a Kaggle notebook, one notebook version per benchmark. LongMemEval ran the embedding model on a T4 GPU (`THREADATLAS_EMBED_DEVICE="cuda"`). The other four ran on CPU |
| Environment | Python and every installed package with its version, in each run's `environment.txt` |

**Coverage.** In every run each stage finished every record, with no failed, skipped or excluded item. PersonaMem v2
is scored by rule matching, so it has a search and an answer stage and no judge stage.

**Scoring.** The harness's own scores. The judged files give the same counts: LoCoMo 1,369 of 1,540, LongMemEval 435
of 500, HaluMem 2,906 of 3,467, and a mean nugget score of 0.7312 over BEAM's 400 questions. PersonaMem v2's
responses file gives 1,846 of 5,000.

**Context tokens** are the harness's count of prompt tokens sent to the answer model, divided by the answer calls, as
each run's report prints it.

**Reading.** Every call to the reading model is a line of the run's `reading-calls.jsonl`, with its stage, token
counts and cost at list price.

| Benchmark | Reading calls | Tokens in | Tokens out | Cost at list price |
|---|---:|---:|---:|---:|
| LoCoMo | 1,597 | 1.54 M | 0.71 M | $1.75 |
| LongMemEval | 85,253 | 148.22 M | 82.98 M | $192.06 |
| BEAM 100K | 735 | 3.81 M | 1.09 M | $3.27 |
| PersonaMem v2 | 8,168 | 13.43 M | 5.61 M | $14.35 |
| HaluMem-Medium | 4,716 | 8.93 M | 4.85 M | $11.33 |

## These runs and the runs of 2026-11-07

The [runs of 2026-11-07](../README.md) used `gpt-5.6-luna` as the reading model. Their LongMemEval score, 87.40, is
ThreadAtlas's full pipeline: every `longmemeval_s` history went through extraction, ingestion and the global merge,
and each user's store is that user's documents from that store.

The runs here are a test pipeline for the leaderboard's baseline: extraction, ingestion and retrieval for one user at
a time through `add()`, with `gpt-4.1-mini-2025-04-14` as the reading model. The global merge works over a whole
corpus, and `add()` hands over one user's session at a time, so these runs do not include it.

## Every run in this setting

| Run (UTC) | Benchmark | Harness | Package | Result |
|---|---|---|---|---|
| 2026-11-07 | LoCoMo | `7c79d46` with the adapter's files | published as `a3337c5f` | 88.44 (1,362 of 1,540), in [`../results/locomo/threadatlas-ta021-41mini-full`](../results/locomo/threadatlas-ta021-41mini-full/) |
| 2026-11-16 04:20 | LoCoMo | `5e8cdc1` | `18df19c` | 89.68 (1,381 of 1,540), in [`locomo-run-of-04-20/`](locomo-run-of-04-20/) |
| 2026-11-16 06:00 | LoCoMo | `5e8cdc1` | `015143c` | 88.90 (1,369 of 1,540), in [`locomo/`](locomo/) |
| 2026-11-16 07:13 | BEAM 100K | `5e8cdc1` | `015143c` | 73.12, in [`beam-100k/`](beam-100k/) |
| 2026-11-16 07:16 | PersonaMem v2 | `5e8cdc1` | `015143c` | 36.92, in [`personamem-v2/`](personamem-v2/) |
| 2026-11-16 07:18 | LongMemEval | `5e8cdc1` | `015143c` | 87.00, in [`longmemeval/`](longmemeval/) |
| 2026-11-16 07:25 | HaluMem-Medium | `5e8cdc1` | `015143c` | 83.82, in [`halumem-medium/`](halumem-medium/) |

LoCoMo has three full runs in this setting. The reported one is the last, the run on the package revision that every
other benchmark used. Between `18df19c` and `015143c` the package gained retries on rate limits, a lock so that one
batch is embedded at a time, the GPU option and an "undated" label for a session added with no date. None of these
changes how a dated session is read or retrieved. The three scores span 1.24 points. No run is combined with another.

Before the full runs, the first users of four benchmarks were run once to time them. They are partial runs, not
scores. Their records are in [`short-runs/`](short-runs/).

| Run (UTC) | Benchmark | Users | Questions | Result |
|---|---|---|---:|---|
| 2026-11-16 06:02 | BEAM 100K | 1 of 20 conversations | 20 | nugget score 0.6737 |
| 2026-11-16 06:03 | HaluMem-Medium | 1 of 20 users | 164 | 84.76 |
| 2026-11-16 06:05 | PersonaMem v2 | 2 of 200 personas | 56 | 42.86 |
| 2026-11-16 06:06 | LongMemEval | 20 of 500 users | 20 | 20 of 20 |

## Reproducing a run

On Kaggle, the notebooks in [`run/`](run/) do every step: one notebook per benchmark, each needing an `OPENAI_API_KEY`
secret and no dataset. [`run/make_notebook.py`](run/make_notebook.py) wrote them. On any machine:

```bash
git clone https://github.com/MemTensor/OmniMemEval.git
cd OmniMemEval
git checkout 5e8cdc115b2eff391e72192dbfe3786ebadc9005
git clone https://github.com/jhffmn82/threadatlas.git ../threadatlas
git -C ../threadatlas checkout 015143cdb995497022b88878c8ebc8c5223d1eee
pip install -r requirements_user_memory.txt tiktoken fastembed
python data/locomo/prepare_locomo.py
python data/longmemeval/prepare_longmemeval.py
python data/beam/prepare_beam.py --scale 100k
python data/personamem_v2/prepare_personamem.py
python data/halumem/prepare_halumem.py
cp env_examples/.env.threadatlas .env.threadatlas      # then set it as below
bash scripts/run_locomo_eval.sh --lib threadatlas --env .env.threadatlas --version base-full --workers 10
bash scripts/run_lme_eval.sh --lib threadatlas --env .env.threadatlas --version base-full --workers 60
bash scripts/run_beam_eval.sh --lib threadatlas --env .env.threadatlas --version base-full --workers 20 --scale 100k
bash scripts/run_pmv2_eval.sh --lib threadatlas --env .env.threadatlas --version base-full --workers 20
bash scripts/run_halumem_eval.sh --lib threadatlas --env .env.threadatlas --version base-full --workers 20 --variant medium
```

`.env.threadatlas` names the ThreadAtlas checkout (`THREADATLAS_REPO`) and a folder for the users' stores
(`THREADATLAS_STATE_DIR`), sets `THREADATLAS_READ_MODEL="gpt-4.1-mini-2025-04-14"`, and has no
`THREADATLAS_STORE_DIR`, `THREADATLAS_STEP0_DIR` or `THREADATLAS_SOURCE` line. The answer and judge settings are those
of each run's `snapshot_eval.env`. API keys come from the environment.

## Data licenses

The records quote the benchmarks' own text, unchanged.

- LoCoMo ([snap-research/locomo](https://github.com/snap-research/locomo), Maharana et al., 2024) is licensed
  CC BY-NC 4.0, so its records are for non-commercial use with attribution to the LoCoMo authors.
- LongMemEval ([xiaowu0162/LongMemEval](https://github.com/xiaowu0162/LongMemEval), Wu et al., 2024) is licensed MIT.
- BEAM ([mohammadtavakoli78/BEAM](https://github.com/mohammadtavakoli78/BEAM), [arXiv:2510.27246](https://arxiv.org/abs/2510.27246)) is licensed
  CC BY-SA 4.0, so its records carry the same license with attribution to the BEAM authors.
- PersonaMem v2 ([bowen-upenn/PersonaMem-v2](https://github.com/bowen-upenn/PersonaMem-v2),
  [arXiv:2512.06688](https://arxiv.org/abs/2512.06688)) is licensed MIT.
- HaluMem ([MemTensor/HaluMem](https://github.com/MemTensor/HaluMem),
  [arXiv:2511.03506](https://arxiv.org/abs/2511.03506)) is licensed CC BY-NC-ND 4.0, so its records are for non-commercial use with attribution to the HaluMem authors.

## Files

Each run's folder is the notebook's output as Kaggle kept it, without the per-user search files of `tmp/`, which the
combined search results repeat.

| Path | What it holds |
|---|---|
| `locomo/`, `longmemeval/`, `beam-100k/`, `personamem-v2/`, `halumem-medium/` | the reported run of each benchmark |
| `locomo-run-of-04-20/` | the LoCoMo run of 04:20 UTC on package `18df19c` |
| `short-runs/` | the four timing runs: their records without the search results and responses |
| `<run>/results/<benchmark>/threadatlas-base-full/` | the harness's records: search results, responses, judged answers, grades, status files, token usage, settings, report |
| `<run>/reading-calls.jsonl` | every call to the reading model: stage, model, tokens in and out, seconds, cost, session |
| `<run>/provenance.json` | the run's setting, the harness and package commits, the prepared file's SHA-256, the users, the workers, the embedding device, the account's rate limits |
| `<run>/environment.txt` | Python and the installed packages with their versions |
| `<run>/<benchmark>-base-full.log` | the harness's own output |
| `<run>/kernel.log` | the notebook's output |
| `run/` | the five notebooks and the script that wrote them |
| `SHA256SUMS` | a checksum for every other file in this folder |
