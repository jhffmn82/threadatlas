"""Step 1 for one chat session: the facts it states, checked against its own words.

The ingestor's path for a chat (kaggle.com/code/jhffmn/threadatlas-document-ingestor, Blocks 4 and 6 to 9):

    read:      one call per 40,000 characters of turns returns a summary and facts, each tied to a turn;
               a fact is kept only if its quote is found in that turn (the quote gate) and its subject
               is the user or is named in that turn
    salience:  one call gives each entity a kind and says whether it is major; the user is a major person
    entities:  one entity per name; a major gets its own node, a minor's facts go on the session's node
    support:   the facts are read against their passages, 60 a call; the ones not stated are flagged
    correct:   a flagged fact gets a second look: it stands, is reworded to what its passage does state,
               or is dropped; what is kept is checked against its passage once more
    rows:      the session's nodes, facts and abstract, in the store's own columns
"""

import unicodedata

from . import llm
from .prompts import (CORRECT_SCHEMA, SALIENCE_SCHEMA, SESSION_SCHEMA, SUPPORT_SCHEMA, correct_prompt,
                      salience_prompt, session_prompt, support_prompt)

SESSION_WINDOW = 40000       # characters of chat read in one call; a longer session is read in stretches
VERIFY_BATCH = 60            # facts to a support or correction call
WORDS_NEEDED = 0.85          # the share of a quote's words a `words` match must hold, in order

# typographic marks read as their plain forms when a quote is matched; the soft hyphen is dropped
REPLACEMENTS = {chr(0x2018): "'", chr(0x2019): "'", chr(0x201C): '"', chr(0x201D): '"', chr(0x2013): "-",
                chr(0x2014): "-", chr(0x2012): "-", chr(0x2212): "-", chr(0x2010): "-", chr(0x2011): "-",
                chr(0x00AD): "", chr(0x00A0): " "}
QUOTE_PAIRS = {chr(0x201C): chr(0x201D), '"': '"', chr(0x2018): chr(0x2019), "'": "'"}


# --- small text helpers ------------------------------------------------------------------------------

def norm(s):
    """One space between words, case folded."""
    return " ".join(str(s or "").split()).casefold()


def loose_name(name):
    """A name as the model may write it back: case folded, one space between words, a leading article dropped."""
    loose = norm(name)
    for article in ("the ", "a ", "an "):
        if loose.startswith(article):
            return loose[len(article):]
    return loose


def snake_case(s):
    out = []
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "_":
            out.append("_")
    return "".join(out).strip("_")


def name_words(name):
    """The words of a name longer than three letters, case folded, punctuation stripped."""
    words = set()
    for token in name.replace("_", " ").casefold().split():
        word = ""
        for ch in token:
            if ch.isalpha():
                word += ch
        if len(word) > 3:
            words.add(word)
    return words


def is_word_char(ch):
    return ch.isalnum() or ch == "_"


def valid_numbers(numbers, n):
    """The numbers a reply points at, as distinct integers within 1..n."""
    good = []
    if not isinstance(numbers, list):
        return good
    for x in numbers:
        if isinstance(x, str) and x.strip().isdigit():
            x = int(x)
        if isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= n and x not in good:
            good.append(x)
    return good


def fact_line(fact):
    line = fact["subject"] + " " + fact["predicate"] + " " + fact["object"]
    if fact["qualifiers"]:
        line += " [" + fact["qualifiers"] + "]"
    return line


def quoted(fact):
    return '("' + " ".join(fact["quote"].split()) + '")'


# --- the quote gate: is the quote in the turn, and where ---------------------------------------------

def normalised(text):
    """(normalised string, map from each of its characters to an offset in the original)."""
    out = []
    back = []
    in_space = True
    for i in range(len(text)):
        ch = REPLACEMENTS.get(text[i], text[i])
        if ch == "-":                   # hyphens are left out on both sides, so a broken compound still matches
            continue
        if ch.isspace():
            if not in_space:
                out.append(" ")
                back.append(i)
                in_space = True
            continue
        in_space = False
        for c in unicodedata.normalize("NFKC", ch).casefold():
            out.append(c)
            back.append(i)
    if out and out[-1] == " ":
        out.pop()
        back.pop()
    return "".join(out), back


