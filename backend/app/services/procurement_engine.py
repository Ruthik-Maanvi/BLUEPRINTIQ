"""
Procurement engine.

Per the PROCUREMENT ENGINE REQUIREMENT: stage assignment is decided by the
deterministic ontology mapping (see services/ontology_mapper.py); GPT-4o may
suggest additional materials but never overrides a stage that the ontology
already determined. This module's job is purely to organize already-decided
materials into an ordered, stage-grouped procurement plan for the API and UI.
"""
import sqlite3

from app.services.ontology_mapper import get_ontology_mapper


def build_procurement_plan(materials_rows: list[sqlite3.Row]) -> list[dict]:
    mapper = get_ontology_mapper()
    stage_order = mapper.stage_order

    grouped: dict[str, list[sqlite3.Row]] = {stage: [] for stage in stage_order}
    for row in materials_rows:
        stage = row["procurement_stage"]
        if stage not in grouped:
            grouped[stage] = []  # LLM-suggested stage outside the 8 canonical ones
        grouped[stage].append(row)

    plan = []
    ordered_stage_names = stage_order + [s for s in grouped if s not in stage_order]
    for idx, stage in enumerate(ordered_stage_names):
        rows = grouped.get(stage, [])
        plan.append(
            {
                "stage": stage,
                "order": idx + 1,
                "item_count": len(rows),
                "materials": rows,
            }
        )
    return plan