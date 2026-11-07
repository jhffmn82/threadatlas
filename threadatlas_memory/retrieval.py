"""Retrieval over one user's store: the packet a reader is given for a question.

This is the retrieval notebook's path (kaggle.com/code/jhffmn/threadatlas-retrieval, 0.21, Blocks 3 to 7) for a
store that holds one user's documents and no parents. A record is a fact, a cell, an abstract, or a
chunk of the document's own text:

    1. score the question against every vector; a record scores as its best row
    2. take the HITS best records by vector and the HITS best by keyword (FTS5 bm25)
    3. fuse the two lists by reciprocal rank
    4. walk HOPS steps through the graph from the best-placed records; what the walk reaches is a
       third ranked list, valued by similarity times DISCOUNT per hop, fused the same way
    5. group the pool into bundles: a cell with its facts, an abstract alone, and loose facts by the
       passage of the source they were read from
    6. pack the best bundles, whole, until the item count or the token budget is reached
"""

import sqlite3

import numpy as np

from . import config
from .store import plain       # a passage is shown without LongMemEval's marks, as every other text is

K_ENTRY = 80          # hits each search returns; the setting takes its first HITS
K_HOP = 10            # records a hop takes along each edge, the most similar first
FRONTIER = 20         # records a hop walks on from
DISCOUNT = 0.8        # a walked record's similarity is multiplied by this for each hop
RRF_K = 60            # the reciprocal rank fusion constant
MAX_PASSAGE = 500     # characters of source text shown with one fact, centred on its quote

EMBEDDER = None
TOKENIZER = None


def embed(texts):
    global EMBEDDER
    if EMBEDDER is None:
        from fastembed import TextEmbedding
        EMBEDDER = TextEmbedding(config.EMBED_MODEL)
    return np.asarray(list(EMBEDDER.embed(texts, batch_size=256)), dtype=np.float32)


def count_tokens(text):
    global TOKENIZER
    if TOKENIZER is None:
        import tiktoken
        TOKENIZER = tiktoken.get_encoding("o200k_base")
    return len(TOKENIZER.encode(text, disallowed_special=()))     # a chat can hold the words <|endoftext|>


# --- the store, read once --------------------------------------------------------------------------

def open_store(folder):
    """Everything a question reads, held in memory, with the connection kept for the text lookups."""
    db = sqlite3.connect(folder / "store.sqlite", check_same_thread=False)
    store = {"db": db, "vectors": np.load(folder / "vectors.npy").astype(np.float32)}

    store["record_of_row"] = []
    store["rows_of_record"] = {}
    for row, kind, doc_id, record_id in db.execute("select row, record, doc_id, record_id from vec_row order by row"):
        record = (kind, doc_id, record_id)
        store["record_of_row"].append(record)
        store["rows_of_record"].setdefault(record, []).append(row)

    store["documents"] = {}
    for doc_id, title, source_uri, occurred_at in db.execute("select doc_id, title, source_uri, occurred_at from document"):
        store["documents"][doc_id] = {"title": title, "source_uri": source_uri, "occurred_at": occurred_at}

    store["names"] = {}
    store["document_node"] = {}
    for doc_id, node_id, name, kind in db.execute("select doc_id, node_id, name, kind from node"):
        store["names"][(doc_id, node_id)] = name
        if kind == "document":
            store["document_node"][doc_id] = node_id

    store["units"] = {}
    for unit_id, position, label, kind, occurred_at, start, end in db.execute(
            "select unit_id, position, label, kind, occurred_at, start, end from unit"):
        store["units"][unit_id] = {"position": position, "label": label, "kind": kind, "occurred_at": occurred_at,
                                   "start": start, "end": end}

    store["texts"] = {}
    for doc_id, text in db.execute("select doc_id, text from document_text"):
        store["texts"][doc_id] = text

    # a chunk's offsets, and the facts each chunk holds: the walk's edges between them
    store["chunks"] = {}
    store["facts_in_chunk"] = {}
    store["chunks_of_fact"] = {}
    for doc_id, chunk_id, start, end in db.execute("select doc_id, chunk_id, start, end from chunk"):
        store["chunks"][("chunk", doc_id, chunk_id)] = (start, end)
    for doc_id, fact_id, chunk_id in db.execute("select doc_id, fact_id, chunk_id from fact_in_chunk"):
        store["facts_in_chunk"].setdefault(("chunk", doc_id, chunk_id), []).append(("fact", doc_id, fact_id))
        store["chunks_of_fact"].setdefault(("fact", doc_id, fact_id), []).append(("chunk", doc_id, chunk_id))

    store["graph"] = read_graph(db, store["units"])
    return store


