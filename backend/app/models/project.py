"""Repository functions for `projects` and `documents` tables.

Kept as plain functions over raw SQL (see core/database.py for the
rationale) rather than an ORM class hierarchy -- this is the data-access
layer the original folder structure calls `models/`.
"""
import sqlite3


def create_project(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.execute("INSERT INTO projects (name) VALUES (?)", (name,))
    return cur.lastrowid


def get_project(conn: sqlite3.Connection, project_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()


def list_projects(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()


def update_project_status(conn: sqlite3.Connection, project_id: int, status: str) -> None:
    conn.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))


def create_document(
    conn: sqlite3.Connection,
    project_id: int,
    filename: str,
    filepath: str,
    content_type: str | None,
    document_type: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO documents (project_id, filename, filepath, content_type, document_type, ocr_status) "
        "VALUES (?, ?, ?, ?, ?, 'pending')",
        (project_id, filename, filepath, content_type, document_type),
    )
    return cur.lastrowid


def get_document(conn: sqlite3.Connection, document_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM documents WHERE id = ?", (document_id,)
    ).fetchone()


def list_documents_for_project(
    conn: sqlite3.Connection, project_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM documents WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()


def update_document_ocr_status(
    conn: sqlite3.Connection,
    document_id: int,
    status: str,
    engine_used: str | None = None,
    page_count: int | None = None,
    note: str | None = None,
) -> None:
    conn.execute(
        "UPDATE documents SET ocr_status = ?, ocr_engine_used = COALESCE(?, ocr_engine_used), "
        "page_count = COALESCE(?, page_count), ocr_note = ? WHERE id = ?",
        (status, engine_used, page_count, note, document_id),
    )