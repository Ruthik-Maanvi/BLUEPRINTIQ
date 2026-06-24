from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    project_id: int
    filename: str
    content_type: str | None
    page_count: int
    ocr_status: str
    uploaded_at: str


class ProjectOut(BaseModel):
    id: int
    name: str
    status: str
    created_at: str
    documents: list[DocumentOut] = []


class UploadResponse(BaseModel):
    project: ProjectOut
    message: str