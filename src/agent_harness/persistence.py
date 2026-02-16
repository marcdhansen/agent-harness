from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

DB_DIR = Path(".harness/data")
DB_PATH = DB_DIR / "harness_state.db"


def ensure_db_directory():
    """Create DB directory if it doesn't exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)


def get_sqlite_checkpointer(db_path: str | None = None):
    """
    Returns a SqliteSaver checkpointer for persistent state storage.
    """
    if db_path is None:
        ensure_db_directory()
        db_path = str(DB_PATH)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)
