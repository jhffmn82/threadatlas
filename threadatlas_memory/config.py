"""Where things are, the models, and the retrieval setting. Every path can be set from the environment."""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# the store the pipeline built (threadatlas.sqlite and threadatlas.npy) and Step 0's export
STORE_DIR = Path(os.environ.get("THREADATLAS_STORE_DIR", str(REPO / "data" / "global")))
STEP0_DIR = Path(os.environ.get("THREADATLAS_STEP0_DIR", str(REPO / "data" / "step0")))

# the benchmark file the store's chat histories were read from, so a session already read is found again
SOURCE_FILE = Path(os.environ.get("THREADATLAS_SOURCE",
                                  str(REPO / "data" / "raw" / "longmemeval" / "longmemeval_s.json")))

# one folder per user, holding that user's store
STATE_DIR = Path(os.environ.get("THREADATLAS_STATE_DIR", str(REPO / "memory-state")))

# Step 1's model for a chat: the reading, salience, the support check, corrections
READ_MODEL = os.environ.get("THREADATLAS_READ_MODEL", "gpt-5.6-luna")
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
DIMENSION = 384

# the retrieval setting: LongMemEval's best, two hops from 40 hits of each search; the item count binds, not tokens
HOPS = int(os.environ.get("THREADATLAS_HOPS", "2"))
HITS = int(os.environ.get("THREADATLAS_HITS", "40"))
BUDGET = int(os.environ.get("THREADATLAS_BUDGET", "100000"))

# text OmniMemEval removes from every turn before a memory sees it; a session's key leaves it out the same way
DROPPED = ("<|endoftext|>",)

# the head of every packet, word for word the retrieval notebook's, so any reader is told how to read the records
PACKET_HEADER = """The records below are dated and name their documents; a "source" is the passage of the
document its facts were read from. When records disagree, the one with the later date is current. If the
question asks for a fact the records do not state, say so. If it asks for advice or a recommendation, give
one, built on what the records say about the person asking: what they own, use and prefer."""