def normalised_unit(text, cache):
    if "norm" not in cache:
        cache["norm"] = normalised(text)
    return cache["norm"]


def word_runs(s):
    """Every run of word characters in s, as (word, start, end)."""
    runs = []
    i = 0
    while i < len(s):
        if is_word_char(s[i]):
            j = i
            while j < len(s) and is_word_char(s[j]):
                j += 1
            runs.append((s[i:j], i, j))
            i = j
        else:
            i += 1
    return runs


def words_only(s):
    words = []
    for word, start, end in word_runs(s):
        words.append(word)
    return words


def unwrapped(written):
    """One layer of the model's own quotation marks off; a single mark alone stays, as it may be an apostrophe."""
    if len(written) >= 2 and written[0] in QUOTE_PAIRS and written[-1] == QUOTE_PAIRS[written[0]]:
        return written[1:-1].strip()
    bare = written
    if bare[:1] in (chr(0x201C), '"'):
        bare = bare[1:]
    if bare[-1:] in (chr(0x201D), '"'):
        bare = bare[:-1]
    return bare.strip()


def classify_miss(ntext, nquote):
    """'paraphrase' when at least seven in ten of the quote's words appear in order, else 'not_found'."""
    wanted = words_only(nquote)
    matched = 0
    for word in words_only(ntext):
        if matched < len(wanted) and word == wanted[matched]:
            matched += 1
    if matched >= 0.7 * max(1, len(wanted)):
        return "paraphrase"
    return "not_found"


def find_exact_or_normalised(text, needle, cache):
    needle = needle.strip()
    if not needle:
        return None, None, "empty"
    i = text.find(needle)
    if i >= 0:
        return i, i + len(needle), "exact"
    ntext, back = normalised_unit(text, cache)
    nneedle = normalised(needle)[0]
    i = -1
    if nneedle:
        i = ntext.find(nneedle)
    if i >= 0:
        return back[i], back[i + len(nneedle) - 1] + 1, "normalised"
    return None, None, classify_miss(ntext, nneedle)


def in_order(wanted, have):
    """How many of `wanted` occur in `have` in order (the longest common subsequence), the first and last
    positions in `have` that take part, and how many of `wanted` they span."""
    n = len(wanted)
    m = len(have)
    table = []
    for i in range(n + 1):
        table.append([0] * (m + 1))
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if wanted[i] == have[j]:
                table[i][j] = table[i + 1][j + 1] + 1
            else:
                table[i][j] = max(table[i + 1][j], table[i][j + 1])
    i = 0
    j = 0
    taken = []
    while i < n and j < m:
        if wanted[i] == have[j]:
            taken.append((i, j))
            i += 1
            j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    if not taken:
        return 0, 0, 0, 0
    return len(taken), taken[0][1], taken[-1][1], taken[-1][0] - taken[0][0] + 1


def words_hit(text, quote, cache):
    """The shortest passage holding at least WORDS_NEEDED of the quote's words in order, no longer than the
    quote plus three words, the quote's unmatched words only at its front or back; (start, end) or (None, None)."""
    wanted = words_only(normalised(quote)[0])
    if len(wanted) < 4:
        return None, None
    ntext, back = normalised_unit(text, cache)
    words = word_runs(ntext)
    needed = max(4, int(WORDS_NEEDED * len(wanted) + 0.999))
    best = None
    for at in range(len(words)):
        if words[at][0] not in wanted:
            continue
        window = []
        for w in words[at:at + len(wanted) + 3]:
            window.append(w[0])
        matched, first, last, spanned = in_order(wanted, window)
        if matched >= needed and spanned == matched:
            if best is None or (matched, first - last) > (best[0], best[1] - best[2]):
                best = (matched, at + first, at + last)
    if best is None:
        return None, None
    return back[words[best[1]][1]], back[words[best[2]][2] - 1] + 1