def read_graph(db, units):
    """What a walk steps along: each entity's facts and cells, each fact's entity and unit, the abstracts."""
    graph = {"fact_of": {}, "facts_of_node": {}, "facts_of_doc": {}, "facts_of_cell": {}, "cells_of_node": {},
             "abstracts": set()}
    for doc_id, fact_id, subject, unit_id in db.execute("select doc_id, fact_id, subject, unit_id from fact"):
        graph["fact_of"][(doc_id, fact_id)] = (subject, unit_id)
        graph["facts_of_node"].setdefault((doc_id, subject), []).append(fact_id)
        graph["facts_of_doc"].setdefault(doc_id, []).append(fact_id)
        graph["facts_of_cell"].setdefault((doc_id, subject, unit_id), []).append(fact_id)

    # an entity's cells in the order its units come in the document
    placed = {}
    for doc_id, node_id, unit_id in db.execute("select doc_id, node_id, unit_id from cell"):
        position = 0
        if unit_id in units:
            position = units[unit_id]["position"]
        placed.setdefault((doc_id, node_id), []).append((position, unit_id))
    for key in placed:
        placed[key].sort()
        graph["cells_of_node"][key] = []
        for position, unit_id in placed[key]:
            graph["cells_of_node"][key].append(unit_id)

    for doc_id, node_id in db.execute("select doc_id, node_id from abstract"):
        graph["abstracts"].add((doc_id, node_id))
    return graph


# --- steps 1 to 3: the two searches and their fusion -------------------------------------------------

def best_first(records, score_of):
    """Highest score first; ties go by the record's name, so the order never depends on the run."""
    ranked = []
    for record in records:
        name = []
        for part in record:
            name.append(str(part))
        ranked.append((-score_of[record], tuple(name), record))
    ranked.sort()
    ordered = []
    for item in ranked:
        ordered.append(item[2])
    return ordered


def record_score(store, row_scores, record):
    """A record scores as its best row: a cell or abstract has a row per sentence."""
    rows = store["rows_of_record"].get(record)
    if not rows:
        return 0.0
    return float(row_scores[rows].max())


def vector_entries(store, row_scores):
    best = {}
    for row in np.argsort(-row_scores, kind="stable"):
        score = float(row_scores[row])
        if len(best) >= K_ENTRY and score < min(best.values()):
            break
        record = store["record_of_row"][row]
        if record not in best:
            best[record] = score
    return best_first(best, best)[:K_ENTRY]


def question_words(question):
    """The question's words, as FTS5 reads a word: runs of letters and digits."""
    words = []
    word = ""
    for ch in question:
        if ch.isalnum() or ch == "_":
            word += ch
        elif word:
            words.append(word)
            word = ""
    if word:
        words.append(word)
    return words


def keyword_entries(store, question):
    words = question_words(question)
    if len(words) == 0:
        return []
    quoted = []
    for word in words:
        quoted.append('"' + word + '"')
    sql = ("select record, doc_id, record_id from search where search match ? "
           "order by bm25(search), record, doc_id, record_id limit ?")
    found = []
    for row in store["db"].execute(sql, (" OR ".join(quoted), K_ENTRY)):
        found.append(tuple(row))
    return found


