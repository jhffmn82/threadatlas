"""Writes the Kaggle notebook for ThreadAtlas's fresh baseline runs of OmniMemEval, and its kernel metadata.

usage: python make_notebook.py <out folder> <RUN> <benchmarks, comma separated> <cpu|gpu>
    RUN "check": set up, test, prepare the data, call no model.
    RUN "smoke": the first few users of each benchmark named, through every step.
    RUN "full":  every user of each benchmark named.
    benchmarks: locomo, lme, beam, halumem, pmv2
"""
import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
RUN = sys.argv[2]
BENCHMARKS = [b for b in sys.argv[3].split(",") if b]
DEVICE = sys.argv[4]
assert RUN in ("check", "smoke", "full") and DEVICE in ("cpu", "gpu")
assert all(b in ("locomo", "lme", "beam", "halumem", "pmv2") for b in BENCHMARKS)
SLUG = sys.argv[5] if len(sys.argv) > 5 else "threadatlas-omnimemeval-baseline"

INTRO = """# ThreadAtlas on OmniMemEval: fresh baseline runs

OmniMemEval's harness at its merged commit, unchanged, run on ThreadAtlas through the `threadatlas` adapter
that is part of the harness. ThreadAtlas's memory package comes from its public repository at a pinned commit.

Every session is read during the run, through `add()`. No store built beforehand is attached, and the
notebook stops if one is. The memory-reading model, the answer model and the judge are the harness's
baseline: `gpt-4.1-mini-2025-04-14`, `gpt-4.1-mini-2025-04-14` and `gpt-4o-mini-2024-07-18`, with `TOPK=20`.

```
the harness at its commit, nothing laid over it
the memory package at its commit, from github.com/jhffmn82/threadatlas
the datasets by the harness's own prepare scripts
for each benchmark: the harness's run script, every step
the records: the harness's results, the reading model's call log, the environment, the commits
```

`RUN = "check"` sets everything up, prepares the data and calls no model. `"smoke"` runs the first few users of
each benchmark named. `"full"` runs every user. `DEVICE = "gpu"` runs the embedding model on the session's GPU.
"""

CONFIG = '''import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RUN = "__RUN__"                    # "check": no model called. "smoke": the first few users. "full": every user
BENCHMARKS = __BENCHMARKS__        # "locomo", "lme", "beam", "halumem", "pmv2"
DEVICE = "__DEVICE__"              # "cpu", or "gpu" for the embedding model on the session's GPU
LABEL = "captions"                     # the run's folder in the harness's results: <LABEL>-<RUN>
READ_MODEL = "gpt-4.1-mini-2025-04-14"                             # the harness's baseline memory-service model
HARNESS_COMMIT = "05513bfa2faa4f19b46089b4fd2691cd60689338"        # jhffmn82/OmniMemEval, main at 1619178 plus the photo description for ThreadAtlas
PACKAGE_COMMIT = "015143cdb995497022b88878c8ebc8c5223d1eee"        # jhffmn82/threadatlas, for threadatlas_memory
WORK = Path("/kaggle/working")
HARNESS = WORK / "omnimemeval"
PACKAGE = WORK / "threadatlas"

# each benchmark: its prepare script, its run script, the options both take, the file its users are in,
# how many users are read at once, and how many a smoke run keeps
BENCH = {
    "locomo": {"prepare": ["data/locomo/prepare_locomo.py"], "script": "scripts/run_locomo_eval.sh", "options": [],
               "data": "data/locomo/locomo10.json", "workers": 10, "smoke": 1},
    "lme": {"prepare": ["data/longmemeval/prepare_longmemeval.py"], "script": "scripts/run_lme_eval.sh", "options": [],
            "data": "data/longmemeval/longmemeval_s_cleaned.json", "workers": 60, "smoke": 20},
    "beam": {"prepare": ["data/beam/prepare_beam.py", "--scale", "100k"], "script": "scripts/run_beam_eval.sh",
             "options": ["--scale", "100k"], "data": "data/beam/beam_100k.json", "workers": 20, "smoke": 1},
    "halumem": {"prepare": ["data/halumem/prepare_halumem.py"], "script": "scripts/run_halumem_eval.sh",
                "options": ["--variant", "medium"], "data": "data/halumem/HaluMem-Medium.jsonl", "workers": 20, "smoke": 1},
    "pmv2": {"prepare": ["data/personamem_v2/prepare_personamem.py"], "script": "scripts/run_pmv2_eval.sh", "options": [],
             "data": "data/personamem_v2/benchmark/text/benchmark.csv", "workers": 20, "smoke": 2},
}

# nothing built beforehand: every session is read through add() during the run
attached = sorted(str(p) for p in Path("/kaggle/input").glob("*")) if Path("/kaggle/input").exists() else []
print("attached inputs:", attached or "none")
if Path("/kaggle/input").exists() and list(Path("/kaggle/input").rglob("threadatlas.sqlite")):
    raise SystemExit("a store built beforehand is attached; this notebook reads every session fresh")

# the key, from the Kaggle secret, for the reading model, the answer model and the judge
key = os.environ.get("OPENAI_API_KEY")
if not key:
    try:
        from kaggle_secrets import UserSecretsClient
        key = UserSecretsClient().get_secret("OPENAI_API_KEY")
    except Exception as error:
        print("the secret could not be read:", type(error).__name__)
print("OPENAI_API_KEY available:", bool(key))
if RUN != "check" and not key:
    raise SystemExit("the OPENAI_API_KEY secret is not attached to this notebook")
if key:
    for name in ("OPENAI_API_KEY", "ANSWER_API_KEY", "EVAL_API_KEY"):
        os.environ[name] = key
'''

