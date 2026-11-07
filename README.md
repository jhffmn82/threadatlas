# ThreadAtlas

**[Open the wiki: https://jhffmn82.github.io/threadatlas/wiki/](https://jhffmn82.github.io/threadatlas/wiki/)**

ThreadAtlas turns a mixed pile of documents (books, papers, chat histories) into one knowledge graph in which every
fact carries the verbatim quote and the document it came from. On top of it sit a self-building wiki and a retrieval
path that answers questions from the graph.

IT 494 project, M.S. in Computer Science, Illinois State University. Advisor: Dr. Xing Fang.

## The wiki

**[https://jhffmn82.github.io/threadatlas/wiki/](https://jhffmn82.github.io/threadatlas/wiki/)**

Rendered from the graph by one deterministic pass: every entity, work and claim links to the verbatim quote it came
from, and every quote opens the source text where it was taken. The built site is in [`wiki/`](wiki/); nothing in it is
edited by hand. The texts are public-domain literature and CC BY papers, and each paper's page carries its licence line.

## Data and notebooks

Each stage is a Kaggle notebook; the copies in [`development_code/`](development_code/) are the versions that made the published
outputs.

| stage | notebook | output |
|---|---|---|
| Step 0, extraction: documents to text and units | [`threadatlas-extractor`](development_code/threadatlas-extractor.ipynb) ([Kaggle](https://www.kaggle.com/code/jhffmn/threadatlas-extractor)) | [Step 0 dataset](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0) |
| Step 1, reading: entities, facts with their quotes, cells, abstracts | [`threadatlas-document-ingestor`](development_code/threadatlas-document-ingestor.ipynb) ([Kaggle](https://www.kaggle.com/code/jhffmn/threadatlas-document-ingestor)) | [Step 1 dataset](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step1) |
| Global layer: one graph over every document, its parents, chunks and vectors | [`threadatlas-global-layer`](development_code/threadatlas-global-layer.ipynb) ([Kaggle](https://www.kaggle.com/code/jhffmn/threadatlas-global-layer)) | [store](https://www.kaggle.com/datasets/jhffmn/threadatlas-global-chunks) |
| GraphRAG-Bench Medical: the same pipeline over the Medical corpus | [`threadatlas-medical`](development_code/threadatlas-medical.ipynb) ([Kaggle](https://www.kaggle.com/code/jhffmn/threadatlas-medical)) | [store](https://www.kaggle.com/datasets/jhffmn/threadatlas-medical-chunks) |
| Retrieval, and the GraphRAG-Bench submission run | [`threadatlas-graphrag-submission`](development_code/threadatlas-graphrag-submission.ipynb) ([Kaggle](https://www.kaggle.com/code/jhffmn/threadatlas-graphrag-submission)) | [answers, evaluator output, board rows](https://www.kaggle.com/code/jhffmn/threadatlas-graphrag-submission/output) |

## Layout

| folder | what it holds |
|---|---|
| `development_code/` | the pipeline's Kaggle notebooks, from extraction to the GraphRAG-Bench submission |
| `wiki/` | the published wiki, built by the wiki notebook |
| `threadatlas_memory/` | ThreadAtlas as a memory for one user at a time: `add`, `search` and `delete` |
| `omnimemeval/` | ThreadAtlas's OmniMemEval runs on LoCoMo and LongMemEval: results, every record, the notebook |

## License

The code, the wiki's pages and every derived record are MIT ([LICENSE](LICENSE)). Quoted text keeps its source's
license: public domain for the books, MIT for LongMemEval and GraphRAG-Bench, CC BY for the papers (each paper's wiki
page carries its licence line), and CC BY-NC 4.0 for the LoCoMo text in `omnimemeval/`.
