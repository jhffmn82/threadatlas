"""Step 0 for one chat session: the session as a document of dated turns, the way the extractor writes one
(the extractor notebook, kaggle.com/code/jhffmn/threadatlas-extractor, Blocks 0, 2, 7 and 9).

    the session file is {"session_id", "turns": [{"role", "content", "timestamp"}]}; its id is the sha256 of its bytes
    the text is one block per turn that says something:
        SESSION <id> TURN <n> <time>
        role: content
        (a blank line)
    each such turn is one unit, labelled by its opening line and dated by its timestamp
"""

import hashlib
import json
from datetime import datetime


def turn_time(value):
    """An ISO timestamp as the extractor writes a unit's date, or None."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except (ValueError, AttributeError):
        return None


def unit_id(doc_id, text, start, end, seen):
    """Content hash of the slice; the n-th identical slice in one document gets n in the hash."""
    body = text[start:end]
    n = seen.get(body, 0)
    seen[body] = n + 1
    return hashlib.sha256((doc_id + "\n" + str(n) + "\n" + body).encode("utf-8")).hexdigest()


def session_document(session_id, turns, minute, source_uri):
    """The document and its units for one session. `minute` is the session's date as 'YYYY-MM-DDTHH:MM',
    stamped on every turn as Step 0 stamps a LongMemEval history's sessions."""
    stamped = []
    for turn in turns:
        stamped.append({"role": turn["role"], "content": turn["content"], "timestamp": minute})
    data = json.dumps({"session_id": session_id, "turns": stamped}, ensure_ascii=False).encode("utf-8")
    doc_id = hashlib.sha256(data).hexdigest()

    text = ""
    units = []
    seen = {}
    for i in range(len(stamped)):
        turn = stamped[i]
        if not str(turn["content"]).replace(chr(0x200B), "").strip():     # a turn that says nothing is left out
            continue
        start = len(text)
        label = "SESSION " + str(session_id) + " TURN " + str(i + 1) + " " + minute
        text += label + "\n" + turn["role"] + ": " + str(turn["content"]) + "\n\n"
        units.append({"unit_id": unit_id(doc_id, text, start, len(text), seen), "doc_id": doc_id, "position": len(units),
                      "label": label, "kind": turn["role"], "start": start, "end": len(text),
                      "occurred_at": turn_time(minute)})

    dates = []
    for unit in units:
        if unit["occurred_at"]:
            dates.append(unit["occurred_at"])
    document = {"doc_id": doc_id, "source_uri": source_uri, "title": str(session_id), "author": None,
                "source_class": "record", "text": text, "occurred_at": min(dates) if dates else None}
    return document, units
