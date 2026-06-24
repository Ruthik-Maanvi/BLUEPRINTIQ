from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])




@router.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "vision_fallback_configured": settings.vision_fallback_configured,
        "llm_configured": settings.llm_configured,
    }