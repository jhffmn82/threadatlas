# Retrieval 0.21: every result, with commentary

All results of `threadatlas-retrieval 0.21` (the Kaggle notebooks below)
on the 0.7 store, which holds chunks as records, and the OmniMemEval entry of `threadatlas_memory` at the
same version. The paper's results part cites this file for every number it does not print. Collected
2026-11-07.

## Where each number comes from

| Set | Kaggle notebook | File |
|---|---|---|
| LongMemEval `_s`, filtered and whole store | `jhffmn/threadatlas-retrieval-memory`, version 10 | `results.json`, `memory` |
| GraphRAG-Bench Novel, own set | `jhffmn/threadatlas-novels-filtered` | `results.json`, `graphrag_bench.novels` |
| GraphRAG-Bench Novel, whole store | `jhffmn/threadatlas-novels-unfiltered` | `results.json`, `graphrag_bench.novels` |
| GraphRAG-Bench Medical, own set | `jhffmn/threadatlas-medical-chunks-run` | `results.json`, `graphrag_bench.medical` |
| OmniMemEval LoCoMo and LongMemEval | ThreadAtlas's rows for the board's `docs/user_memory/results.md` | every record the harness wrote: github.com/jhffmn82/threadatlas, `omnimemeval/` |

Every run used reader `gpt-4o-mini-2024-07-18` at temperature 0, except OmniMemEval, which fixes reader
`gpt-4.1-mini-2025-04-14` and judge `gpt-4o-mini-2024-07-18`. LongMemEval's judge is `gpt-4o-2024-08-06`.
GraphRAG-Bench is scored by its own evaluator at commit `fdbab59`, unchanged, with `gpt-4o-mini` and
`bge-large-en-v1.5`.

## The arms

| Arm | What the reader gets |
|---|---|
| plain RAG (`flat-` on LongMemEval, `plain-rag-` on GraphRAG-Bench) | raw text by vector search, packed to the budget: turns on LongMemEval, 256-token chunks of the source on GraphRAG-Bench |
| plain RAG, top 5 (`plain-rag`) | the benchmark's own five chunks |
| chunks through hybrid search (`chunks-hybrid-`) | the store's chunks only, found by ThreadAtlas's fused keyword and vector search; no fact, cell, abstract or parent; no walk |
| graph and chunks, hop 0, 1, 2 (`hop<n>-`) | ThreadAtlas 0.21: facts, cells, abstracts, parents and chunks, found by the same fused search, then a walk of 0, 1 or 2 hops, packed as whole bundles |
| full context | LongMemEval only: the question's whole history |
| no context | GraphRAG-Bench only: the question alone |

Budgets are 2,000 and 12,000 tokens. "Filtered" searches each question's own history (LongMemEval) or its
own set's documents (GraphRAG-Bench). "Whole store" searches all 24,071 documents: chats, books and
papers together. Medical has no whole-store run.

Plain RAG to chunks through hybrid search isolates the search. Chunks through hybrid search to graph and
chunks isolates the graph.

## LongMemEval

500 questions; accuracy with its standard error; won, lost and p are paired per question against plain
RAG at the same budget and filter (McNemar).

### Filtered: each question's own history

| Arm | Accuracy | se | Tokens | Won | Lost | p |
|---|---:|---:|---:|---:|---:|---:|
| plain RAG, 2,000 | 70.4 | 2.04 | 1,992 | | | |
| chunks, hybrid, 2,000 | 61.6 | 2.18 | 1,958 | 24 | 68 | < 0.001 |
| graph hop 0, 2,000 | 74.2 | 1.96 | 1,973 | 59 | 40 | 0.070 |
| graph hop 1, 2,000 | 73.2 | 1.98 | 1,980 | 58 | 44 | 0.198 |
| graph hop 2, 2,000 | 73.6 | 1.97 | 1,986 | 54 | 38 | 0.117 |
| plain RAG, 12,000 | 72.4 | 2.00 | 11,992 | | | |
| chunks, hybrid, 12,000 | 68.6 | 2.08 | 11,924 | 30 | 49 | 0.042 |
| graph hop 0, 12,000 | 74.0 | 1.96 | 9,390 | 47 | 39 | 0.451 |
| graph hop 1, 12,000 | 76.2 | 1.90 | 10,591 | 50 | 31 | 0.045 |
| graph hop 2, 12,000 | 75.2 | 1.93 | 11,795 | 46 | 32 | 0.141 |
| full context | 60.6 | 2.19 | 115,123 | | | |

