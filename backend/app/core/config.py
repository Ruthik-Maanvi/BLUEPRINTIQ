"""
Enterprise Application Configuration.

Strictly validates global settings and internal processing weights. 
Configures the primary offline extraction pipeline for structured text, 
incorporating an optional local optical character recognition (OCR) fallback 
for non-textual or rasterized engineering drawings.
"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # --- Storage Infrastructure ---
    UPLOAD_DIR: Path = BACKEND_ROOT / "uploads"
    OUTPUT_DIR: Path = BACKEND_ROOT / "outputs"
    DATABASE_PATH: Path = BACKEND_ROOT / "blueprintiq.db"

    # --- Vision & Layout Pipeline (Non-Textual Fallback) ---
    # Optional local optical character recognition for scanned documents 
    # and image-based engineering artifacts.
    ENABLE_LOCAL_VISION_FALLBACK: bool = False
    VISION_ENGINE_TYPE: str = "paddleocr" 
    
    @property
    def vision_fallback_configured(self) -> bool:
        return self.ENABLE_LOCAL_VISION_FALLBACK and bool(self.VISION_ENGINE_TYPE)

    # --- Reasoning & Synthesis Engine (LLM) ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    @property
    def llm_configured(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    # --- Internal Confidence Blending Weights ---
    # Mathematical thresholds used by the reasoning engine to grade extraction fidelity.
    WEIGHT_ONTOLOGY_MATCH: float = 0.60
    WEIGHT_OCR_CONFIDENCE: float = 0.20
    WEIGHT_LLM_CONFIDENCE: float = 0.20

    # --- Document Extraction Pipeline (IBM Docling) ---
    # Configured explicitly for high-speed, offline structured text extraction.
    DOCLING_TABLE_MODE: str = "accurate"
    DOCLING_TIMEOUT_SECONDS: int = 300
    
    # IMPLEMENTATION NOTE: Defined as a string rather than a list[str].
    # Bypassing the default Pydantic JSON parser prevents JSONDecodeErrors 
    # when reading environment variables in a Windows execution context.
    DOCLING_OCR_LANG: str = "en"

    # --- Application Security Boundaries ---
    APP_NAME: str = "BlueprintIQ"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    MAX_UPLOAD_MB: int = 50
    LOG_LEVEL: str = "info"

    # Automatically load from .env and ignore stray variables
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton of the validated configuration state."""
    return Settings()