SETUP = '''def run(command, **options):
    print("$", " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, check=True, **options)


def said(command, **options):
    return subprocess.run(command, capture_output=True, text=True, **options).stdout.strip()


# the harness from the fork at its commit: upstream main with one change, the photo description kept with a
# ThreadAtlas message in LoCoMo; nothing else laid over it
if not HARNESS.exists():
    run(["git", "clone", "-q", "https://github.com/jhffmn82/OmniMemEval.git", str(HARNESS)])
run(["git", "-C", str(HARNESS), "checkout", "-q", HARNESS_COMMIT])

# the memory package at its commit: only its folder of the repository, whose bulk is the wiki
if not PACKAGE.exists():
    run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", "https://github.com/jhffmn82/threadatlas.git", str(PACKAGE)])
    run(["git", "-C", str(PACKAGE), "sparse-checkout", "set", "threadatlas_memory"])
run(["git", "-C", str(PACKAGE), "checkout", "-q", PACKAGE_COMMIT])
assert (PACKAGE / "threadatlas_memory" / "memory.py").exists()

run([sys.executable, "-m", "pip", "install", "-q", "-r", str(HARNESS / "requirements_user_memory.txt"), "tiktoken"])
if DEVICE == "gpu":         # the embedding model on the GPU: fastembed's GPU build in place of the CPU one
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-q", "-y", "fastembed", "onnxruntime"])
    run([sys.executable, "-m", "pip", "install", "-q", "fastembed-gpu"])
    print(said(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]) or "nvidia-smi reports no GPU")
    # an onnxruntime build whose CUDA and cuDNN libraries this session's driver can run, installed beside it (the
    # package preloads them): the newest first, then the builds made for CUDA 12
    TRY = chr(10).join([
        "import onnxruntime as o",
        "if hasattr(o, 'preload_dlls'): o.preload_dlls()",
        "from fastembed import TextEmbedding",
        "m = TextEmbedding('BAAI/bge-small-en-v1.5', providers=['CUDAExecutionProvider'])",
        "print(','.join(m.model.model.get_providers()))"])
    for build in ("onnxruntime-gpu[cuda,cudnn]", "onnxruntime-gpu[cuda,cudnn]==1.23.2", "onnxruntime-gpu[cuda,cudnn]==1.22.0"):
        run([sys.executable, "-m", "pip", "install", "-q", build])
        tried = subprocess.run([sys.executable, "-c", TRY], capture_output=True, text=True)
        print(build, "->", tried.stdout.strip() or "no session", "|", " / ".join(tried.stderr.strip()[-500:].splitlines()))
        if "CUDAExecutionProvider" in tried.stdout:
            break
    print([line for line in said([sys.executable, "-m", "pip", "list", "--format=freeze"]).splitlines() if line.startswith(("onnxruntime", "fastembed", "nvidia-cudnn", "nvidia-cublas"))])
else:
    run([sys.executable, "-m", "pip", "install", "-q", "fastembed"])
run([sys.executable, "-m", "unittest", "scripts/tests/unit/test_threadatlas_client.py"], cwd=HARNESS)

for benchmark in BENCHMARKS:
    run([sys.executable] + BENCH[benchmark]["prepare"], cwd=HARNESS)


def users_in(benchmark):
    """How many users the benchmark's prepared file holds."""
    path = HARNESS / BENCH[benchmark]["data"]
    if benchmark in ("locomo", "lme"):
        return len(json.loads(path.read_text(encoding="utf-8")))
    if benchmark in ("beam", "halumem"):
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    csv.field_size_limit(10 ** 9)
    with open(path, encoding="utf-8", newline="") as f:
        return len({row["persona_id"] for row in csv.DictReader(f)})


def keep_first(benchmark, keep):
    """A smoke run's users: the prepared file cut to its first few, in place."""
    path = HARNESS / BENCH[benchmark]["data"]
    if benchmark in ("locomo", "lme"):
        path.write_text(json.dumps(json.loads(path.read_text(encoding="utf-8"))[:keep]), encoding="utf-8")
    elif benchmark in ("beam", "halumem"):
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        path.write_text("\\n".join(lines[:keep]) + "\\n", encoding="utf-8")
    else:
        csv.field_size_limit(10 ** 9)
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            names, rows = reader.fieldnames, list(reader)
        first = list(dict.fromkeys(row["persona_id"] for row in rows))[:keep]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=names)
            writer.writeheader()
            writer.writerows(row for row in rows if row["persona_id"] in first)


record = {"run": RUN, "benchmarks": BENCHMARKS, "label": LABEL, "read_model": READ_MODEL, "device": DEVICE,
          "store_built_beforehand": False, "attached_inputs": attached, "data": {}, "users": {}, "workers": {}}
for benchmark in BENCHMARKS:
    path = HARNESS / BENCH[benchmark]["data"]
    record["data"][BENCH[benchmark]["data"]] = hashlib.sha256(path.read_bytes()).hexdigest()
    whole = users_in(benchmark)
    if RUN == "smoke":
        keep_first(benchmark, BENCH[benchmark]["smoke"])
    record["users"][benchmark] = {"in the prepared file": whole, "in this run": users_in(benchmark)}
    record["workers"][benchmark] = min(BENCH[benchmark]["workers"], users_in(benchmark))
    print(benchmark, record["users"][benchmark], "| read at once:", record["workers"][benchmark])

ENV = HARNESS / ".env.threadatlas"
ENV.write_text("\\n".join([
    'THREADATLAS_REPO="' + str(PACKAGE) + '"',
    'THREADATLAS_STATE_DIR="' + str(WORK / "state") + '"',
    'THREADATLAS_READ_MODEL="' + READ_MODEL + '"',
    'THREADATLAS_EMBED_DEVICE="' + ("cuda" if DEVICE == "gpu" else "cpu") + '"',
    "LLM_WORKERS=10",
    "TOPK=20",
    'ANSWER_MODEL="gpt-4.1-mini-2025-04-14"',
    'ANSWER_BASE_URL="https://api.openai.com/v1"',
    'EVAL_MODEL="gpt-4o-mini-2024-07-18"',
    'EVAL_BASE_URL="https://api.openai.com/v1"',
]) + "\\n", encoding="utf-8")

# the package as the run will load it: no session found in a store, the baseline reading model, and the embedding
# model on the device asked for, timed on 512 short texts
probe = subprocess.run(
    [sys.executable, "-c",
     "import sys, time; sys.path.insert(0, sys.argv[1]); from threadatlas_memory import sessions, config, retrieval; "
     "retrieval.embed(['warm up']); t = time.time(); v = retrieval.embed(['My dog is called Rex and he is seven.'] * 512); "
     "print(len(sessions.read_index()), config.READ_MODEL, config.EMBED_DEVICE, "
     "','.join(retrieval.EMBEDDER.model.model.get_providers()), v.shape[0], round(time.time() - t, 2))", str(PACKAGE)],
    capture_output=True, text=True,
    env={**os.environ, "THREADATLAS_STATE_DIR": str(WORK / "state"), "THREADATLAS_READ_MODEL": READ_MODEL,
         "THREADATLAS_EMBED_DEVICE": "cuda" if DEVICE == "gpu" else "cpu"})
print("the package as loaded:", probe.stdout.strip(), probe.stderr[-600:])
fields = probe.stdout.split()
assert len(fields) == 6, "the package did not load: " + probe.stderr[-300:]
assert fields[:2] == ["0", READ_MODEL], "the package would not read every session fresh with the baseline model"
assert DEVICE == "cpu" or "CUDAExecutionProvider" in fields[3], "the embedding model is not on the GPU"
record["embedding"] = {"device": fields[2], "providers": fields[3], "seconds for 512 texts": float(fields[5])}

# the account's limits for the reading model, from the headers of one small call
if RUN != "check":
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({"model": READ_MODEL, "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]}).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        record["rate limits"] = {name: response.headers.get(name) for name in (
            "x-ratelimit-limit-requests", "x-ratelimit-limit-tokens", "x-ratelimit-remaining-requests",
            "x-ratelimit-remaining-tokens")}
    print("rate limits for", READ_MODEL + ":", record["rate limits"])

# what ran, for the record
record.update({"harness": said(["git", "-C", str(HARNESS), "rev-parse", "HEAD"]),
               "package": said(["git", "-C", str(PACKAGE), "rev-parse", "HEAD"]),
               "package_files_changed": said(["git", "-C", str(PACKAGE), "status", "--porcelain", "--untracked-files=no"])})
(WORK / "provenance.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
print(json.dumps(record, indent=1))
with open(WORK / "environment.txt", "w", encoding="utf-8") as f:
    f.write("python " + sys.version + "\\n")
    f.write(said([sys.executable, "-m", "pip", "freeze"]) + "\\n")
'''