### Whole store: all 24,071 documents

| Arm | Accuracy | se | Tokens | Won | Lost | p |
|---|---:|---:|---:|---:|---:|---:|
| plain RAG, 2,000 | 33.6 | 2.11 | 1,991 | | | |
| chunks, hybrid, 2,000 | 31.8 | 2.08 | 1,946 | 47 | 56 | 0.431 |
| graph hop 0, 2,000 | 45.2 | 2.23 | 1,969 | 97 | 39 | < 0.001 |
| graph hop 2, 2,000 | 45.4 | 2.23 | 1,983 | 98 | 39 | < 0.001 |
| plain RAG, 12,000 | 41.2 | 2.20 | 11,991 | | | |
| chunks, hybrid, 12,000 | 44.0 | 2.22 | 11,930 | 68 | 54 | 0.239 |
| graph hop 0, 12,000 | 47.0 | 2.23 | 11,157 | 74 | 45 | 0.010 |
| graph hop 1, 12,000 | 49.0 | 2.24 | 11,923 | 84 | 45 | < 0.001 |
| graph hop 2, 12,000 | 50.0 | 2.24 | 11,936 | 88 | 44 | < 0.001 |

Hop 1 at 2,000 tokens over the whole store was not run.

### Commentary

- **Over the whole store the graph wins at every setting, by 5.8 to 11.8 points** (best per budget:
  +11.8 at 2,000, +8.8 at 12,000; every graph arm p 0.01 or below). Hybrid search over
  chunks alone does not: it is within error of plain RAG at both budgets. On LongMemEval the gain over
  the whole store is the graph's, not the search's.
- **The graph loses less when the haystack becomes the library.** From each question's own history to
  the whole store, plain RAG falls 36.8 points at 2,000 tokens and 31.2 at 12,000; the best graph arm
  falls 28.8 and 26.2.
- **Filtered, the graph is ahead at every setting by 1.6 to 3.8 points.** One setting, hop 1 at
  12,000, is below p 0.05 before any correction for the number of comparisons. Chunks through hybrid
  search score below plain RAG filtered: a turn of a chat is a better unit than a 256-token chunk that
  cuts across turns.
- **The graph uses fewer tokens at 12,000 filtered** (9,390 at hop 0), because it packs whole bundles
  and stops when the next does not fit.
- **Full context, 60.6, is below every filtered arm**, all of which use 12,000 tokens or fewer
  against its 115,123.
- **0.20 against 0.21, filtered:** 0.20's best was 73.8 at hop 2, 12,000, tying plain RAG at 73.8.

## GraphRAG-Bench Novel

Figure: the mean of the four question types' answer correctness on the questions every arm scored.
"vs plain" is the paired difference per question against plain RAG at the same budget and filter, with
its standard error. Types: fact retrieval (FR), complex reasoning (CR), contextual summarize (CS),
creative generation (CG).

### Own set: 1,968 questions