def surface_spans(text, surface, cache):
    """Every whole-word occurrence of a phrase in the turn, found on the normalised copy."""
    nsurface = normalised(surface or "")[0]
    if not nsurface:
        return []
    ntext, back = normalised_unit(text, cache)
    spans = []
    i = ntext.find(nsurface)
    while i >= 0:
        j = i + len(nsurface)
        before = " "
        if i > 0:
            before = ntext[i - 1]
        after = " "
        if j < len(ntext):
            after = ntext[j]
        if not is_word_char(before) and not is_word_char(after):
            spans.append((back[i], back[j - 1] + 1))
        i = ntext.find(nsurface, i + 1)
    return spans


def locate(text, quote, cache):
    """(start, end, how) in `text`, or (None, None, why). Every path keeps a verbatim slice of the turn."""
    written = (quote or "").strip()
    start, end, how = find_exact_or_normalised(text, written, cache)
    if start is not None:
        return start, end, how
    bare = unwrapped(written)
    if bare and bare != written:
        spans = surface_spans(text, bare, cache)
        if spans:
            return spans[0][0], spans[0][1], "unwrapped"
    start, end = words_hit(text, bare, cache)
    if start is not None:
        return start, end, "words"
    return None, None, how


# --- reading the session -----------------------------------------------------------------------------

def session_windows(turns):
    """The turns in reading order, cut into stretches of at most SESSION_WINDOW characters."""
    windows = []
    current = []
    size = 0
    for turn in turns:
        if current and size + len(turn["text"]) > SESSION_WINDOW:
            windows.append(current)
            current = []
            size = 0
        current.append(turn)
        size += len(turn["text"])
    if current:
        windows.append(current)
    return windows


def read_session(doc, turns):
    """(facts by turn position, summary). Each kept fact is tied to its turn by a quote found in that turn."""
    tag = doc["doc_id"][:8]
    by_number = {}
    for turn in turns:
        by_number[int(turn["label"].split(" ")[3])] = turn
    facts_of = {}
    for turn in turns:
        facts_of[turn["position"]] = []
    summaries = []
    seen = set()
    caches = {}
    for window in session_windows(turns):
        text = ""
        for turn in window:
            text += turn["text"]
        reply = llm.generate(session_prompt(text), SESSION_SCHEMA, "session", effort="medium",
                             context={"doc": doc["source_uri"]})
        if not reply:
            continue
        summaries.append(" ".join(str(reply["summary"]).split()))
        for item in reply["facts"]:
            if not isinstance(item, dict):
                continue
            readable = True
            for key in ("subject", "predicate", "object", "quote"):
                if not isinstance(item.get(key), str):
                    readable = False
            if not readable:
                continue
            number = item.get("turn")
            if not isinstance(number, int) or number not in by_number:
                continue                                  # a turn the session does not have
            turn = by_number[number]
            written = item["subject"].strip()
            thing = item["object"].strip()
            predicate = snake_case(item["predicate"]) or "related_to"
            subject = written
            if written.casefold() == "user":
                subject = "user"
            start, end, how = locate(turn["text"], item["quote"], caches.setdefault(turn["unit_id"], {}))

            # the gate: a subject the turn never names, a fact about itself, a quote not found, a repeat
            if subject != "user" and subject.casefold() not in turn["text"].casefold() \
                    and not (name_words(subject) & name_words(turn["text"])):
                continue
            if norm(thing) == norm(subject) or start is None:
                continue
            if (turn["unit_id"], subject, predicate, norm(thing)) in seen:
                continue
            seen.add((turn["unit_id"], subject, predicate, norm(thing)))

            qualifiers = item.get("qualifiers")
            if isinstance(qualifiers, str):
                qualifiers = " ".join(qualifiers.split()) or None
            else:
                qualifiers = None
            facts = facts_of[turn["position"]]
            facts.append({"fact_id": tag + ":u" + str(turn["position"]) + ":f" + str(len(facts) + 1),
                          "subject": subject, "predicate": predicate, "object": thing, "qualifiers": qualifiers,
                          "unit_id": turn["unit_id"], "position": turn["position"],
                          "quote": turn["text"][start:end], "quote_start": turn["start"] + start,
                          "quote_end": turn["start"] + end})

    # a "stated" fact over the same words as another kept fact says nothing new
    for position in facts_of:
        spans = set()
        for fact in facts_of[position]:
            if fact["predicate"] != "stated":
                spans.add((fact["quote_start"], fact["quote_end"]))
        kept = []
        for fact in facts_of[position]:
            if fact["predicate"] == "stated" and (fact["quote_start"], fact["quote_end"]) in spans:
                continue
            kept.append(fact)
        facts_of[position] = kept
    return facts_of, " ".join(summaries) or None