def fuse(vector_ranked, keyword_ranked):
    rrf = {}
    for ranked in (vector_ranked, keyword_ranked):
        rank = 1
        for record in ranked:
            rrf[record] = rrf.get(record, 0.0) + 1 / (RRF_K + rank)
            rank += 1
    return best_first(rrf, rrf), rrf


def ranked_score(rrf_value, similarity):
    """A record's place in the pool: its fused rank, with its own similarity deciding only exact ties."""
    return rrf_value + 1e-12 * similarity


# --- step 4: the walk ---------------------------------------------------------------------------------

def abstract_above(store, doc_id, node_id):
    abstracts = store["graph"]["abstracts"]
    if (doc_id, node_id) in abstracts:
        return [("abstract", doc_id, node_id)]
    # an entity with no abstract of its own (a chat's) goes to its document's abstract
    document = store["document_node"].get(doc_id)
    if document and (doc_id, document) in abstracts:
        return [("abstract", doc_id, document)]
    return []


def facts_of(store, doc_id, node_id):
    """An entity's facts; a document's own node has every fact of its document."""
    graph = store["graph"]
    fact_ids = graph["facts_of_node"].get((doc_id, node_id), [])
    if node_id == store["document_node"].get(doc_id):
        fact_ids = graph["facts_of_doc"].get(doc_id, [])
    facts = []
    for fact_id in fact_ids:
        facts.append(("fact", doc_id, fact_id))
    return facts


def edges_of(store, record):
    """The records one step from this one, by edge."""
    graph = store["graph"]
    kind, doc_id, record_id = record
    if kind == "chunk":                       # a chunk leads to the facts read from its text
        return {"facts": list(store["facts_in_chunk"].get(record, []))}
    edges = {}
    if kind == "fact":
        node_id, unit_id = graph["fact_of"][(doc_id, record_id)]
        edges["cell"] = []
        if unit_id in graph["cells_of_node"].get((doc_id, node_id), []):
            edges["cell"] = [("cell", doc_id, node_id + "@" + unit_id)]
        edges["abstract"] = abstract_above(store, doc_id, node_id)
        edges["chunk"] = list(store["chunks_of_fact"].get(record, []))
    elif kind == "cell":
        node_id, unit_id = record_id.split("@")
        units = graph["cells_of_node"].get((doc_id, node_id), [])
        here = units.index(unit_id)
        edges["abstract"] = abstract_above(store, doc_id, node_id)
        edges["previous"] = []
        if here > 0:
            edges["previous"] = [("cell", doc_id, node_id + "@" + units[here - 1])]
        edges["next"] = []
        if here + 1 < len(units):
            edges["next"] = [("cell", doc_id, node_id + "@" + units[here + 1])]
        edges["facts"] = []
        for fact_id in graph["facts_of_cell"].get((doc_id, node_id, unit_id), []):
            edges["facts"].append(("fact", doc_id, fact_id))
    else:
        node_id = record_id
        edges["cells"] = []
        for unit_id in graph["cells_of_node"].get((doc_id, node_id), []):
            edges["cells"].append(("cell", doc_id, node_id + "@" + unit_id))
        edges["facts"] = facts_of(store, doc_id, node_id)
    return edges


def pool_scores(pool):
    scores = {}
    for record in pool:
        scores[record] = pool[record]["score"]
    return scores


def walk(store, row_scores, pool, hops):
    frontier = best_first(pool, pool_scores(pool))[:FRONTIER]
    walked = {}
    values = {}
    for hop in range(1, hops + 1):
        reached = {}
        for record in frontier:
            edges = edges_of(store, record)
            for edge in edges:
                candidates = set(edges[edge])
                candidates.discard(record)
                scores = {}
                for candidate in candidates:
                    scores[candidate] = record_score(store, row_scores, candidate)
                for candidate in best_first(candidates, scores)[:K_HOP]:
                    if candidate in pool:
                        continue
                    value = scores[candidate] * DISCOUNT ** hop
                    if candidate in values and values[candidate] >= value:
                        continue
                    walked[candidate] = scores[candidate]
                    values[candidate] = value
                    reached[candidate] = value
        frontier = best_first(reached, reached)[:FRONTIER]

    # what the walk reached is a third ranked list, placed by rank like the two searches
    rank = 1
    for record in best_first(walked, values):
        pool[record] = {"score": ranked_score(1 / (RRF_K + rank), walked[record])}
        rank += 1


