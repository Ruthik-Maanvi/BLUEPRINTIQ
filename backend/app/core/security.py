"""
Application Boundary Security and Ingestion Validation.

Hardens the single untrusted edge of the system (document uploads) by enforcing 
strict extension validation, payload size ceilings, and path-traversal mitigation.
"""
import re
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.core.config import get_settings

settings = get_settings()

# Strictly enforced whitelist for supported document and image formats
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

def sanitize_filename(filename: str) -> str:
    """
    Neutralizes path-traversal vectors by stripping directory structures and 
    unsafe characters, anchoring the file safely within the execution directory.
    """
    safe_name = Path(filename).name
    
    # Restrict to alphanumerics, dots, underscores, and hyphens
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)
    
    if safe_name.startswith(".") or not safe_name:
        return "unnamed_upload"
        
    return safe_name

def validate_upload(file: UploadFile) -> str:
    """
    Executes validation on incoming file uploads.
    Rejects unauthorized file types before disk persistence.
    """
    safe_name = sanitize_filename(file.filename or "upload")
    ext = Path(safe_name).suffix.lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unauthorized file format '{ext}'. "
                f"Boundary configured to accept: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )
    return safe_name

def enforce_size_limit(num_bytes: int) -> None:
    """
    Protects downstream extraction pipelines (Docling / Local OCR) 
    from memory exhaustion by enforcing a hard termination ceiling on incoming payload bytes.
    """
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if num_bytes > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Payload rejected. Stream exceeds the {settings.MAX_UPLOAD_MB}MB safety limit.",
        )