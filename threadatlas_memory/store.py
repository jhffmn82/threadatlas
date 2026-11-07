"""One user's store: the tables retrieval reads, a keyword index, and a vector per row.

A user's store holds only that user's documents. It is built one of two ways:

    from the pipeline's store, for sessions it already read: the documents' rows and their vectors
        are copied out of threadatlas.sqlite and threadatlas.npy, with their text from Step 0
    from Step 1's rows, for sessions read fresh: the rows are loaded and their texts embedded

Either way the search rows and the vector texts are written the way the global layer writes them
(kaggle.com/code/jhffmn/threadatlas-global-layer, Blocks 5 to 7), so a question meets the same records.
Parents are left out: they are formed across many people's documents, and a user's memory holds
only their own.
"""

import json
import shutil
import sqlite3
import threading

import numpy as np

from . import config

SCHEMA = """
create table document (doc_id text primary key, title text, author text, occurred_at text, source_uri text);
create table document_text (doc_id text primary key, text text);
create table unit (unit_id text primary key, doc_id text, position integer, label text, kind text, occurred_at text,
    start integer, end integer);
create table node (doc_id text, node_id text, name text, kind text, primary key (doc_id, node_id));
create table fact (doc_id text, fact_id text, subject text, subject_name text, predicate text, object text,
    object_is_node integer, qualifiers text, unit_id text, quote text, quote_start integer, quote_end integer,
    occurred_at text, direction text, primary key (doc_id, fact_id));
create table cell (doc_id text, node_id text, unit_id text, text text);
create table abstract (doc_id text, node_id text, text text);
create table chunk (doc_id text, chunk_id text, start integer, end integer, primary key (doc_id, chunk_id));
create table fact_in_chunk (doc_id text, fact_id text, chunk_id text);
create table vec_row (row integer primary key, record text, doc_id text, record_id text);
create virtual table search using fts5(record unindexed, doc_id unindexed, record_id unindexed, text);
create index fact_subject on fact (doc_id, subject);
create index cell_node on cell (doc_id, node_id);
create index abstract_node on abstract (doc_id, node_id);
"""

COPIED = {
    "document": "doc_id, title, author, occurred_at, source_uri",
    "node": "doc_id, node_id, name, kind",
    "fact": "doc_id, fact_id, subject, subject_name, predicate, object, object_is_node, qualifiers, unit_id, "
            "quote, quote_start, quote_end, occurred_at, direction",
    "cell": "doc_id, node_id, unit_id, text",
    "abstract": "doc_id, node_id, text",
    "chunk": "doc_id, chunk_id, start, end",
    "fact_in_chunk": "doc_id, fact_id, chunk_id",
}

CHUNK_TOKENS = 256        # the benchmark's chunks, as the global layer cuts them (Block 16b)
CHUNK_OVERLAP = 32
ENCODER = None


# --- the lines that are searched and embedded, as the global layer writes them ----------------------

def sentences(text):
    """Cut text after . ! or ? where white space and a sentence opener follow."""
    openers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\"'(["
    text = (text or "").strip()
    pieces = []
    start = 0
    i = 1
    while i < len(text):
        if text[i - 1] in ".!?" and text[i].isspace():
            opener = i
            while opener < len(text) and text[opener].isspace():
                opener += 1
            if opener < len(text) and text[opener] in openers:
                pieces.append(text[start:i])
                start = opener
            i = opener
        i += 1
    pieces.append(text[start:])
    kept = []
    for piece in pieces:
        if piece.strip():
            kept.append(piece)
    return kept


def plain(text):
    """Text without the marks LongMemEval puts in session ids: answer_ on gold, _abs on an unanswerable history's."""
    text = text.replace("answer_", "")
    for end in ("_", " ", ":", ",", ".", ")", "\n"):       # only at the end of an id, so a book's _absolute_ stays
        text = text.replace("_abs" + end, end)
    return text


def is_identifier(title, source_uri):
    """A chat has no title of its own, and a file's own name is not a title either."""
    return title is None or source_uri.rsplit("/", 1)[-1].startswith(title + ".")


