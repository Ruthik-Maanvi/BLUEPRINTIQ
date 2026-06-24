from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import os
import shutil
from app.core.database import get_db_connection # Assumes your standard SQLite connector

router = APIRouter(prefix="/api", tags=["Upload"])

UPLOAD_DIR = os.path.abspath("uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadResponse(BaseModel):
    project_id: str
    message: str
    files_uploaded: list[str]

@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks, 
    files: list[UploadFile] = File(...)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
        
    project_id = str(uuid.uuid4())
    uploaded_filenames = []
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Initialize the project tracking row
            cursor.execute(
                "INSERT INTO projects (id, status, created_at) VALUES (?, ?, datetime('now'))",
                (project_id, "Uploaded")
            )
            
            for file in files:
                # Sanitize filename and define paths
                safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
                file_path = os.path.join(UPLOAD_DIR, safe_filename)
                
                # Stream file to local storage
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Record individual document asset
                cursor.execute(
                    "INSERT INTO documents (id, project_id, filename, file_path, status) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), project_id, file.filename, file_path, "Pending")
                )
            conn.commit()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write failure during upload: {str(e)}")

    return UploadResponse(
        project_id=project_id,
        message="Documents successfully saved. Project context initialized.",
        files_uploaded=[f.filename for f in files]
    )