| Arm | Figure | vs plain | se | Tokens | FR | CR | CS | CG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plain RAG, top 5 | 58.52 | | | 1,435 | 57.11 | 55.25 | 62.74 | 58.98 |
| plain RAG, 2,000 | 60.70 | | | 1,946 | 59.96 | 56.50 | 65.95 | 60.39 |
| chunks, hybrid, 2,000 | 63.04 | +2.44 | 0.60 | 1,922 | 63.20 | 57.76 | 68.26 | 62.93 |
| graph hop 0, 2,000 | 62.47 | +2.60 | 0.65 | 1,986 | 64.27 | 57.91 | 66.31 | 61.40 |
| graph hop 1, 2,000 | 63.14 | +2.17 | 0.66 | 1,988 | 63.29 | 57.30 | 66.95 | 65.02 |
| graph hop 2, 2,000 | 62.65 | +1.78 | 0.66 | 1,988 | 62.74 | 57.45 | 66.09 | 64.31 |
| plain RAG, 12,000 | 64.29 | | | 11,901 | 65.84 | 58.92 | 70.58 | 61.83 |
| chunks, hybrid, 12,000 | 64.39 | +0.36 | 0.54 | 11,899 | 66.40 | 59.28 | 70.59 | 61.29 |
| graph hop 0, 12,000 | 63.47 | -0.39 | 0.60 | 8,175 | 65.71 | 59.07 | 68.82 | 60.30 |
| graph hop 1, 12,000 | 63.71 | -0.45 | 0.60 | 10,072 | 65.31 | 59.57 | 68.50 | 61.46 |
| graph hop 2, 12,000 | 64.09 | -0.42 | 0.60 | 10,946 | 65.60 | 58.71 | 69.06 | 63.01 |
| no context | 36.56 | | | 89 | 25.68 | 32.96 | 41.52 | 46.10 |

No context scored 1,912 questions.

### Whole store: 1,954 questions

| Arm | Figure | vs plain | se | Tokens | FR | CR | CS | CG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plain RAG, 2,000 | 58.77 | | | 1,964 | 56.98 | 55.62 | 64.82 | 57.68 |
| chunks, hybrid, 2,000 | 58.32 | -0.37 | 0.66 | 1,946 | 57.57 | 54.98 | 62.18 | 58.56 |
| graph hop 0, 2,000 | 60.51 | +1.60 | 0.70 | 1,983 | 59.11 | 57.28 | 64.57 | 61.07 |
| graph hop 2, 2,000 | 60.61 | +1.61 | 0.70 | 1,987 | 59.29 | 56.29 | 65.86 | 60.99 |
| plain RAG, 12,000 | 63.91 | | | 11,940 | 62.96 | 59.58 | 69.83 | 63.25 |
| chunks, hybrid, 12,000 | 63.54 | -1.53 | 0.60 | 11,928 | 61.51 | 56.94 | 69.16 | 66.55 |
| graph hop 0, 12,000 | 63.37 | -0.42 | 0.64 | 10,325 | 63.17 | 58.52 | 68.80 | 62.99 |
| graph hop 1, 12,000 | 63.58 | -0.40 | 0.64 | 11,394 | 63.16 | 58.03 | 69.69 | 63.44 |
| graph hop 2, 12,000 | 62.55 | -1.32 | 0.63 | 11,708 | 62.36 | 57.54 | 67.71 | 62.58 |

Every arm scored the same 1,954 questions. Hop 1 at 2,000 tokens over the whole store was not run.

### Commentary

- **At 12,000 tokens the graph ties plain RAG.** On its own set every hop is within one standard
  error, with 8,175 to 10,946 tokens against plain RAG's 11,901. Over the whole store hops 0 and 1 tie
  (-0.42, -0.40); hop 2 trails by 1.32 (se 0.63), and hybrid search alone by 1.53 (se 0.60).
- **At 2,000 tokens on its own set the graph beats plain RAG by about 2 points, and so does hybrid
  search over chunks alone** (+2.44). There the gain is the search's.
- **At 2,000 tokens over the whole store the graph beats plain RAG by 1.6 (about 2.3 se) and hybrid
  search alone does not** (-0.37). There the gain is the graph's, as on LongMemEval.
- **From own set to whole store, hybrid search over chunks falls 4.7 points at 2,000 tokens; the graph
  falls about 2.** The question sets differ slightly (1,968 and 1,954).