def fact_text(fact, names):
    subject = names.get(fact["subject"], fact["subject"])
    if fact["direction"] == "mentioned" and fact["subject_name"]:     # a chat minor's fact, carried by its session
        subject = fact["subject_name"]
    thing = fact["object"]
    if fact["object_is_node"]:
        thing = names.get(fact["object"], fact["object"])
    if fact["predicate"] == "belongs_to_history":                     # a history's folder is its question's id
        thing = thing.removesuffix("_abs")
    if fact["direction"] == "inverse":                                # stored under the major its object points at
        subject, thing = thing, subject
    line = subject + " " + fact["predicate"].replace("_", " ") + " " + thing
    if fact["qualifiers"]:
        line += " (" + fact["qualifiers"] + ")"
    return line


def record_lines(db, doc_id_wanted):
    """(record, doc_id, record_id, search text, [vector texts]) for every fact, chunk, cell and abstract of one
    document."""
    where = " where doc_id = ?"
    wanted = (doc_id_wanted,)
    documents = {}
    for doc_id, title, source_uri in db.execute("select doc_id, title, source_uri from document" + where, wanted):
        documents[doc_id] = (title, source_uri)
    names = {}
    for doc_id, node_id, name in db.execute("select doc_id, node_id, name from node" + where, wanted):
        names[(doc_id, node_id)] = name

    lines = []
    fields = ["doc_id", "fact_id", "subject", "subject_name", "predicate", "object", "object_is_node", "qualifiers",
              "occurred_at", "direction", "quote"]
    for row in db.execute("select " + ", ".join(fields) + " from fact" + where + " order by doc_id, fact_id", wanted):
        fact = dict(zip(fields, row))
        doc_id = fact["doc_id"]
        title, source_uri = documents[doc_id]
        local = {fact["subject"]: names.get((doc_id, fact["subject"]), fact["subject"]),
                 fact["object"]: names.get((doc_id, fact["object"]), fact["object"])}
        line = fact_text(fact, local)
        if fact["occurred_at"]:
            line += ", " + fact["occurred_at"]
        if not is_identifier(title, source_uri):
            line += ", " + title
        line = plain(line)
        searched = line
        if fact["quote"]:
            searched += "\n" + fact["quote"]
        lines.append(("fact", doc_id, fact["fact_id"], searched, [line]))

    # a chunk is searched and embedded as its text, without the marks
    texts = {}
    for doc_id, text in db.execute("select doc_id, text from document_text" + where, wanted):
        texts[doc_id] = text
    for doc_id, chunk_id, start, end in db.execute(
            "select doc_id, chunk_id, start, end from chunk" + where + " order by rowid", wanted):
        words = plain(texts[doc_id][start:end])
        lines.append(("chunk", doc_id, chunk_id, words, [words]))

    # a cell or abstract is searched as it stands and embedded a sentence at a time, its entity in front
    for table, key in (("cell", "node_id || '@' || unit_id"), ("abstract", "node_id")):
        for doc_id, node_id, record_id, text in db.execute(
                "select doc_id, node_id, " + key + ", text from " + table + where + " order by rowid", wanted):
            title, source_uri = documents[doc_id]
            entity = names.get((doc_id, node_id), node_id)
            if is_identifier(title, source_uri):
                front = plain(entity + ": ")
            else:
                front = entity + ", " + title + ": "
            embedded = []
            for sentence in sentences(text):
                embedded.append(front + sentence)
            lines.append((table, doc_id, record_id, text, embedded))
    return lines


def write_search(db, lines):
    rows = []
    for record, doc_id, record_id, searched, embedded in lines:
        rows.append((record, doc_id, record_id, searched))
    db.executemany("insert into search values (?,?,?,?)", rows)


# --- the library: what a copy reads, opened once -----------------------------------------------------

LIBRARY = {}
LIBRARY_LOCK = threading.Lock()
THREAD = threading.local()       # each thread's own connection: users are added in parallel threads


