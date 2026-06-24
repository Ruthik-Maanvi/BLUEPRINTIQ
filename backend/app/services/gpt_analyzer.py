"""
GPT-4o analysis service.

Per the MODEL CONSTRAINT and NO FAKE INTELLIGENCE rules: GPT-4o is used only
for two narrowly-scoped, strictly-grounded tasks, never as a free-form
generator:

  1. Material enhancement -- given an OCR text chunk and the materials the
     deterministic ontology pass already found, ask GPT-4o to surface
     ADDITIONAL materials/quantities it can see, quoting exact evidence from
     the chunk. Deterministic ontology matches always take priority; this is
     additive only (see PROCUREMENT ENGINE REQUIREMENT: "deterministic
     mapping must take priority").
  2. Grounded Q&A synthesis -- given rows already retrieved from SQLite by
     the search layer, answer the user's question using ONLY those rows.

If OPENAI_API_KEY is not set, both functions raise LLMNotConfigured and
callers fall back to deterministic-only output / raw retrieved evidence,
never to a fabricated answer.
"""
import json

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMNotConfigured(Exception):
    pass


def _get_client():
    settings = get_settings()
    if not settings.llm_configured:
        raise LLMNotConfigured("OPENAI_API_KEY not set in .env")
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise LLMNotConfigured("openai package not installed") from exc
    return OpenAI(api_key=settings.OPENAI_API_KEY), settings.OPENAI_MODEL


MATERIAL_ENHANCEMENT_SYSTEM_PROMPT = """You are a construction document analyst. You will be given:
- a chunk of OCR-extracted text from a construction document
- a list of materials a deterministic system already detected in this chunk

Your job: identify ADDITIONAL construction materials, quantities, or specifications
visible in the text that are NOT already in the detected list. Only report materials
you can directly quote evidence for in the given text. Never invent a material that
isn't textually present. If there is nothing additional, return an empty list.

Respond ONLY with strict JSON in this exact shape, no prose, no markdown fences:
{
  "materials": [
    {
      "material_name": string,
      "category": string,
      "procurement_stage": one of ["Site Preparation","Foundation","Structural Works","Masonry","Roofing","MEP Rough-In","Finishing","External Works"],
      "quantity": number or null,
      "unit": string or null,
      "confidence": number between 0 and 1 (your own certainty),
      "evidence": string (exact short quote, under 25 words, copied from the input text),
      "reasoning": string (one sentence: what you saw and why it implies this material/stage)
    }
  ]
}
"""


def enhance_materials(
    text_chunk: str, already_detected: list[str], document_name: str
) -> list[dict]:
    client, model = _get_client()
    user_prompt = (
        f"Document: {document_name}\n\n"
        f"Already detected materials (do not repeat these): {already_detected}\n\n"
        f"OCR text chunk:\n{text_chunk}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": MATERIAL_ENHANCEMENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1200,
    )
    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        return parsed.get("materials", [])
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("GPT-4o material enhancement returned invalid JSON: %s", exc)
        return []


ASK_SYSTEM_PROMPT = """You are a grounded question-answering assistant for a construction
project knowledge base. You will be given a user question and a numbered list of evidence
records retrieved from a SQL database (OCR text, extracted materials, or reasoning traces).

Rules:
- Answer using ONLY the provided evidence records. Never use outside knowledge.
- Every claim in your answer must be traceable to at least one numbered record.
- If the evidence does not contain enough information to answer, say so plainly
  and set "grounded" to false. Do not guess.

Respond ONLY with strict JSON in this exact shape, no prose, no markdown fences:
{
  "answer": string,
  "grounded": boolean,
  "used_record_indices": [list of integers referencing the numbered records you relied on]
}
"""


def synthesize_answer(question: str, evidence_records: list[dict]) -> dict:
    client, model = _get_client()
    numbered = "\n".join(
        f"[{i}] (source: {r.get('document_name') or 'n/a'}, page: {r.get('page_number') or 'n/a'}, "
        f"type: {r.get('content_type')}): {r.get('content')}"
        for i, r in enumerate(evidence_records)
    )
    user_prompt = f"Question: {question}\n\nEvidence records:\n{numbered}"
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": ASK_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=600,
    )
    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("GPT-4o ask synthesis returned invalid JSON: %s", exc)
        return {"answer": "Evidence unavailable.", "grounded": False, "used_record_indices": []}