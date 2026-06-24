from pydantic import BaseModel
from app.schemas.material import Material


class ProcurementStageGroup(BaseModel):
    stage: str
    order: int
    item_count: int
    materials: list[Material]


class ProcurementPlan(BaseModel):
    project_id: int
    stages: list[ProcurementStageGroup]


class SearchResultItem(BaseModel):
    content_type: str  # 'ocr_page' | 'material' | 'reasoning'
    content_id: int
    project_id: int | None = None
    snippet: str
    document_name: str | None = None
    page_number: int | None = None
    score: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]


class AskRequest(BaseModel):
    project_id: int
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    citations: list[SearchResultItem]
    note: str | None = None