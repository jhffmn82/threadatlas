"""The prompts that read a chat session, word for word the ingestor's
(kaggle.com/code/jhffmn/threadatlas-document-ingestor, Block 5), with the reply shapes they ask for."""

QUOTE_RULE = ("a passage states a fact when it carries the claim itself, in whatever words the document uses:"
              " it need not repeat the fact's wording, the subject may be a pronoun or a shorter form, and a table row,"
              " a heading or a caption states what it lists")

SESSION_SCHEMA = {"type": "object", "required": ["summary", "facts"],
                  "properties": {"summary": {"type": "string"}, "facts": {"type": "array"}}}
SALIENCE_SCHEMA = {"type": "object", "required": ["entities"], "properties": {"entities": {"type": "array"}}}
# only the reply's outer shape: each item is read on its own, so one malformed entry costs one fact, not the batch
SUPPORT_SCHEMA = {"type": "object", "required": ["unsupported"], "properties": {"unsupported": {"type": "array"}}}
CORRECT_SCHEMA = {"type": "object", "required": ["corrections"], "properties": {"corrections": {"type": "array"}}}


def session_prompt(turns_text):
    return f"""TEXT (a conversation between a user and an assistant; each turn opens with its SESSION ... TURN n line):
{turns_text}

Above is one conversation, or a stretch of one. The record is the user's memory. Record two kinds of fact, and nothing else:
- From the user's turns: what the user says about themselves, the people and things in their life, and their plans, preferences and decisions. In addition, for every sentence in which the user states a detail about themselves, their life, or the people and things in it, record one more fact with subject user, predicate stated, the whole sentence in the user's own words as its object, and the whole sentence as its quote; for these facts only, the object is that sentence rather than a bare value. A question or request to the assistant is not a detail, though a detail stated inside one is.
- From the assistant's turns: each specific name, number, amount, ratio, step or option the assistant gives this user, with the thing it is about as the subject. No descriptions or attributes of things, no definitions, nothing said in general.

Return JSON {{"summary": "...", "facts": [{{"turn", "subject", "predicate", "object", "qualifiers", "quote", "valid_from"}}]}} where:
- summary: the conversation in 3-5 concrete sentences, naming what the user said about themselves
- turn: the number in the TURN line of the turn the fact comes from
- subject: user for what the user says of themselves; otherwise the thing the fact is about, named as that turn names it
- predicate: a lowercase_snake_case relation in the present tense, named the way the text gives it
- object: a short literal value that does not repeat the predicate, or the name of another subject; never a bare true or false
- qualifiers: one short phrase for role, manner or condition, as a string, else null; never an object
- quote: one continuous verbatim passage of that turn that STATES the fact, copied exactly as it appears, punctuation and all, with nothing skipped; never use an ellipsis. {QUOTE_RULE}
- valid_from: an ISO date (YYYY, YYYY-MM or YYYY-MM-DD) only when the quote itself states when the fact began; otherwise null. Never infer a date.
- each fact other than a stated fact is atomic: one attribute or one relationship"""


def salience_prompt(summary, listing):
    return f"""Below is one conversation between a user and an assistant, as its summary and the facts read from it, grouped under the entity each fact is about. The record is the user's memory.

For each entity, give its kind and its salience:
- kind: one lowercase word for what sort of thing it is, such as person, place, organisation, store, product, work, event or project; never thing
- salience: "major" for something worth finding again in a later conversation: a named person, place, organisation, store, product, work, event or project, or a specific thing the user owns, plans, attends or returns to; "minor" for the scaffolding of this one conversation: a category, a section of the assistant's answer, one option among several, a step in a list, an abstract topic. When in doubt, minor.

Return JSON {{"entities": [{{"name", "kind", "salience"}}]}}, one for each entity below, its name exactly as written.

SUMMARY: {summary}

ENTITIES:
{chr(10).join(listing)}"""


def support_prompt(facts):
    return f"""Below are statements one document makes, numbered, each with the passage it rests on.

Return JSON {{"unsupported": [numbers]}}: the numbers of the facts whose own passage does not state them (a loose citation that says something else, or only part of it).

{QUOTE_RULE}. A bare value is the usual near miss: a number quoted without the heading or label that names what it measures carries the figure but not the claim, and does not state it. Only call a fact unsupported when its passage genuinely does not carry the claim. Return an empty list when every passage states its fact.

FACTS:
{chr(10).join(facts)}"""


def correct_prompt(facts):
    return f"""Below are statements one document makes, numbered, each with the passage it rests on. An earlier and cheaper check suspected the passage does not state the statement. That check is often wrong, and this is the second look: decide each one on the passage in front of you.

{QUOTE_RULE}.

Answer for EVERY statement, with a "verdict":
- "stands": the passage does state the statement as written. This is the right answer whenever the claim is there, even if the passage says it in other words or says more besides.
- "corrected": the passage states something about the same subject, but not this. Give the "predicate" (lowercase_snake_case, present tense) and "object" it does state, with "qualifiers" or null. Keep the subject. The object is another entity's name exactly as the passage writes it, or a short value in the passage's own words, never in snake_case; the qualifiers are one short phrase or null, never a remark about the passage.
- "drop": the passage says nothing durable about that subject at all.

Return JSON {{"corrections": [{{"number", "verdict", "predicate", "object", "qualifiers"}}]}}, where "number" is the number of the statement you are answering, as it is printed below.

STATEMENTS:
{chr(10).join(facts)}"""