- **0.20, the graph without chunks** (the retrieval 0.20 Novel run, 1,931 questions): hop 0 at 12,000
  scored 61.14 against plain RAG's 64.12, -5.07 per question (se 0.68). With chunks as records, 0.21
  closes that gap.

## GraphRAG-Bench Medical

Own set only: the Medical store holds the medical corpus alone. 1,971 questions scored by every arm, of
2,062.

| Arm | Figure | vs plain | se | Tokens | FR | CR | CS | CG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plain RAG, top 5 | 70.03 | | | 1,423 | 68.70 | 72.09 | 74.10 | 65.22 |
| plain RAG, 2,000 | 70.96 | | | 1,957 | 70.79 | 72.84 | 73.95 | 66.26 |
| chunks, hybrid, 2,000 | 70.71 | -0.14 | 0.52 | 1,914 | 70.61 | 73.13 | 73.31 | 65.78 |
| graph hop 0, 2,000 | 71.62 | +0.50 | 0.55 | 1,987 | 70.98 | 74.13 | 73.77 | 67.62 |
| graph hop 1, 2,000 | 70.75 | -0.05 | 0.56 | 1,990 | 70.62 | 73.76 | 72.73 | 65.89 |
| graph hop 2, 2,000 | 71.08 | -0.24 | 0.57 | 1,989 | 69.98 | 73.17 | 74.60 | 66.57 |
| plain RAG, 12,000 | 75.08 | | | 11,907 | 73.97 | 78.45 | 78.17 | 69.72 |
| chunks, hybrid, 12,000 | 74.49 | -0.56 | 0.47 | 11,900 | 73.85 | 76.75 | 77.66 | 69.70 |
| graph hop 0, 12,000 | 74.42 | -0.33 | 0.51 | 7,664 | 74.59 | 76.63 | 76.44 | 70.01 |
| graph hop 1, 12,000 | 74.88 | -0.11 | 0.51 | 9,888 | 74.41 | 77.40 | 77.09 | 70.60 |
| graph hop 2, 12,000 | 74.55 | -0.18 | 0.51 | 11,120 | 74.31 | 77.96 | 76.51 | 69.40 |
| no context | 36.08 | | | 89 | 25.67 | 43.96 | 25.71 | 48.97 |

No context scored 1,875 questions.

### Commentary

- **The graph ties plain RAG at every setting**, each difference within about one standard error.
- **At 12,000 tokens, hop 0 ties it with 7,664 tokens against 11,907**, about 36% fewer.
- **Hybrid search over chunks alone also ties.** On one corpus of one kind, neither the search nor the
  graph moves the score.
- **0.20 against 0.21:** 0.20's best graph arm scored 72.72 against plain RAG's 74.84. Chunks as records
  close that gap.
- **The board figure.** By the board's own figure hop 1 at 12,000 scores 74.58 and plain RAG at 12,000
  74.62: see "GraphRAG-Bench: the board's figure and our place" below.

## OmniMemEval

The board's fixed settings: reader `gpt-4.1-mini-2025-04-14`, judge `gpt-4o-mini-2024-07-18`, top-k 20,
one run each, every question scored. ThreadAtlas reads sessions with `gpt-5.6-luna`.

| Benchmark | Accuracy | Questions | Context tokens | Place |
|---|---:|---:|---:|---|
| LoCoMo, categories 1 to 4 | 89.22 | 1,540 | 6,190 | 1st of 16; MemOS 88.83 at 5,400 |
| LongMemEval, cleaned | 87.40 | 500 | 4,332 | 2nd of 14; MemOS 89.20 at 4,151, LCM-X 87.00 at 5,164 |

LoCoMo by type: single-hop 94.17 (841 questions), multi-hop 83.69 (282), temporal 86.29 (321),
open-domain 71.88 (96). ThreadAtlas has the highest score of the 16 on single-hop, temporal and
open-domain; MemOS leads multi-hop at 88.65.

