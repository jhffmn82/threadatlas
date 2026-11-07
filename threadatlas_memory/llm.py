"""Calls to the model that reads the sessions: one prompt in, a JSON reply that fits its shape out.

The ingestor's call policy (kaggle.com/code/jhffmn/threadatlas-document-ingestor, Block 2): the Flex
tier at half price, the standard tier when Flex has no room, three tries on a timeout or a busy server,
and one more asking for the shape again when a reply does not fit. Every call's cost goes to calls.jsonl.
A model without reasoning, such as gpt-4.1-mini, is called on the standard tier with no reasoning effort.
"""

import http.client
import json
import os
import threading
import time
import urllib.error
import urllib.request

from . import config

URL = "https://api.openai.com/v1/chat/completions"
PRICE = {"flex": {"gpt-5.6-luna": (0.10, 0.60)},                                            # $ per million tokens
         "default": {"gpt-5.6-luna": (0.20, 1.20), "gpt-4.1-mini-2025-04-14": (0.40, 1.60)}}
REASONS = ("gpt-5.6-luna",)      # the models that take a reasoning effort and the Flex tier
LOG_LOCK = threading.Lock()
TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float)}


class SchemaError(ValueError):
    pass


def is_of_type(value, name):
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    return name in TYPES and isinstance(value, TYPES[name]) and not isinstance(value, bool)


def check_schema(value, schema, path="$"):
    """Type, required keys, items and enum; the error names the path, and goes back to the model on the retry."""
    allowed = schema.get("type", "object")
    if not isinstance(allowed, list):
        allowed = [allowed]
    fits = False
    for name in allowed:
        if is_of_type(value, name):
            fits = True
    if not fits:
        raise SchemaError(path + ": expected " + "/".join(allowed) + ", got " + type(value).__name__)
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaError(path + ": " + repr(value) + " is not one of " + str(schema["enum"]))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise SchemaError(path + "." + key + ": missing")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                check_schema(value[key], sub, path + "." + key)
    if isinstance(value, list) and "items" in schema:
        for i in range(len(value)):
            check_schema(value[i], schema["items"], path + "[" + str(i) + "]")


def log_call(row):
    with LOG_LOCK:
        config.STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(config.STATE_DIR / "calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def post(payload):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    request = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=900) as response:        # Flex can take minutes
        return response.status, response.read().decode("utf-8")


def call(payload, stage, context):
    model = payload["model"]
    started = time.time()
    for attempt in range(3):
        try:
            status, text = post(payload)
        except urllib.error.HTTPError as error:
            status, text = error.code, error.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))
            continue
        if status == 429 and "flex_unavailable" in text and payload.get("service_tier") == "flex":
            payload = dict(payload)
            payload["service_tier"] = "default"          # Flex has no room for this call: the standard tier takes it
            continue
        if status == 429 or status >= 500:
            if attempt == 2:
                raise RuntimeError("OpenAI " + str(status) + ": " + text[:300])
            time.sleep(15 * (attempt + 1))
            continue
        if status != 200:
            raise RuntimeError("OpenAI " + str(status) + ": " + text[:300])
        break
    body = json.loads(text)
    tier = body.get("service_tier") or payload.get("service_tier")
    price_in, price_out = PRICE.get(tier, PRICE["default"])[model]
    usage = body.get("usage", {})
    tokens_in = usage.get("prompt_tokens", 0)
    tokens_out = usage.get("completion_tokens", 0)
    row = {"stage": stage, "model": body.get("model", model), "tier": tier, "in": tokens_in, "out": tokens_out,
           "seconds": round(time.time() - started, 1), "cost": (tokens_in * price_in + tokens_out * price_out) / 1e6}
    row.update(context)
    log_call(row)
    return body


def generate(prompt, schema, stage, effort="low", context=None):
    """The reply as a dict that fits `schema`, or None after one retry with the error added to the prompt."""
    for attempt in range(2):
        payload = {"model": config.READ_MODEL, "response_format": {"type": "json_object"},
                   "messages": [{"role": "user", "content": prompt}]}
        if config.READ_MODEL in REASONS:
            payload["reasoning_effort"] = effort
            payload["service_tier"] = "flex"
        body = call(payload, stage, context or {})
        try:
            message = body["choices"][0]["message"]
            if not message.get("content"):
                raise SchemaError("empty reply")
            reply = json.loads(message["content"])
            check_schema(reply, schema)
            return reply
        except (SchemaError, ValueError, TypeError, KeyError, IndexError) as error:
            prompt += ("\n\nYour previous reply did not fit the required shape (" + type(error).__name__ + ": " +
                       str(error) + "). Reply again, in exactly the shape asked for.")
    return None
