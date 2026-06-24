"""
Reasoning and Confidence Synthesis Engine.

Implements the core Explainability Requirement (What / Where / Why-Category / 
Why-Stage / Confidence) and the mathematically blended Confidence Framework.
All inputs to this module are derived from upstream extraction stages to 
guarantee 100% deterministic traceability and prevent AI hallucination.
"""
from app.core.config import get_settings

settings = get_settings()

def compute_confidence(
    ontology_match_strength: float | None,
    ocr_confidence: float | None,
    llm_confidence: float | None,
) -> tuple[float, str]:
    """
    Dynamically calculates a weighted confidence matrix from available pipeline signals.
    Normalizes weights if a signal is missing (e.g., graceful LLM degradation) 
    to ensure the final score is mathematically grounded and never guessed.
    """
    # Strongly typed list to hold available scoring signals
    components: list[tuple[float, float, str]] = []
    
    if ontology_match_strength is not None:
        components.append((ontology_match_strength, settings.WEIGHT_ONTOLOGY_MATCH, "Ontology Match"))
    if ocr_confidence is not None:
        components.append((ocr_confidence, settings.WEIGHT_OCR_CONFIDENCE, "Native Extraction"))
    if llm_confidence is not None:
        components.append((llm_confidence, settings.WEIGHT_LLM_CONFIDENCE, "LLM Verification"))

    total_weight = sum(weight for _, weight, _ in components)
    
    # Fallback if all extraction confidence signals fail or are stripped
    if total_weight == 0.0:
        return 0.5, "No confidence signals available; defaulting to baseline isolation midpoint."

    # Compute the weighted average and clamp precisely between 0.0 and 1.0
    score = sum(value * weight for value, weight, _ in components) / total_weight
    score = round(max(0.0, min(1.0, score)), 2)

    # Generate the transparent audit matrix string
    parts = ", ".join(f"{label} = {v:.2f} (Weight {w/total_weight:.0%})" for v, w, label in components)
    explanation = f"Blended Matrix: [{parts}]. Final Grounded Score = {score:.2f}."
    
    return score, explanation


def generate_reasoning(
    material_name: str,
    category: str,
    primary_stage: str,
    secondary_stage: str | None,
    document_name: str,
    page_number: int | None,
    evidence: str,
    extraction_method: str,
    confidence: float,
    confidence_explanation: str,
    matched_alias: str,
) -> dict:
    """
    Constructs the fully traceable audit log for the frontend payload and persistence layer.
    
    NOTE: The return dictionary is strictly mapped to the exact **kwargs expected 
    by the SQLAlchemy `create_reasoning_trace()` schema to prevent backend crashes.
    """
    page_str = f"Page {page_number}" if page_number else "an unspecified layout"

    what_detected = (
        f"Detected '{material_name}' mapped from the raw blueprint text alias '{matched_alias}'."
    )
    
    where_detected = (
        f"Anchored in document '{document_name}', {page_str}. Source Evidence: \"{evidence}\"."
        if evidence else f"Anchored in document '{document_name}', {page_str}. Source Evidence unavailable."
    )
    
    why_category = (
        f"Categorized as '{category}' by the deterministic construction taxonomy "
        f"(construction_ontology.json)."
    )
    
    secondary_str = f" (Secondary: '{secondary_stage}')" if secondary_stage else ""
    why_stage = (
        f"Routed to primary procurement stage '{primary_stage}'{secondary_str} "
        f"based on hardcoded staging taxonomy rules."
    )

    full_text = (
        f"{what_detected} {where_detected} {why_category} {why_stage} "
        f"System Confidence: {confidence:.2f}. {confidence_explanation} "
        f"(Extraction Engine: {extraction_method})."
    )

    # STRICT DICTIONARY RETURN: Do not add extra keys here without updating the DB schema
    return {
        "what_detected": what_detected,
        "where_detected": where_detected,
        "why_category": why_category,
        "why_stage": why_stage,
        "confidence_explanation": confidence_explanation,
        "full_text": full_text,
    }