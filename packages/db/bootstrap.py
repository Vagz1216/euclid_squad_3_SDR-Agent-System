"""
Apply SQLite schema and optional seed from db/schema.sql and db/seed.sql.

For non-SQLite URLs, session setup uses SQLAlchemy metadata instead.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sqlite_paths(database_url: str) -> Path | None:
    """Return filesystem path for a sqlite URL, or None."""
    from sqlalchemy.engine.url import make_url

    try:
        u = make_url(database_url)
    except Exception:
        return None
    if u.get_backend_name() != "sqlite":
        return None
    if not u.database or u.database == ":memory:":
        return None
    # Absolute on disk: sqlite:////var/data/x.db -> database '/var/data/x.db'
    p = Path(u.database)
    if p.is_absolute():
        return p
    return Path(p)


def bootstrap_sqlite_file(database_url: str) -> Path | None:
    """
    Ensure parent dir exists, apply db/schema.sql, seed if campaigns empty.
    Returns the DB file path if SQLite, else None.
    """
    path = _sqlite_paths(database_url)
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)

    root = _repo_root()
    schema_file = root / "db" / "schema.sql"
    seed_file = root / "db" / "seed.sql"

    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        if schema_file.is_file():
            conn.executescript(schema_file.read_text(encoding="utf-8"))
        cur = conn.execute("SELECT count(1) FROM campaigns")
        row = cur.fetchone()
        need_seed = row is None or row[0] == 0
        if need_seed and seed_file.is_file():
            conn.executescript(seed_file.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()

    return path
