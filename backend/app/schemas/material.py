from pydantic import BaseModel, Field


class Material(BaseModel):
    """Matches the OUTPUT CONTRACT defined in the product spec exactly,
    with `secondary_stage` and `id`/`extraction_method` as justified
    traceability extensions."""

    id: int
    material_name: str
    category: str
    procurement_stage: str
    secondary_stage: str | None = None
    quantity: float | None = None
    unit: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    source_document: str
    source_page: int | None = None
    extraction_method: str


class ReasoningTrace(BaseModel):
    id: int
    material_id: int
    what_detected: str
    where_detected: str
    why_category: str
    why_stage: str
    confidence_explanation: str
    full_text: str


class MaterialWithReasoning(Material):
    reasoning: ReasoningTrace | None = None