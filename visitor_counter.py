"""Persistent, anonymous browser count; no IP addresses or fingerprints."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import UUID

import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
_browser_identity = components.declare_component(
    "bondhu_visitor_identity", path=str(ROOT / "visitor_component")
)


def count_visitors(visitor_id=None, db_path=None):
    """Register a valid browser UUID once and return the all-time total."""
    identity = None
    if isinstance(visitor_id, str):
        try:
            parsed = UUID(visitor_id)
            if parsed.version == 4:
                identity = str(parsed)
        except ValueError:
            pass

    database = Path(db_path or os.getenv("BONDHU_VISITOR_DB_PATH", ROOT / "data" / "visitors.sqlite3"))
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database, timeout=10)) as connection:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS visitors (id TEXT PRIMARY KEY)")
            if identity:
                connection.execute("INSERT OR IGNORE INTO visitors (id) VALUES (?)", (identity,))
            return connection.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]


def unique_visitor_count():
    identity = _browser_identity(key="bondhu_browser_identity", default=None)
    try:
        return count_visitors(identity)
    except (OSError, sqlite3.Error):
        # An unavailable database must not turn into a misleading zero count.
        return None