def library():
    """The pipeline's store, its vectors, and a small index beside the users of each chat's text, unit spans
    and vector rows, built once from Step 0 and the store. The vectors are shared; each thread reads the
    index through a connection of its own."""
    with LIBRARY_LOCK:
        if "vectors" not in LIBRARY:
            path = config.STATE_DIR / "library.sqlite"
            if not path.exists():
                build_library(path)
            LIBRARY["path"] = path
            LIBRARY["vectors"] = np.load(config.STORE_DIR / "threadatlas.npy", mmap_mode="r")
    if getattr(THREAD, "db", None) is None:
        THREAD.db = sqlite3.connect(LIBRARY["path"])
        THREAD.db.execute("attach database ? as main_store", (str(config.STORE_DIR / "threadatlas.sqlite"),))
    return {"db": THREAD.db, "vectors": LIBRARY["vectors"]}


def build_library(path):
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    building = path.with_suffix(".building")
    if building.exists():
        building.unlink()
    db = sqlite3.connect(building)
    db.executescript("""
        create table chat (doc_id text primary key);
        create table document_text (doc_id text primary key, text text);
        create table unit_span (unit_id text primary key, start integer, end integer);
        create table vec_row (row integer primary key, record text, doc_id text, record_id text);
    """)
    store = sqlite3.connect(config.STORE_DIR / "threadatlas.sqlite")
    chats = set()
    for (doc_id,) in store.execute("select doc_id from document where source_uri like 'chats/%'"):
        chats.add(doc_id)
    rows = []
    for doc_id in sorted(chats):
        rows.append((doc_id,))
    db.executemany("insert into chat values (?)", rows)

    rows = []
    with open(config.STEP0_DIR / "documents.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["doc_id"] in chats:
                rows.append((row["doc_id"], row["text"]))
    db.executemany("insert into document_text values (?,?)", rows)

    rows = []
    with open(config.STEP0_DIR / "units.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["doc_id"] in chats:
                rows.append((row["unit_id"], row["start"], row["end"]))
    db.executemany("insert into unit_span values (?,?,?)", rows)

    db.executemany("insert into vec_row values (?,?,?,?)",
                   store.execute("select row, record, doc_id, record_id from vec_row where record != 'parent'"))
    db.execute("create index vec_row_doc on vec_row (doc_id)")
    db.commit()
    db.close()
    store.close()
    building.rename(path)


# --- building a user's store -------------------------------------------------------------------------

def open_store_file(folder):
    """The user's store, made empty the first time."""
    if not (folder / "store.sqlite").exists():
        folder.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(folder / "store.sqlite")
        db.executescript(SCHEMA)
        np.save(folder / "vectors.npy", np.zeros((0, config.DIMENSION), dtype=np.float16))
        return db
    return sqlite3.connect(folder / "store.sqlite")


def copy_documents(db, doc_ids):
    """These documents' rows copied out of the pipeline's store, and their vectors, in the store's row order."""
    lib = library()
    source = lib["db"]
    wanted = sorted(doc_ids)
    marks = ", ".join(["?"] * len(wanted))
    for table in COPIED:
        if source.execute("select count(*) from main_store.sqlite_master where name = ?", (table,)).fetchone()[0] == 0:
            continue                          # a store built before chunks has no chunk tables
        columns = COPIED[table]
        places = ", ".join(["?"] * len(columns.split(",")))
        rows = source.execute("select " + columns + " from main_store." + table + " where doc_id in (" + marks + ")",
                              wanted)
        db.executemany("insert into " + table + " (" + columns + ") values (" + places + ")", rows)
    db.executemany("insert into document_text values (?,?)",
                   source.execute("select doc_id, text from document_text where doc_id in (" + marks + ")", wanted))
    db.executemany("insert into unit values (?,?,?,?,?,?,?,?)", source.execute(
        "select u.unit_id, u.doc_id, u.position, u.label, u.kind, u.occurred_at, s.start, s.end "
        "from main_store.unit u join unit_span s on s.unit_id = u.unit_id where u.doc_id in (" + marks + ")", wanted))

    rows = source.execute("select row, record, doc_id, record_id from vec_row where doc_id in (" + marks + ") "
                          "order by row", wanted).fetchall()
    places = []
    records = []
    for row in rows:
        places.append(row[0])
        records.append((row[1], row[2], row[3]))
    return records, np.asarray(lib["vectors"][places], dtype=np.float32)


def load_session(db, session):
    """One session read fresh: its document, text, turns, nodes, facts and abstract. A chat keeps no title,
    as in the pipeline's store: its id is only a file name."""
    doc = session["document"]
    db.execute("insert into document values (?,?,?,?,?)",
               (doc["doc_id"], None, doc["author"], doc["occurred_at"], doc["source_uri"]))
    db.execute("insert into document_text values (?,?)", (doc["doc_id"], doc["text"]))
    for unit in session["units"]:
        db.execute("insert into unit values (?,?,?,?,?,?,?,?)",
                   (unit["unit_id"], unit["doc_id"], unit["position"], unit["label"], unit["kind"], unit["occurred_at"],
                    unit["start"], unit["end"]))
    for node in session["nodes"]:
        db.execute("insert into node values (?,?,?,?)", (doc["doc_id"], node["node_id"], node["name"], node["kind"]))
    for fact in session["facts"]:
        db.execute("insert into fact values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (fact["doc_id"], fact["fact_id"], fact["subject"], fact["subject_name"], fact["predicate"],
                    fact["object"], fact["object_is_node"], fact["qualifiers"], fact["unit_id"], fact["quote"],
                    fact["quote_start"], fact["quote_end"], fact["occurred_at"], fact["direction"]))
    if session["abstract"]:
        db.execute("insert into abstract values (?,?,?)",
                   (doc["doc_id"], session["abstract"]["node_id"], session["abstract"]["text"]))
    add_chunks(db, doc["doc_id"], doc["text"], session["facts"])


def chunk_spans(text):
    """(start, end) character offsets of each 256-token chunk of the text, each starting 32 tokens back."""
    global ENCODER
    if ENCODER is None:
        import tiktoken
        ENCODER = tiktoken.get_encoding("o200k_base")
    tokens = ENCODER.encode(text, disallowed_special=())
    if not tokens:
        return []
    decoded, offsets = ENCODER.decode_with_offsets(tokens)
    spans = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_TOKENS, len(tokens))
        if decoded == text:
            first = offsets[start]
            last = len(text)
            if end < len(tokens):
                last = offsets[end]
        else:                                 # a token split inside a character: measure by decoding
            first = len(ENCODER.decode(tokens[:start]))
            last = len(ENCODER.decode(tokens[:end]))
        if text[first:last].strip():
            spans.append((first, last))
        if end == len(tokens):
            break
        start += CHUNK_TOKENS - CHUNK_OVERLAP
    return spans


