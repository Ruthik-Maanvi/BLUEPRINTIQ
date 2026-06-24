"""
SQLite persistence layer.

Design decision (see docs/decisions.md): we use the stdlib `sqlite3` module
directly with hand-written SQL rather than an ORM. Rationale:
  - The schema is small and stable for an MVP.
  - SQLite FTS5 (used for full-text search) is most reliably driven with raw
    SQL/virtual tables; ORMs add an abstraction layer that fights FTS5.
  - "Simple reliable systems over complex unstable systems" (MVP principle).

A single connection-per-call pattern is used (`get_connection`), which is
the simplest correct way to use sqlite3 safely with FastAPI's threaded
request handling.
"""
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.core.config import get_settings

settings = get_settings()

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'created'
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    content_type TEXT,
    document_type TEXT,
    page_count INTEGER DEFAULT 0,
    ocr_engine_used TEXT,
    ocr_status TEXT NOT NULL DEFAULT 'pending',
    ocr_note TEXT,
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ocr_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    raw_text TEXT,
    tables_json TEXT,
    ocr_confidence REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    material_name TEXT NOT NULL,
    category TEXT,
    procurement_stage TEXT,
    secondary_stage TEXT,
    quantity REAL,
    unit TEXT,
    confidence REAL NOT NULL,
    evidence TEXT NOT NULL,
    source_document TEXT NOT NULL,
    source_page INTEGER,
    extraction_method TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reasoning_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    what_detected TEXT NOT NULL,
    where_detected TEXT NOT NULL,
    why_category TEXT NOT NULL,
    why_stage TEXT NOT NULL,
    confidence_explanation TEXT NOT NULL,
    full_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Unified full-text search index across OCR text, materials, and reasoning.
-- content_type in ('ocr_page', 'material', 'reasoning'); content_id points
-- back to the source row id in the corresponding table for traceability.
CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    content,
    content_type,
    content_id UNINDEXED,
    project_id UNINDEXED,
    document_name UNINDEXED,
    page_number UNINDEXED
);
"""


def init_db() -> None:
    conn = sqlite3.connect(str(settings.DATABASE_PATH))
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(settings.DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def index_for_search(
    conn: sqlite3.Connection,
    content: str,
    content_type: str,
    content_id: int,
    project_id: int,
    document_name: str = "",
    page_number: int | None = None,
) -> None:
    """Insert a row into the unified FTS5 search index. Called by services
    whenever OCR text, materials, or reasoning traces are persisted."""
    if not content:
        return
    conn.execute(
        "INSERT INTO search_index (content, content_type, content_id, project_id, document_name, page_number) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (content, content_type, content_id, project_id, document_name, page_number),
    )