# --- step 5: bundles ------------------------------------------------------------------------------

def read_fact(store, doc_id, fact_id):
    fields = ["subject", "subject_name", "predicate", "object", "object_is_node",
              "qualifiers", "occurred_at", "direction", "quote", "quote_start", "quote_end", "unit_id"]
    values = store["db"].execute("select " + ", ".join(fields) + " from fact where doc_id = ? and fact_id = ?",
                                 (doc_id, fact_id)).fetchone()
    fact = {}
    for i in range(len(fields)):
        fact[fields[i]] = values[i]
    return fact


def fact_line(store, doc_id, fact):
    names = store["names"]
    subject = names.get((doc_id, fact["subject"]), fact["subject"])
    if fact["direction"] == "mentioned" and fact["subject_name"]:
        subject = fact["subject_name"]
    thing = fact["object"]
    if fact["object_is_node"]:
        thing = names.get((doc_id, fact["object"]), fact["object"])
    if fact["direction"] == "inverse":            # stored under the major its object points at
        subject, thing = thing, subject
    line = subject + " " + fact["predicate"].replace("_", " ") + " " + thing
    if fact["qualifiers"]:
        line += " (" + fact["qualifiers"] + ")"
    return line


def whole_words(text, start, end):
    """A cut moved inward to the nearest space at each end, so no word is split."""
    while start < end and start > 0 and not text[start - 1].isspace() and not text[start].isspace():
        start += 1
    while end > start and end < len(text) and not text[end].isspace() and not text[end - 1].isspace():
        end -= 1
    return start, end


