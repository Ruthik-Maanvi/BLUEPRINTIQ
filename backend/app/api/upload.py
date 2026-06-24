from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.database import get_connection
from app.core.security import enforce_size_limit, validate_upload
from app.models import project as project_repo
from app.schemas.upload import DocumentOut, ProjectOut, UploadResponse
from app.utils.logger import get_logger




# Define the absolute path to the backend/uploads directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"

# Ensure the directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


router = APIRouter(tags=["upload"])
logger = get_logger(__name__)


def _row_to_document_out(row) -> DocumentOut:
    return DocumentOut(
        id=row["id"],
        project_id=row["project_id"],
        filename=row["filename"],
        content_type=row["content_type"],
        page_count=row["page_count"],
        ocr_status=row["ocr_status"],
        uploaded_at=row["uploaded_at"],
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    project_name: str | None = Form(None),
    project_id: int | None = Form(None),
):
    """Accept one or more construction documents. Either pass `project_id`
    to add files to an existing project, or `project_name` to create a new
    one. Files are saved to disk under uploads/{project_id}/ and a
    `documents` row is created for each, in status 'pending' until
    /analyze/{project_id} is called."""
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    settings = get_settings()

    with get_connection() as conn:
        if project_id is not None:
            existing = project_repo.get_project(conn, project_id)
            if existing is None:
                raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
            pid = project_id
        else:
            name = project_name or f"Untitled Project ({len(files)} file(s))"
            pid = project_repo.create_project(conn, name)

        project_dir: Path = settings.UPLOAD_DIR / str(pid)
        project_dir.mkdir(parents=True, exist_ok=True)

        for upload_file in files:
            safe_name = validate_upload(upload_file)
            contents = await upload_file.read()
            enforce_size_limit(len(contents))

            dest_path = project_dir / safe_name
            with open(dest_path, "wb") as f:
                f.write(contents)

            project_repo.create_document(
                conn,
                project_id=pid,
                filename=safe_name,
                filepath=str(dest_path),
                content_type=upload_file.content_type,
            )

        project_row = project_repo.get_project(conn, pid)
        doc_rows = project_repo.list_documents_for_project(conn, pid)

    project_out = ProjectOut(
        id=project_row["id"],
        name=project_row["name"],
        status=project_row["status"],
        created_at=project_row["created_at"],
        documents=[_row_to_document_out(r) for r in doc_rows],
    )
    logger.info("Uploaded %d file(s) to project %d", len(files), pid)
    return UploadResponse(
        project=project_out,
        message=f"{len(files)} file(s) uploaded. Call POST /analyze/{pid} to process them.",
    )