def mark_salience(facts_of, summary, doc):
    """{name: (kind, major)} for every subject but the user, from one call with every fact in view."""
    grouped = {}
    for position in facts_of:
        for fact in facts_of[position]:
            if fact["subject"] != "user":
                grouped.setdefault(fact["subject"], []).append(fact)
    if not grouped:
        return {}
    listing = []
    for name in grouped:
        listing.append(name)
        for fact in grouped[name]:
            text = fact["predicate"] + " " + fact["object"]
            if fact["qualifiers"]:
                text += " [" + fact["qualifiers"] + "]"
            listing.append("  - " + text + " " + quoted(fact))
    reply = llm.generate(salience_prompt(summary or "(none)", listing), SALIENCE_SCHEMA, "salience",
                         context={"doc": doc["source_uri"]})
    marks = {}
    if reply:
        for item in reply.get("entities", []):
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                marks.setdefault(norm(item["name"]), item)
    found = {}
    for name in grouped:
        item = marks.get(norm(name), {})
        kind = str(item.get("kind") or "").strip().casefold()
        if kind == "thing":                 # the prompt refuses "thing" as a kind
            kind = ""
        major = str(item.get("salience") or "").strip().casefold() == "major"
        found[name] = (kind or None, major)
    return found


# --- the support check and the second look -----------------------------------------------------------

def unsupported_of(facts, doc, stage):
    """(the ids of facts whose passage does not state them, whether any batch was refused)."""
    flagged = []
    refused = False
    for at in range(0, len(facts), VERIFY_BATCH):
        batch = facts[at:at + VERIFY_BATCH]
        listing = []
        for n in range(len(batch)):
            listing.append(str(n + 1) + ". " + fact_line(batch[n]) + "  " + quoted(batch[n]))
        reply = llm.generate(support_prompt(listing), SUPPORT_SCHEMA, stage, context={"doc": doc["source_uri"]})
        if reply is None:
            refused = True
            continue
        for n in valid_numbers(reply.get("unsupported"), len(batch)):
            flagged.append(batch[n - 1]["fact_id"])
    return flagged, refused


def one_phrase(value):
    """A qualifier as one short phrase, or None."""
    if value is None or isinstance(value, dict):
        return None
    if isinstance(value, (list, tuple)):
        parts = []
        for x in value:
            if str(x).strip():
                parts.append(str(x).strip())
        value = ", ".join(parts)
    phrase = str(value).strip()
    if phrase[:1] in ("{", "[") or phrase.casefold().startswith("the passage"):
        return None
    return phrase or None


def statement_number(item, n):
    """The statement an answer is about, as a number in 1..n; "3." and "3)" are three."""
    for key in ("number", "fact", "n", "id"):
        if key not in item:
            continue
        value = item[key]
        if isinstance(value, str):
            digits = ""
            for ch in value.strip():
                if not ch.isdigit():
                    break
                digits += ch
            value = digits
        found = valid_numbers([value], n)
        if found:
            return found[0]
    return None


