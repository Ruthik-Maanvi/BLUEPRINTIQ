"""
Search architecture (see product spec, SEARCH ARCHITECTURE section):

Stage 1 -- SQLite FTS5 retrieval across OCR text, materials, and reasoning
           traces (the unified `search_index` virtual table).
Stage 2 -- GPT-4o synthesizes a grounded answer using ONLY the retrieved
           rows. If GPT-4o is not configured, the raw retrieved evidence is
           returned directly instead of a synthesized answer -- never a
           fabricated one.
"""
import re

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_connection
from app.models import project as project_repo
from app.schemas.procurement import AskRequest, AskResponse, SearchResponse, SearchResultItem
from app.services import gpt_analyzer
from app.services.gpt_analyzer import LLMNotConfigured
from app.utils.logger import get_logger

router = APIRouter(tags=["search"])
logger = get_logger(__name__)

DEFAULT_LIMIT = 15


def _sanitize_fts_query(raw: str) -> str:
    """Turn a free-text query into a safe FTS5 MATCH expression: each
    alphanumeric token is quoted (so hyphens/punctuation in the input can't
    break FTS5 syntax) and joined with OR for maximum recall; ranking by
    bm25 then surfaces the most relevant rows first."""
    tokens = re.findall(r"[A-Za-z0-9]+", raw)
    if not tokens:
        return '""'
    return " OR ".join(f'"{t}"' for t in tokens)


def _run_search(query: str, project_id: int | None, limit: int = DEFAULT_LIMIT) -> list[dict]:
    fts_query = _sanitize_fts_query(query)
    sql = (
        "SELECT content, content_type, content_id, project_id, document_name, page_number, "
        "bm25(search_index) AS score "
        "FROM search_index WHERE search_index MATCH ?"
    )
    params: list = [fts_query]
    if project_id is not None:
        sql += " AND project_id = ?"
        params.append(project_id)
    sql += " ORDER BY score ASC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _truncate(text: str, max_len: int = 280) -> str:
    text = text or ""
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., min_length=1), project_id: int | None = None, limit: int = DEFAULT_LIMIT):
    rows = _run_search(q, project_id, limit)
    results = [
        SearchResultItem(
            content_type=r["content_type"],
            content_id=r["content_id"],
            project_id=r["project_id"],
            snippet=_truncate(r["content"]),
            document_name=r["document_name"],
            page_number=r["page_number"],
            score=round(r["score"], 3) if r["score"] is not None else None,
        )
        for r in rows
    ]
    return SearchResponse(query=q, results=results)


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    with get_connection() as conn:
        if project_repo.get_project(conn, payload.project_id) is None:
            raise HTTPException(status_code=404, detail=f"Project {payload.project_id} not found.")

    rows = _run_search(payload.question, payload.project_id, limit=10)

    if not rows:
        return AskResponse(
            question=payload.question,
            answer="Evidence unavailable: nothing in this project's uploaded documents or analysis matched the question.",
            grounded=False,
            citations=[],
        )

    citations = [
        SearchResultItem(
            content_type=r["content_type"],
            content_id=r["content_id"],
            project_id=r["project_id"],
            snippet=_truncate(r["content"]),
            document_name=r["document_name"],
            page_number=r["page_number"],
            score=round(r["score"], 3) if r["score"] is not None else None,
        )
        for r in rows
    ]

    try:
        synthesis = gpt_analyzer.synthesize_answer(payload.question, rows)
        used_indices = synthesis.get("used_record_indices", [])
        used_citations = [citations[i] for i in used_indices if 0 <= i < len(citations)] or citations
        return AskResponse(
            question=payload.question,
            answer=synthesis.get("answer", "Evidence unavailable."),
            grounded=bool(synthesis.get("grounded", False)),
            citations=used_citations,
        )
    except LLMNotConfigured:
        return AskResponse(
            question=payload.question,
            answer=(
                "LLM synthesis is unavailable because OPENAI_API_KEY is not configured. "
                "Showing the raw matched evidence from the project knowledge base instead."
            ),
            grounded=False,
            citations=citations,
            note="Set OPENAI_API_KEY in backend/.env to enable synthesized, grounded answers.",
        )
    except Exception as exc:  # pragma: no cover - network/API errors
        logger.warning("GPT-4o ask synthesis failed: %s", exc)
        return AskResponse(
            question=payload.question,
            answer="LLM synthesis failed. Showing the raw matched evidence from the project knowledge base instead.",
            grounded=False,
            citations=citations,
            note=str(exc),
        )