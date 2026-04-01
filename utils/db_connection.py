import os
import sqlite3
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(ROOT, 'db')
DB_FILE = os.path.join(DB_DIR, 'database.sqlite3')
SCHEMA_FILE = os.path.join(DB_DIR, 'schema.sql')
SEED_FILE = os.path.join(DB_DIR, 'seed.sql')


def _ensure_db_dir():
    os.makedirs(DB_DIR, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    """Return a sqlite3.Connection with foreign keys enabled and row factory as dict.

    This function bootstraps the schema (safe to call multiple times) and seeds sample
    data if the database is empty.
    """
    _ensure_db_dir()
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')

    # Apply schema (idempotent)
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            sql = f.read()
            conn.executescript(sql)

    # Seed if campaigns table is empty
    cur = conn.execute("SELECT count(1) as cnt FROM campaigns LIMIT 1")
    row = cur.fetchone()
    need_seed = True
    if row is not None and row['cnt'] > 0:
        need_seed = False

    if need_seed and os.path.exists(SEED_FILE):
        with open(SEED_FILE, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

    return conn


def dict_from_row(row: Optional[sqlite3.Row]) -> Optional[dict]:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}
