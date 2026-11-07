"""A session's key, and the sessions the store has already read.

A session is known by its turns, role and text with the empty turns left out, and the minute it is
dated. The benchmark file the store was read from lists every history's sessions; each is keyed the
same way and pointed at its history and the file name Step 0 gave it, so a session that arrives
through add() is matched to the documents it was read into.
"""

import hashlib
import json
import threading

from . import config


def turn_text(content):
    """A turn's text as a memory receives it: the dropped tokens taken out."""
    text = str(content)
    for token in config.DROPPED:
        text = text.replace(token, "")
    return text


def session_key(turns, minute):
    """The session's turns and its minute, as one string."""
    kept = []
    for turn in turns:
        text = turn_text(turn.get("content", ""))
        if text.strip() == "":
            continue
        kept.append([turn["role"], text])
    digest = hashlib.sha256(json.dumps(kept, ensure_ascii=False).encode("utf-8")).hexdigest()
    return digest + "|" + minute


def lme_minute(stamp):
    """'2023/05/20 (Sat) 02:38' -> '2023-05-20T02:38', the minute Step 0 dates a session by."""
    parts = stamp.split(" ")
    return parts[0].replace("/", "-") + "T" + parts[2]


def plain_name(name):
    """A session's file name without the benchmark's 'answer_' mark, which the store does not keep."""
    if name.startswith("answer_"):
        return name[len("answer_"):]
    return name


INDEX = {}
INDEX_LOCK = threading.Lock()


def read_index():
    """key -> [[history, file name], ...]: built once from the source file, then kept beside the users."""
    with INDEX_LOCK:
        if "keys" in INDEX:
            return INDEX["keys"]
        cached = config.STATE_DIR / "session-index.json"
        if cached.exists():
            INDEX["keys"] = json.loads(cached.read_text(encoding="utf-8"))
            return INDEX["keys"]
        keys = {}
        for row in json.loads(config.SOURCE_FILE.read_text(encoding="utf-8")):
            listed = {}                # a history that lists one session twice names the second <id>.2, as Step 0 does
            for session_id, stamp, turns in zip(row["haystack_session_ids"], row["haystack_dates"],
                                                row["haystack_sessions"]):
                listed[session_id] = listed.get(session_id, 0) + 1
                name = session_id
                if listed[session_id] > 1:
                    name = session_id + "." + str(listed[session_id])
                key = session_key(turns, lme_minute(stamp))
                if key not in keys:
                    keys[key] = []
                keys[key].append([row["question_id"], name])
        config.STATE_DIR.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(keys), encoding="utf-8")
        INDEX["keys"] = keys
        return keys
