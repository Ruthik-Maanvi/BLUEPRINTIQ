"""Repository functions for `ocr_pages` and `reasoning_traces` tables."""
import json
import sqlite3


def create_ocr_page(
    conn: sqlite3.Connection,
    document_id: int,
    page_number: int,
    raw_text: str,
    tables: list,
    ocr_confidence: float,
) -> int:
    cur = conn.execute(
        "INSERT INTO ocr_pages (document_id, page_number, raw_text, tables_json, ocr_confidence) "
        "VALUES (?, ?, ?, ?, ?)",
        (document_id, page_number, raw_text, json.dumps(tables), ocr_confidence),
    )
    return cur.lastrowid


def list_ocr_pages_for_document(
    conn: sqlite3.Connection, document_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM ocr_pages WHERE document_id = ? ORDER BY page_number",
        (document_id,),
    ).fetchall()


def list_ocr_pages_for_project(
    conn: sqlite3.Connection, project_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ocr_pages.*, documents.filename AS document_name
        FROM ocr_pages
        JOIN documents ON documents.id = ocr_pages.document_id
        WHERE documents.project_id = ?
        ORDER BY ocr_pages.document_id, ocr_pages.page_number
        """,
        (project_id,),
    ).fetchall()


def create_reasoning_trace(
    conn: sqlite3.Connection,
    material_id: int,
    project_id: int,
    what_detected: str,
    where_detected: str,
    why_category: str,
    why_stage: str,
    confidence_explanation: str,
    full_text: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO reasoning_traces (
            material_id, project_id, what_detected, where_detected,
            why_category, why_stage, confidence_explanation, full_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            material_id, project_id, what_detected, where_detected,
            why_category, why_stage, confidence_explanation, full_text,
        ),
    )
    return cur.lastrowid


def list_reasoning_for_project(
    conn: sqlite3.Connection, project_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM reasoning_traces WHERE project_id = ? ORDER BY id",
        (project_id,),
    ).fetchall()


def get_reasoning_for_material(
    conn: sqlite3.Connection, material_id: int
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM reasoning_traces WHERE material_id = ?", (material_id,)
    ).fetchone()