LongMemEval by type: 100.00, 96.43, 86.67, 83.46, 79.70 and 89.74 in the board's column order
(the board's `docs/user_memory/results.md`).

A LoCoMo run with sessions read by `gpt-4.1-mini-2025-04-14` scored 88.44; an earlier version, before
chunks as records, 89.35. Both are in the artifacts.

### Commentary

- These are places among other memory systems under one reader and judge. There is no plain RAG run
  under the board's settings, so they measure ThreadAtlas against the field, not the graph against raw
  text.
- The board shows these rows once our submission is merged:
  https://github.com/MemTensor/OmniMemEval/pull/21 (opened 2026-11-07).

## GraphRAG-Bench: the board's figure and our place

The board averages each type's answer correctness over the questions that type scored, then takes the
plain mean of the four types. That is the figure below, read from the evaluator's own output for each
arm (`<set>-<arm>-generation.json`); the tables above use the questions common to every arm instead.
Places are against the boards as read on 2026-11-02 (21 rows each); the arm placed on each board is
hop 1 at 12,000 tokens, own set, as on the wiki.

| Set | Arm | Board figure | FR | CR | CS | CG | Place |
|---|---|---:|---:|---:|---:|---:|---|
| Novel | graph hop 1, 12,000 | 63.77 | 65.06 | 59.65 | 68.65 | 61.72 | 6th of 22, between KT-MOSAIC 64.28 and AutoPrunedRetriever-llm 63.72 |
| Novel | graph hop 0, 12,000 | 63.65 | 65.30 | 58.93 | 68.92 | 61.46 | |
| Novel | graph hop 2, 12,000 | 63.94 | 65.24 | 58.57 | 69.09 | 62.86 | |
| Novel | plain RAG, 12,000 | 64.48 | 65.41 | 58.91 | 70.61 | 62.98 | |
| Novel | graph hop 0, 2,000 | 62.42 | 63.73 | 57.89 | 66.10 | 61.96 | |
| Novel | graph hop 1, 2,000 | 63.16 | 62.82 | 57.16 | 67.01 | 65.63 | |
| Novel | graph hop 2, 2,000 | 62.50 | 62.36 | 57.40 | 65.94 | 64.31 | |
| Novel | plain RAG, 2,000 | 60.24 | 59.24 | 56.37 | 65.79 | 59.56 | |
| Medical | graph hop 1, 12,000 | 74.58 | | | | | 7th of 22, between AtlasGraphRAG 75.62 and G-reasoner 73.30 |
| Medical | plain RAG, 12,000 | 74.62 | | | | | |

Novel questions scored by type for hop 1 at 12,000: 970 of 971 FR, 609 of 610 CR, 362 of 362 CS, 67 of
67 CG.

- On both boards ThreadAtlas sits among the graph systems above the board's own RAG rows (Novel 48.35
  and 47.93, Medical 62.43 and 61.00). Our plain RAG, run with our reader prompt at 12,000 tokens,
  scores close to the graph (Novel 64.48, Medical 74.62); the board's RAG rows were scored by an earlier
  evaluator on an earlier question file, so the two are not like for like.

## The pattern across the four sets

| Set | Whole store | Own set, 2,000 | Own set, 12,000 |
|---|---|---|---|
| LongMemEval | graph +5.8 to +11.8; hybrid search alone no gain | graph +2.8 to +3.8; hybrid alone below plain | graph +1.6 to +3.8, one at p 0.045 |
| Novel | graph +1.6 at 2,000, tie at 12,000 for hops 0 and 1; hybrid alone no gain | graph and hybrid alone both about +2 | all tie; graph uses fewer tokens |
| Medical | not run | all tie | all tie; graph uses fewer tokens |

The graph's best setting never scores below plain RAG beyond its standard error. It gains most where the store is
large and mixed, and where the material is a person's conversations; on one book set or one medical
corpus it ties, usually with fewer tokens. Where hybrid search over chunks matches the graph (Novel own
set, 2,000 tokens), the gain is the search's; where it does not (LongMemEval and Novel over the whole
store), the gain is the graph's.
