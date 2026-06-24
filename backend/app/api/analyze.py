"""
Analysis pipeline orchestration + read endpoints for analysis results.

Pipeline:
  documents -> OCR (IBM Docling Local Deep Learning) -> ontology matching
  -> optional GPT-4o enhancement -> confidence blending -> reasoning
  generation -> SQLite persistence (+ FTS5 indexing) -> read via GET endpoints.

Processing is synchronous. Extraction relies entirely on the local IBM Docling
ML stack. If document conversion fails (e.g., malformed PDF, missing torch
weights), the pipeline explicitly logs the underlying Docling exception to the 
database so the user sees the exact extraction failure reason.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.database import get_connection, index_for_search
from app.models import analysis as analysis_repo
from app.models import material as material_repo
from app.models import project as project_repo
from app.schemas.material import Material, MaterialWithReasoning, ReasoningTrace
from app.schemas.procurement import ProcurementPlan, ProcurementStageGroup
from app.schemas.upload import DocumentOut, ProjectOut
from app.services import gpt_analyzer
from app.services.gpt_analyzer import LLMNotConfigured
from app.services.ontology_mapper import get_ontology_mapper
from app.services.procurement_engine import build_procurement_plan
from app.services.reasoning_engine import compute_confidence, generate_reasoning
from app.utils.helpers import chunk_text
from app.utils.logger import get_logger

# --- IMPORT THE NEW PURE IBM DOCLING EXTRACTOR ---
from app.services.document_extractor import (
    analyze_document,
    DoclingNotAvailable,
    DoclingExtractionError
)

router = APIRouter(tags=["analyze"])
logger = get_logger(__name__)
mapper = get_ontology_mapper()


# ---------------------------------------------------------------------------
# Row -> schema helpers
# ---------------------------------------------------------------------------

def _material_row_to_schema(row) -> Material:
    return Material(
        id=row["id"],
        material_name=row["material_name"],
        category=row["category"],
        procurement_stage=row["procurement_stage"],
        secondary_stage=row["secondary_stage"],
        quantity=row["quantity"],
        unit=row["unit"],
        confidence=row["confidence"],
        evidence=row["evidence"],
        source_document=row["source_document"],
        source_page=row["source_page"],
        extraction_method=row["extraction_method"],
    )


def _reasoning_row_to_schema(row) -> ReasoningTrace:
    return ReasoningTrace(
        id=row["id"],
        material_id=row["material_id"],
        what_detected=row["what_detected"],
        where_detected=row["where_detected"],
        why_category=row["why_category"],
        why_stage=row["why_stage"],
        confidence_explanation=row["confidence_explanation"],
        full_text=row["full_text"],
    )


VALID_STAGES = set(mapper.stage_order)


def _validate_stage(stage: str | None) -> str:
    if stage in VALID_STAGES:
        return stage
    return "Finishing"  # conservative default for an unrecognized LLM-suggested stage


# ---------------------------------------------------------------------------
# POST /analyze/{project_id}
# ---------------------------------------------------------------------------

@router.post("/analyze/{project_id}")
def analyze_project(project_id: int):
    with get_connection() as conn:
        project_row = project_repo.get_project(conn, project_id)
        if project_row is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

        documents = project_repo.list_documents_for_project(conn, project_id)
        if not documents:
            raise HTTPException(status_code=400, detail="Project has no uploaded documents to analyze.")

        results_summary = []

        for doc in documents:
            filepath = Path(doc["filepath"])
            if not filepath.exists():
                project_repo.update_document_ocr_status(
                    conn, doc["id"], "failed", note="Source file missing on disk."
                )
                results_summary.append({"document": doc["filename"], "status": "failed", "reason": "file missing"})
                continue

            # --- Pure IBM Docling Extraction Pass ---
            try:
                pages = analyze_document(filepath)
                # If we get here, extraction worked. Method string will be inside the page objects.
            except (DoclingNotAvailable, DoclingExtractionError) as exc:
                logger.error("Docling extraction failed for %s: %s", doc["filename"], exc)
                # Persist the EXACT docling error to DB per the architectural rule
                project_repo.update_document_ocr_status(
                    conn, doc["id"], "failed", note=f"Docling error: {exc}"
                )
                results_summary.append({"document": doc["filename"], "status": "failed", "reason": str(exc)})
                continue
            except Exception as exc:
                logger.error("Unexpected error during local extraction for %s: %s", doc["filename"], exc)
                project_repo.update_document_ocr_status(
                    conn, doc["id"], "failed", note=f"Unexpected extraction error: {exc}"
                )
                results_summary.append({"document": doc["filename"], "status": "failed", "reason": str(exc)})
                continue

            materials_found = 0
            engine_label = "ibm_docling" # Setting a clean label for the DB tracker

            for page in pages:
                page_number = page["page_number"]
                page_text = page["text"] or ""
                page_confidence = page["confidence"]
                page_method = page["method"]  # Provided natively by _extract_page_content ("docling" or "docling_partial")

                ocr_page_id = analysis_repo.create_ocr_page(
                    conn, doc["id"], page_number, page_text, page.get("tables", []), page_confidence
                )
                index_for_search(
                    conn, page_text, "ocr_page", ocr_page_id, project_id, doc["filename"], page_number
                )

                if not page_text.strip():
                    continue

                # --- Deterministic ontology pass (primary signal) ---
                ontology_matches = mapper.match_text(page_text)
                detected_names_this_page = []
                
                for match in ontology_matches:
                    detected_names_this_page.append(match.material_name)
                    ontology_strength = mapper.match_strength(match)
                    confidence, conf_explanation = compute_confidence(
                        ontology_match_strength=ontology_strength,
                        ocr_confidence=page_confidence,
                        llm_confidence=None,
                    )
                    
                    extraction_method = f"ontology_deterministic+{page_method}"

                    material_id = material_repo.create_material(
                        conn,
                        project_id=project_id,
                        document_id=doc["id"],
                        material_name=match.material_name,
                        category=match.category,
                        procurement_stage=match.primary_stage,
                        secondary_stage=match.secondary_stage,
                        quantity=None,  # Ontology matches do not extract quantity directly
                        unit=match.unit_hint,
                        confidence=confidence,
                        evidence=match.evidence,
                        source_document=doc["filename"],
                        source_page=page_number,
                        extraction_method=extraction_method,
                    )
                    materials_found += 1

                    reasoning = generate_reasoning(
                        material_name=match.material_name,
                        category=match.category,
                        primary_stage=match.primary_stage,
                        secondary_stage=match.secondary_stage,
                        document_name=doc["filename"],
                        page_number=page_number,
                        evidence=match.evidence,
                        extraction_method=extraction_method,
                        confidence=confidence,
                        confidence_explanation=conf_explanation,
                        matched_alias=match.matched_alias,
                    )
                    
                    reasoning_id = analysis_repo.create_reasoning_trace(
                        conn, material_id, project_id, **reasoning
                    )
                    
                    index_for_search(
                        conn, match.evidence, "material", material_id, project_id, doc["filename"], page_number
                    )
                    index_for_search(
                        conn, reasoning["full_text"], "reasoning", reasoning_id, project_id, doc["filename"], page_number
                    )

                # --- Optional GPT-4o enhancement pass (additive only) ---
                try:
                    for chunk in chunk_text(page_text):
                        llm_items = gpt_analyzer.enhance_materials(
                            chunk, detected_names_this_page, doc["filename"]
                        )
                        for item in llm_items:
                            stage = _validate_stage(item.get("procurement_stage"))
                            llm_conf = item.get("confidence")
                            llm_conf = float(llm_conf) if isinstance(llm_conf, (int, float)) else None
                            
                            confidence, conf_explanation = compute_confidence(
                                ontology_match_strength=None,
                                ocr_confidence=page_confidence,
                                llm_confidence=llm_conf,
                            )
                            
                            material_id = material_repo.create_material(
                                conn,
                                project_id=project_id,
                                document_id=doc["id"],
                                material_name=item.get("material_name", "Unspecified material"),
                                category=item.get("category", "Uncategorized"),
                                procurement_stage=stage,
                                secondary_stage=None,
                                quantity=item.get("quantity"),
                                unit=item.get("unit"),
                                confidence=confidence,
                                evidence=item.get("evidence", "Evidence unavailable"),
                                source_document=doc["filename"],
                                source_page=page_number,
                                extraction_method="llm_gpt4o",
                            )
                            materials_found += 1
                            
                            full_text = (
                                f"GPT-4o detected '{item.get('material_name')}' (not in deterministic ontology). "
                                f"Reasoning: {item.get('reasoning', 'n/a')} "
                                f"Evidence: \"{item.get('evidence', 'Evidence unavailable')}\" "
                                f"Confidence: {confidence:.2f}. {conf_explanation}"
                            )
                            
                            reasoning_id = analysis_repo.create_reasoning_trace(
                                conn,
                                material_id,
                                project_id,
                                what_detected=f"GPT-4o identified '{item.get('material_name')}' from document context.",
                                where_detected=f"Document '{doc['filename']}', page {page_number}. Evidence: \"{item.get('evidence', 'Evidence unavailable')}\".",
                                why_category=f"Category '{item.get('category')}' suggested by GPT-4o (no deterministic ontology match).",
                                why_stage=f"Stage '{stage}' suggested by GPT-4o.",
                                confidence_explanation=conf_explanation,
                                full_text=full_text,
                            )
                            
                            index_for_search(
                                conn, item.get("evidence", ""), "material", material_id, project_id, doc["filename"], page_number
                            )
                            index_for_search(
                                conn, full_text, "reasoning", reasoning_id, project_id, doc["filename"], page_number
                            )
                except LLMNotConfigured:
                    pass  # graceful degradation: deterministic-only output stands on its own
                except Exception as exc:
                    logger.warning("GPT-4o enhancement failed for %s page %s: %s", doc["filename"], page_number, exc)

            project_repo.update_document_ocr_status(
                conn, doc["id"], "completed", engine_used=engine_label, page_count=len(pages)
            )
            results_summary.append(
                {"document": doc["filename"], "status": "completed", "pages": len(pages), "materials_found": materials_found}
            )

        project_repo.update_project_status(conn, project_id, "analyzed")

    return {"project_id": project_id, "status": "analyzed", "documents": results_summary}


# ---------------------------------------------------------------------------
# GET /project/{project_id}
# ---------------------------------------------------------------------------

@router.get("/project/{project_id}", response_model=ProjectOut)
def get_project(project_id: int):
    with get_connection() as conn:
        row = project_repo.get_project(conn, project_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
        doc_rows = project_repo.list_documents_for_project(conn, project_id)
    return ProjectOut(
        id=row["id"],
        name=row["name"],
        status=row["status"],
        created_at=row["created_at"],
        documents=[
            DocumentOut(
                id=d["id"], project_id=d["project_id"], filename=d["filename"],
                content_type=d["content_type"], page_count=d["page_count"],
                ocr_status=d["ocr_status"], uploaded_at=d["uploaded_at"],
            )
            for d in doc_rows
        ],
    )


@router.get("/projects")
def list_projects():
    with get_connection() as conn:
        rows = project_repo.list_projects(conn)
    return [{"id": r["id"], "name": r["name"], "status": r["status"], "created_at": r["created_at"]} for r in rows]


# ---------------------------------------------------------------------------
# GET /materials/{project_id}
# ---------------------------------------------------------------------------

@router.get("/materials/{project_id}", response_model=list[Material])
def get_materials(project_id: int):
    with get_connection() as conn:
        if project_repo.get_project(conn, project_id) is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
        rows = material_repo.list_materials_for_project(conn, project_id)
    return [_material_row_to_schema(r) for r in rows]


# ---------------------------------------------------------------------------
# GET /procurement/{project_id}
# ---------------------------------------------------------------------------

@router.get("/procurement/{project_id}", response_model=ProcurementPlan)
def get_procurement_plan(project_id: int):
    with get_connection() as conn:
        if project_repo.get_project(conn, project_id) is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
        rows = material_repo.list_materials_for_project(conn, project_id)

    plan = build_procurement_plan(rows)
    stages = [
        ProcurementStageGroup(
            stage=group["stage"],
            order=group["order"],
            item_count=group["item_count"],
            materials=[_material_row_to_schema(r) for r in group["materials"]],
        )
        for group in plan
    ]
    return ProcurementPlan(project_id=project_id, stages=stages)


# ---------------------------------------------------------------------------
# GET /reasoning/{project_id}
# ---------------------------------------------------------------------------

@router.get("/reasoning/{project_id}", response_model=list[MaterialWithReasoning])
def get_reasoning(project_id: int):
    with get_connection() as conn:
        if project_repo.get_project(conn, project_id) is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
        material_rows = material_repo.list_materials_for_project(conn, project_id)
        reasoning_rows = {
            r["material_id"]: r for r in analysis_repo.list_reasoning_for_project(conn, project_id)
        }

    out = []
    for m in material_rows:
        base = _material_row_to_schema(m).model_dump()
        reasoning_row = reasoning_rows.get(m["id"])
        base["reasoning"] = _reasoning_row_to_schema(reasoning_row) if reasoning_row else None
        out.append(MaterialWithReasoning(**base))
    return out