RUNS = '''# each benchmark through the harness's own run script, every step
if RUN == "check":
    print("check only: nothing is run and no model is called")
for benchmark in ([] if RUN == "check" else BENCHMARKS):
    version = LABEL + "-" + RUN
    command = (["bash", BENCH[benchmark]["script"], "--lib", "threadatlas", "--env", str(ENV), "--version", version,
                "--workers", str(record["workers"][benchmark])] + BENCH[benchmark]["options"])
    print(" ".join(command), flush=True)
    began = time.time()
    with open(WORK / (benchmark + "-" + version + ".log"), "w", encoding="utf-8") as log:
        done = subprocess.run(command, cwd=HARNESS, stdout=log, stderr=subprocess.STDOUT)
    print(benchmark, "exit", done.returncode, "after", round((time.time() - began) / 60, 1), "minutes")
    lines = (WORK / (benchmark + "-" + version + ".log")).read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-30:]:
        print(line)
'''

RECORDS = '''# the records, beside this notebook's output: the harness's results and the reading model's call log
if (HARNESS / "results").exists():
    shutil.copytree(HARNESS / "results", WORK / "results", dirs_exist_ok=True)
calls = WORK / "state" / "calls.jsonl"
if calls.exists():
    shutil.copy(calls, WORK / "reading-calls.jsonl")
    total = {}
    for line in calls.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        slot = total.setdefault((row.get("stage"), row.get("model")), {"calls": 0, "in": 0, "out": 0, "cost": 0.0, "seconds": 0.0})
        slot["calls"] += 1
        slot["in"] += row.get("in", 0)
        slot["out"] += row.get("out", 0)
        slot["cost"] += row.get("cost", 0.0)
        slot["seconds"] += row.get("seconds", 0.0)
    for (stage, model), slot in sorted(total.items(), key=str):
        print("reading:", stage, model, slot["calls"], "calls,", slot["in"], "tokens in,", slot["out"], "out, $%.2f" % slot["cost"])
    print("reading in all: %d calls, %d tokens in, %d out, $%.2f at list price, %.2f hours inside calls" % (
        sum(s["calls"] for s in total.values()), sum(s["in"] for s in total.values()),
        sum(s["out"] for s in total.values()), sum(s["cost"] for s in total.values()),
        sum(s["seconds"] for s in total.values()) / 3600))
results = WORK / "results"
for path in sorted(results.rglob("*grades.json")) if results.exists() else []:
    grades = json.loads(path.read_text(encoding="utf-8"))
    print(path)
    print(" metrics:", json.dumps(grades.get("metrics"))[:700])
    print(" status:", json.dumps(grades.get("pipeline_status")))
for path in sorted(results.rglob("exp_report.md")) if results.exists() else []:
    print(path)
    print(path.read_text(encoding="utf-8")[:2500])

# the checkouts, the datasets inside them and the users' stores are not records: only the files above stay
for folder in (HARNESS, PACKAGE, WORK / "state"):
    shutil.rmtree(folder, ignore_errors=True)
print(sorted(str(p.relative_to(WORK)) for p in WORK.glob("*")))
'''