def source_passage(store, doc_id, unit_id, quote_start, quote_end):
    """The passage a fact was read from: a chat turn whole, otherwise the paragraph, cut to MAX_PASSAGE."""
    text = store["texts"][doc_id]
    unit = store["units"][unit_id]
    start = unit["start"]
    end = unit["end"]
    turn = unit["kind"] == "user" or unit["kind"] == "assistant"
    if not turn:
        for blank_line in ("\n\n", "\r\n\r\n"):
            found = text.rfind(blank_line, unit["start"], quote_start)
            if found != -1 and found > start:
                start = found
            found = text.find(blank_line, quote_end, unit["end"])
            if found != -1 and found < end:
                end = found
    if end - start > MAX_PASSAGE and not turn:
        start = max(unit["start"], quote_start - MAX_PASSAGE // 2)
        end = min(unit["end"], quote_end + MAX_PASSAGE // 2)
        start, end = whole_words(text, start, end)
    return start, end, plain(text[start:end].strip())


def passage_of(store, doc_id, fact):
    if not fact["quote"]:
        return None, None
    start, end, words = source_passage(store, doc_id, fact["unit_id"], fact["quote_start"], fact["quote_end"])
    return (doc_id, start, end), words


def make_bundles(store, pool):
    """A cell with the pool's facts of its entity in its unit; an abstract alone; other facts by passage."""
    cell_of = {}
    for record in pool:
        if record[0] == "cell":
            node_id, unit_id = record[2].split("@")
            cell_of[(record[1], node_id, unit_id)] = record

    bundles = {}
    for record in pool:
        if record[0] != "fact":
            bundles[record] = []

    groups = {}
    for record in pool:
        if record[0] != "fact":
            continue
        fact = read_fact(store, record[1], record[2])
        place = (fact["quote_start"] or 0, record[2], record)
        cell = cell_of.get((record[1], fact["subject"], fact["unit_id"]))
        if cell is not None:
            bundles[cell].append(place)
            continue
        passage, words = passage_of(store, record[1], fact)
        if passage is None:
            passage = record
        groups.setdefault(passage, []).append(place)

    # a group of loose facts is headed by its best-scoring fact
    for passage in groups:
        scores = {}
        for place in groups[passage]:
            scores[place[2]] = pool[place[2]]["score"]
        head = best_first(scores, scores)[0]
        bundles[head] = groups[passage]

    for head in bundles:
        bundles[head].sort()
        facts = []
        for place in bundles[head]:
            facts.append(place[2])
        bundles[head] = facts
    return bundles


# --- step 6: what the reader sees -----------------------------------------------------------------

def fresh_words(store, passage, tags, new):
    """A passage's text not shown yet, and the number of the passage that covers it when none is left."""
    doc_id, start, end = passage
    shown = []
    for key in tags:
        if key[0] == doc_id:
            shown.append((key[1], key[2], tags[key]))
    place = len(tags)
    for key in new:
        place += 1
        if key[0] == doc_id:
            shown.append((key[1], key[2], place))
    for first, last, number in shown:
        if first <= start and end <= last:
            return "", number
        if first <= start < last:
            start = last
        if first < end <= last:
            end = first
    start, end = whole_words(store["texts"][doc_id], start, end)
    if end <= start:                     # covered from both sides by passages already shown
        return "", shown[0][2]
    return plain(store["texts"][doc_id][start:end].strip()), None


def fact_lines(store, doc_id, facts, tags, indent):
    """A bundle's facts: a fact with no quote by its line, the others by the passages they came from."""
    by_passage = {}
    order = []
    texts = {}
    for record in facts:
        fact = read_fact(store, doc_id, record[2])
        passage, words = passage_of(store, doc_id, fact)
        if passage is None:
            passage = record
        else:
            texts[passage] = words
        if passage not in by_passage:
            by_passage[passage] = []
            order.append(passage)
        by_passage[passage].append(fact_line(store, doc_id, fact))

    block = ""
    for passage in order:
        if passage not in texts:
            for line in by_passage[passage]:
                block += "\n" + indent + "- " + line

    # passages in source order, each run of overlapping ones joined into one span
    spans = []
    for passage in order:
        if passage not in texts:
            continue
        if len(spans) > 0 and spans[-1][0] == passage[0] and passage[1] <= spans[-1][2]:
            spans[-1] = (passage[0], spans[-1][1], max(spans[-1][2], passage[2]))
        else:
            spans.append(passage)

    # a passage already shown is pointed to by its number, not repeated
    new = []
    for passage in spans:
        if passage in tags:
            block += "\n" + indent + "  source: see [P" + str(tags[passage]) + "] above"
            continue
        words, covered = fresh_words(store, passage, tags, new)
        if covered is not None:
            block += "\n" + indent + "  source: see [P" + str(covered) + "] above"
        else:
            new.append(passage)
            block += "\n" + indent + "  source [P" + str(len(tags) + len(new)) + ']: "' + words + '"'
    return block, new


def document_title(store, doc_id):
    """A document whose title is missing or is its file name, as a chat's is, goes by its id's first 8 characters."""
    document = store["documents"][doc_id]
    title = document["title"]
    stem = document["source_uri"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if title is None or title == stem:
        return doc_id[:8]
    return title


def header(date, title, label, previous):
    """A bundle's date, document and unit, leaving out each one the bundle before it already showed."""
    pieces = []
    if previous is None or previous[0] != date:
        pieces.append(str(date))
    if previous is None or previous[1] != title:
        pieces.append(str(title))
    if previous is None or previous[2] != label:
        pieces.append(str(label))
    if len(pieces) == 0:
        return ""
    return " | ".join(pieces) + " | "


def unit_label_and_date(store, unit_id):
    unit = store["units"].get(unit_id)
    if unit is None:
        return None, None
    return unit["label"], unit["occurred_at"]


def render(store, head, facts, tags, previous):
    """A bundle's text, its new passages, and its date, document and unit for the next bundle's header."""
    db = store["db"]
    kind, doc_id, record_id = head
    title = document_title(store, doc_id)
    document_date = store["documents"][doc_id]["occurred_at"]

    if kind == "abstract":
        text = db.execute("select text from abstract where doc_id = ? and node_id = ?", (doc_id, record_id)).fetchone()[0]
        entity = store["names"].get((doc_id, record_id), record_id)
        shown = (document_date, title, "abstract")
        return header(shown[0], shown[1], shown[2], previous) + entity + ": " + text, [], shown

    if kind == "fact":
        fact = read_fact(store, doc_id, record_id)
        label, unit_date = unit_label_and_date(store, fact["unit_id"])
        shown = (fact["occurred_at"] or unit_date or document_date, title, label or "record")
        lines, new = fact_lines(store, doc_id, facts, tags, "  ")
        return header(shown[0], shown[1], shown[2], previous).removesuffix(" | ") + lines, new, shown

    if kind == "chunk":
        # a numbered source, so a fact read from inside it points to it, and only its unshown part is printed
        start, end = store["chunks"][head]
        passage = (doc_id, start, end)
        shown = (document_date, title, "chunk " + record_id)
        top = header(shown[0], shown[1], shown[2], previous).removesuffix(" | ")
        if passage in tags:
            return top + "\n  source: see [P" + str(tags[passage]) + "] above", [], shown
        words, covered = fresh_words(store, passage, tags, [])
        if covered is not None:
            return top + "\n  source: see [P" + str(covered) + "] above", [], shown
        return top + "\n  source [P" + str(len(tags) + 1) + ']: "' + words + '"', [passage], shown

    node_id, unit_id = record_id.split("@")
    text = db.execute("select text from cell where doc_id = ? and node_id = ? and unit_id = ?",
                      (doc_id, node_id, unit_id)).fetchone()[0]
    label, unit_date = unit_label_and_date(store, unit_id)
    entity = store["names"].get((doc_id, node_id), node_id)
    shown = (unit_date or document_date, title, label or unit_id[:8])
    lines, new = fact_lines(store, doc_id, facts, tags, "  ")
    return header(shown[0], shown[1], shown[2], previous) + entity + ": " + text + lines, new, shown


def pack(store, pool, budget, items):
    """The best bundles, whole, until `items` bundles or `budget` tokens."""
    bundles = make_bundles(store, pool)
    scores = {}
    for head in bundles:
        scores[head] = pool[head]["score"]
        for record in bundles[head]:
            if pool[record]["score"] > scores[head]:
                scores[head] = pool[record]["score"]

    context = []
    used = 0
    tags = {}
    previous = None
    for head in best_first(bundles, scores):
        if items is not None and len(context) >= items:
            break
        text, new, shown = render(store, head, bundles[head], tags, previous)
        size = count_tokens(text)
        if used + size > budget:
            continue
        context.append(text)
        used += size
        previous = shown
        for passage in new:
            tags[passage] = len(tags) + 1
    return context, used


# --- the whole path -------------------------------------------------------------------------------

def retrieve(store, question, hops, hits, budget, items):
    """The bundles for a question, best first, and the tokens they take."""
    row_scores = store["vectors"] @ embed([question])[0]
    vector_ranked = vector_entries(store, row_scores)[:hits]
    keyword_ranked = keyword_entries(store, question)[:hits]
    entries, rrf = fuse(vector_ranked, keyword_ranked)

    pool = {}
    for entry in entries:
        pool[entry] = {"score": ranked_score(rrf[entry], record_score(store, row_scores, entry))}
    if hops > 0:
        walk(store, row_scores, pool, hops)
    return pack(store, pool, budget, items)
