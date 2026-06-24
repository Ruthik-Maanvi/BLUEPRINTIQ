"""
BlueprintIQ FastAPI Application Entrypoint.

Initializes the ASGI server, binds CORS policies, provisions the local 
persistence database, and mounts the routing modules. Utilizes modern 
FastAPI lifespan contexts for safe execution tracking.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, health, search, upload
from app.core.config import get_settings
from app.core.database import init_db
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Executes database initialization and extraction pipeline readiness checks 
    before the server accepts incoming traffic.
    """
    # --- Boot Sequence ---
    init_db()
    logger.info(f"Booting {settings.APP_NAME} Core Engine...")
    
    # 1. Verify Local Vision Capability (Fixes the crash)
    if settings.vision_fallback_configured:
        logger.info(f"Local Vision Fallback [ACTIVE]: Engine mapped to {settings.VISION_ENGINE_TYPE.upper()}")
    else:
        logger.info("Local Vision Fallback [INACTIVE]: Running strictly in native-text layout mode.")

    # 2. Verify Reasoning LLM Capability
    if settings.llm_configured:
        logger.info(f"LLM Reasoning Engine [ACTIVE]: Target model {settings.OPENAI_MODEL}")
    else:
        logger.warning("LLM Reasoning Engine [MISSING]: Falling back to pure deterministic ontology matching.")

    logger.info("BlueprintIQ backend is ready to accept traffic.")
    
    yield  # Server is running
    
    # --- Teardown Sequence ---
    logger.info("Shutting down BlueprintIQ engine...")

# Instantiate the FastAPI core
app = FastAPI(
    title=settings.APP_NAME,
    description="Construction Intelligence API: Native Extraction -> Deterministic Ontology -> Traceable Reasoning.",
    version="0.1.0",
    lifespan=lifespan,
)

# Enforce strict Cross-Origin boundary security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router boundaries
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(search.router)

@app.get("/")
def root():
    """Root health probe for deployment verifications."""
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "docs": "/docs",
        "health_check": "/health",
    }