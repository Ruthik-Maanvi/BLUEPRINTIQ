"""Repository functions for the `materials` table."""
import sqlite3


def create_material(
    conn: sqlite3.Connection,
    project_id: int,
    document_id: int,
    material_name: str,
    category: str,
    procurement_stage: str,
    secondary_stage: str | None,
    quantity: float | None,
    unit: str | None,
    confidence: float,
    evidence: str,
    source_document: str,
    source_page: int | None,
    extraction_method: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO materials (
            project_id, document_id, material_name, category, procurement_stage,
            secondary_stage, quantity, unit, confidence, evidence,
            source_document, source_page, extraction_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id, document_id, material_name, category, procurement_stage,
            secondary_stage, quantity, unit, confidence, evidence,
            source_document, source_page, extraction_method,
        ),
    )
    return cur.lastrowid


def list_materials_for_project(
    conn: sqlite3.Connection, project_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM materials WHERE project_id = ? ORDER BY procurement_stage, material_name",
        (project_id,),
    ).fetchall()


def get_material(conn: sqlite3.Connection, material_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM materials WHERE id = ?", (material_id,)
    ).fetchone()


def materials_grouped_by_stage(
    conn: sqlite3.Connection, project_id: int, stage_order: list[str]
) -> dict[str, list[sqlite3.Row]]:
    rows = list_materials_for_project(conn, project_id)
    grouped: dict[str, list[sqlite3.Row]] = {stage: [] for stage in stage_order}
    for row in rows:
        stage = row["procurement_stage"]
        grouped.setdefault(stage, [])
        grouped[stage].append(row)
    return grouped