def corrected_fact(fact, item, listed):
    """The corrected statement, or None when it fails the checks a fact must pass: it says something, its
    object restates neither subject nor predicate, it is not a bare boolean, and the subject has not moved."""
    subject = str(item.get("subject") or fact["subject"]).strip()
    predicate = snake_case(str(item.get("predicate") or "")) or fact["predicate"]
    thing = str(item.get("object") or "").strip()
    if "_" in thing and " " not in thing:
        thing = thing.replace("_", " ")
    thing = listed.get(loose_name(thing), thing)
    if not thing or thing.casefold() in ("true", "false") or norm(subject) != norm(fact["subject"]):
        return None
    said = norm(thing).replace("_", " ")
    if said == norm(subject).replace("_", " ") or said == norm(predicate).replace("_", " "):
        return None
    return {"subject": subject, "predicate": predicate, "object": thing, "qualifiers": one_phrase(item.get("qualifiers"))}


def corrections_of(flagged, doc, listed_of):
    """{fact id: the corrected statement, or None to keep it as written}. A fact that is dropped, or that no
    answer reaches, is left out, and so is not kept."""
    out = {}
    ids = sorted(flagged)
    for at in range(0, len(ids), VERIFY_BATCH):
        batch = ids[at:at + VERIFY_BATCH]
        listing = []
        for n in range(len(batch)):
            fact = flagged[batch[n]]
            listing.append(str(n + 1) + ". " + fact_line(fact) + "  " + quoted(fact))
        reply = llm.generate(correct_prompt(listing), CORRECT_SCHEMA, "correct", effort="medium",
                             context={"doc": doc["source_uri"]})
        if reply is None:                     # a refused call is no evidence against its facts: they stand
            for fact_id in batch:
                out[fact_id] = None
            continue
        for item in reply.get("corrections", []):
            if not isinstance(item, dict):
                continue
            number = statement_number(item, len(batch))
            if number is None:
                continue
            fact_id = batch[number - 1]
            fact = flagged[fact_id]
            verdict = str(item.get("verdict") or "").strip().lower()
            if verdict == "drop":
                continue
            if verdict != "corrected":
                out[fact_id] = None
                continue
            fixed = corrected_fact(fact, item, listed_of.get(fact["unit_id"], {}))
            if fixed is None:
                continue
            if fixed["predicate"] == fact["predicate"] and norm(fixed["object"]) == norm(fact["object"]).replace("_", " "):
                out[fact_id] = None           # the same fact back again: it stands
            else:
                out[fact_id] = fixed
    return out


def verify(facts, doc, listed_of):
    """(flagged ids, corrections): the support check, the second look, and one more check of what is kept."""
    flagged_ids, refused = unsupported_of(facts, doc, "support")
    if not flagged_ids:
        return set(), {}
    by_id = {}
    for fact in facts:
        by_id[fact["fact_id"]] = fact
    flagged = {}
    for fact_id in flagged_ids:
        flagged[fact_id] = by_id[fact_id]
    corrections = corrections_of(flagged, doc, listed_of)
    if corrections:
        checked = []
        for fact_id in corrections:
            fact = dict(flagged[fact_id])
            if corrections[fact_id]:
                fact.update(corrections[fact_id])
            checked.append(fact)
        failed, refused = unsupported_of(checked, doc, "verify")
        if not refused:
            for fact_id in failed:
                corrections.pop(fact_id, None)
    return set(flagged_ids), corrections


# --- the whole session ---------------------------------------------------------------------------------

def unit_names(facts):
    """The distinct subjects of one turn's facts, in order: the entities that turn names."""
    names = []
    for fact in facts:
        if fact["subject"] not in names:
            names.append(fact["subject"])
    return names


