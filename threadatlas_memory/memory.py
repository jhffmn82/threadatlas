"""add, search and delete: ThreadAtlas as one memory per user.

    add(messages, user_id, minute)
        the session is keyed by its turns and its minute
        a session the pipeline has already read is found by its key and copied in, rows and vectors;
        any other is read now (Step 0 makes it a document, Step 1 reads its facts) and embedded
        either way it goes straight into the user's store, after what is already there
    search(query, user_id, top_k)
        the packet: the header, then at most top_k - 1 bundles from the user's store
    delete(user_id)
        the user's folder removed

Each user is a folder under STATE_DIR holding their store, so ingestion and search can run in separate
processes, as OmniMemEval runs them.
"""

import hashlib
import json
import shutil
import threading

from . import chat, config, extract, retrieval, store
from .sessions import read_index, session_key, turn_text

LOCKS = {}                       # user folder -> the lock that keeps one change to that user at a time
LOCKS_GUARD = threading.Lock()
SEARCH_LOCK = threading.Lock()   # one search at a time: the embedder and the open stores are shared
OPEN = {}                        # user folder -> the store opened from it


def user_folder(user_id):
    return config.STATE_DIR / "users" / hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:32]


def user_lock(folder):
    with LOCKS_GUARD:
        if str(folder) not in LOCKS:
            LOCKS[str(folder)] = threading.Lock()
        return LOCKS[str(folder)]


def read_added(folder):
    """The sessions the user has added, and the histories that hold every one of them so far."""
    path = folder / "added.json"
    if not path.exists():
        return {"sessions": [], "histories": None}
    return json.loads(path.read_text(encoding="utf-8"))


def write_added(folder, added):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "added.json").write_text(json.dumps(added), encoding="utf-8")


def stored_document(found, histories):
    """The pipeline's document for a session already read: the copy in the user's own history when the sessions
    so far point to it, else the first history that has the session. Step 0 kept one copy of a session that two
    histories share word for word and to the minute, so any history that has it serves."""
    lib = store.library()["db"]
    ordered = []
    for history, name in sorted(found):
        if histories is not None and history in histories:
            ordered.insert(0, (history, name))
        else:
            ordered.append((history, name))
    for history, name in ordered:
        for file_name in (name, name.replace("answer_", "")):
            row = lib.execute("select doc_id from main_store.document where source_uri = ?",
                              ("chats/longmemeval/" + history + "/" + file_name + ".json",)).fetchone()
            if row is not None:
                return row[0]
    return None


def add(messages, user_id, minute):
    """One session of one user; `minute` is its date as 'YYYY-MM-DDTHH:MM'."""
    key = session_key(messages, minute)
    folder = user_folder(user_id)
    with user_lock(folder):
        added = read_added(folder)
        if key in added["sessions"]:
            return
        found = read_index().get(key)
        doc_id = None
        if found is not None:
            # the user's history is the one that holds every session they add
            holding = []
            for history, name in found:
                if added["histories"] is None or history in added["histories"]:
                    if history not in holding:
                        holding.append(history)
            if holding:
                added["histories"] = holding
            doc_id = stored_document(found, added["histories"])
        if doc_id is not None:
            store.append(folder / "store", doc_id=doc_id)
        else:
            store.append(folder / "store", session=read_fresh(messages, folder, minute, key))
        added["sessions"].append(key)
        write_added(folder, added)
    with SEARCH_LOCK:
        OPEN.pop(str(folder), None)


def read_fresh(messages, folder, minute, key):
    """A session the pipeline has not read: Step 0 makes it a document and Step 1 reads it."""
    turns = []
    for message in messages:
        turns.append({"role": message["role"], "content": turn_text(message.get("content", ""))})
    session_id = key.split("|")[0][:12]
    source_uri = "chats/memory/" + folder.name + "/" + session_id + ".json"
    document, units = chat.session_document(session_id, turns, minute, source_uri)
    nodes, facts, abstract = extract.read_document(document, units)
    return {"document": document, "units": units, "nodes": nodes, "facts": facts, "abstract": abstract}


def search_memory(query, user_id, top_k):
    """The packet for this question from this user's memory: its header and at most top_k - 1 bundles."""
    folder = user_folder(user_id)
    if not (folder / "store" / "store.sqlite").exists():
        return []
    with SEARCH_LOCK:
        if str(folder) not in OPEN:
            OPEN[str(folder)] = retrieval.open_store(folder / "store")
        context, used = retrieval.retrieve(OPEN[str(folder)], query, config.HOPS, config.HITS,
                                           config.BUDGET - retrieval.count_tokens(config.PACKET_HEADER), top_k - 1)
    return [config.PACKET_HEADER] + context


def delete(user_id):
    folder = user_folder(user_id)
    with user_lock(folder):
        with SEARCH_LOCK:
            OPEN.pop(str(folder), None)
        if folder.exists():
            shutil.rmtree(folder)