def add_chunks(db, doc_id, text, facts):
    """A session's chunks, and the facts whose whole quote each one holds."""
    number = 0
    for start, end in chunk_spans(text):
        number += 1
        db.execute("insert into chunk values (?,?,?,?)", (doc_id, str(number), start, end))
        for fact in facts:
            if fact["quote"] is not None and start <= fact["quote_start"] and fact["quote_end"] <= end:
                db.execute("insert into fact_in_chunk values (?,?,?)", (doc_id, fact["fact_id"], str(number)))


def append(folder, doc_id=None, session=None):
    """One session into the user's store as it is added: a document the pipeline already read is copied with its
    vectors, a session read fresh is loaded and embedded. Its rows, keyword rows and vectors go after the ones
    already there, so a search only opens the store."""
    from .retrieval import embed

    db = open_store_file(folder)
    records = []
    vectors = np.zeros((0, config.DIMENSION), dtype=np.float32)
    if doc_id is not None:
        records, vectors = copy_documents(db, {doc_id})
    else:
        load_session(db, session)
        doc_id = session["document"]["doc_id"]
    lines = record_lines(db, doc_id)
    if session is not None:
        texts = []
        for record, line_doc, record_id, searched, embedded in lines:
            for text in embedded:
                records.append((record, line_doc, record_id))
                texts.append(text)
        if texts:
            vectors = embed(texts)
    write_search(db, lines)

    first = db.execute("select count(*) from vec_row").fetchone()[0]
    numbered = []
    for i in range(len(records)):
        numbered.append((first + i, records[i][0], records[i][1], records[i][2]))
    db.executemany("insert into vec_row values (?,?,?,?)", numbered)
    old = np.load(folder / "vectors.npy")
    np.save(folder / "vectors.npy", np.vstack([old, vectors.astype(np.float16)]))
    db.commit()
    db.close()