def cell(kind, source):
    lines = source.rstrip("\n").split("\n")
    body = [line + "\n" for line in lines[:-1]] + [lines[-1]]
    if kind == "markdown":
        return {"cell_type": "markdown", "metadata": {}, "source": body}
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": body}


config = CONFIG.replace("__RUN__", RUN).replace("__BENCHMARKS__", json.dumps(BENCHMARKS)).replace("__DEVICE__", DEVICE)
codes = [config, SETUP, RUNS, RECORDS]
for number, code in enumerate(codes, 1):
    compile(code, f"cell {number}", "exec")
notebook = {"cells": [cell("markdown", INTRO)] + [cell("code", code) for code in codes],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / (SLUG + ".ipynb")).write_text(json.dumps(notebook, indent=1), encoding="utf-8")
metadata = {"id": "jhffmn/" + SLUG, "title": SLUG, "code_file": SLUG + ".ipynb", "language": "python",
            "kernel_type": "notebook", "is_private": True, "enable_gpu": DEVICE == "gpu", "enable_tpu": False,
            "enable_internet": True, "keywords": [], "dataset_sources": [], "kernel_sources": [],
            "competition_sources": [], "model_sources": []}
if DEVICE == "cpu":         # the image the earlier runs used; a GPU session needs Kaggle's GPU image, so it is left to Kaggle
    metadata["docker_image"] = "gcr.io/kaggle-images/python@sha256:0717e81990be591f8c5f98f033d29ab23e9ffde057e5b3a6bd4371f93969e962"
(OUT / "kernel-metadata.json").write_text(json.dumps(metadata, indent=1), encoding="utf-8")
print("wrote", OUT / (SLUG + ".ipynb"), "| RUN =", RUN, "| BENCHMARKS =", BENCHMARKS, "| DEVICE =", DEVICE, "| cells compile:", len(codes))
