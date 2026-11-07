"""ThreadAtlas as a memory a harness can talk to.

    add(messages, user_id, minute)   one chat session of one user goes into memory
    search(query, user_id, top_k)    the retrieval packet for a question, from that user's memory
    delete(user_id)                  the user is forgotten

    config.py     paths, models and the retrieval setting
    sessions.py   a session's key, and the sessions the pipeline has already read
    store.py      one user's store: its tables, keyword index and vectors
    retrieval.py  retrieval over a user's store
    memory.py     add, search and delete
"""

from .memory import add, delete
from .memory import search_memory as search

__all__ = ["add", "search", "delete"]