def read_document(doc, units):
    """Step 1 for one session: (nodes, facts, abstract) as rows of the store's node, fact and abstract tables."""
    tag = doc["doc_id"][:8]
    doc_node = tag + ":doc"
    turns = []
    for unit in units:
        turn = dict(unit)
        turn["text"] = doc["text"][unit["start"]:unit["end"]]
        turns.append(turn)

    facts_of, summary = read_session(doc, turns)
    salience = mark_salience(facts_of, summary, doc)

    # one entity per name, numbered in order of first appearance; a major with facts gets its own node
    index_of = {}
    names = []
    for unit in units:
        for fact in facts_of[unit["position"]]:
            if norm(fact["subject"]) not in index_of:
                index_of[norm(fact["subject"])] = len(names)
                names.append(fact["subject"])
    node_of = {}
    nodes = []
    for i in range(len(names)):
        name = names[i]
        kind, major = salience.get(name, (None, False))
        if name == "user":
            kind = "person"
            major = True
        if major:
            node_of[norm(name)] = tag + ":n" + str(i)
            nodes.append({"node_id": tag + ":n" + str(i), "name": name, "kind": kind})
    nodes.append({"node_id": doc_node, "name": doc["title"] or doc["source_uri"], "kind": "document"})

    # every fact read against its passage; the ones flagged are corrected or dropped
    every = []
    listed_of = {}
    for unit in units:
        loose = {}
        counts = {}
        for fact in facts_of[unit["position"]]:
            every.append(fact)
        for name in unit_names(facts_of[unit["position"]]):
            key = loose_name(name)
            counts[key] = counts.get(key, 0) + 1
            loose[key] = name
        listed = {}
        for key in loose:
            if counts[key] == 1:
                listed[key] = loose[key]
        listed_of[unit["unit_id"]] = listed
    flagged, corrections = verify(every, doc, listed_of)

    when_of = {}
    for unit in units:
        when_of[unit["unit_id"]] = unit["occurred_at"]
    facts = []
    for fact in every:
        if fact["fact_id"] in flagged and fact["fact_id"] not in corrections:
            continue                                   # its passage does not state it, and it could not be corrected
        fix = corrections.get(fact["fact_id"])
        subject_node = node_of.get(norm(fact["subject"]))
        direction = "forward"
        if subject_node is None:                       # a minor's fact goes on the session, as mentioned
            subject_node = doc_node
            direction = "mentioned"
        thing = fact["object"]
        predicate = fact["predicate"]
        qualifiers = fact["qualifiers"]
        if fix:
            thing = fix["object"]
            predicate = fix["predicate"]
            qualifiers = fix["qualifiers"]
        object_node = node_of.get(norm(thing))
        facts.append({"doc_id": doc["doc_id"], "fact_id": fact["fact_id"], "subject": subject_node,
                      "subject_name": fact["subject"], "predicate": predicate, "object": object_node or thing,
                      "object_is_node": 1 if object_node else 0, "qualifiers": qualifiers, "unit_id": fact["unit_id"],
                      "quote": fact["quote"], "quote_start": fact["quote_start"], "quote_end": fact["quote_end"],
                      "occurred_at": when_of.get(fact["unit_id"]), "direction": direction})

    # the session's own facts, from its record, with no quote
    own = [("has_title", doc["title"]), ("has_date", doc["occurred_at"]), ("has_source_class", doc["source_class"]),
           ("belongs_to_history", doc["source_uri"].split("/")[-2])]
    numbered = 0
    for predicate, value in own:
        if not value:
            continue
        numbered += 1
        facts.append({"doc_id": doc["doc_id"], "fact_id": tag + ":doc:f" + str(numbered), "subject": doc_node,
                      "subject_name": doc["title"] or doc["source_uri"], "predicate": predicate, "object": str(value),
                      "object_is_node": 0, "qualifiers": None, "unit_id": None, "quote": None, "quote_start": None,
                      "quote_end": None, "occurred_at": doc["occurred_at"], "direction": "forward"})

    abstract = None
    if summary:
        abstract = {"node_id": doc_node, "text": summary}
    return nodes, facts, abstract
