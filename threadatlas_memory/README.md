# threadatlas_memory

ThreadAtlas as a memory with three calls, the shape memory benchmarks use:

```python
import threadatlas_memory as memory

memory.add(turns, user_id, minute)       # one chat session; turns are {"role", "content"}, minute 'YYYY-MM-DDTHH:MM'
memory.search(question, user_id, 20)     # the packet: a header, then up to 19 records with their sources
memory.delete(user_id)
```

## What happens

`add` reads a session the way the pipeline does. Step 0 turns it into a document of dated turns.
Step 1 reads its facts, each tied to the words of the turn it came from, checks every fact against
that passage, and corrects or drops the ones the passage does not state. A session the pipeline has
already read, word for word and at the same minute, is not read again: its rows and vectors are
taken from the pipeline's store. Either way the session goes straight into the user's own store,
after the sessions already there, with its facts, its 256-token chunks of text, its keyword rows and
its vectors.

`search` opens the user's store, which holds that user's sessions alone, and runs retrieval: vector
and keyword search over facts, cells, abstracts and chunks, fused by rank, two hops through the
graph, and the best records packed whole with the passages they were read from.

## The files

| File | What it does |
|---|---|
| `config.py` | paths, models, the retrieval setting, the packet's header |
| `sessions.py` | a session's key, and the sessions the pipeline has already read |
| `chat.py` | Step 0 for a chat session |
| `prompts.py` | Step 1's prompts for a chat, word for word the ingestor's |
| `llm.py` | calls to the reading model |
| `extract.py` | Step 1 for a chat session |
| `store.py` | one user's store: tables, keyword index, vectors |
| `retrieval.py` | retrieval over a user's store |
| `memory.py` | `add`, `search`, `delete` |

Each file names the notebook block it follows. The notebooks on Kaggle are the pipeline as it ran:
[extractor](https://www.kaggle.com/code/jhffmn/threadatlas-extractor) (Step 0),
[ingestor](https://www.kaggle.com/code/jhffmn/threadatlas-document-ingestor) (Step 1),
[global layer](https://www.kaggle.com/code/jhffmn/threadatlas-global-layer) and
[retrieval](https://www.kaggle.com/code/jhffmn/threadatlas-retrieval). This package is the same steps for
one user at a time.

## Setting it up

Set these, or put the files under `data/` beside the package:

| Variable | What |
|---|---|
| `THREADATLAS_STORE_DIR` | the global layer's output: `threadatlas.sqlite`, `threadatlas.npy` |
| `THREADATLAS_STEP0_DIR` | Step 0's export: `documents.jsonl`, `units.jsonl` |
| `THREADATLAS_SOURCE` | `longmemeval_s.json`, the file the store's chats were read from |
| `THREADATLAS_STATE_DIR` | where each user's folder goes |
| `THREADATLAS_READ_MODEL` | the model that reads a session the store has not read: `gpt-5.6-luna` (the default, the pipeline's) or `gpt-4.1-mini-2025-04-14` |
| `OPENAI_API_KEY` | for sessions the store has not read |

Needs `numpy`, `fastembed` and `tiktoken`.
