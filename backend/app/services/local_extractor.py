"""Small, reused helper functions shared across services."""
import re


def make_snippet(text: str, match_start: int, match_end: int, context: int = 60) -> str:
    """Return a short window of text around a match span, used as the
    'evidence' field so every material can be traced back to its exact
    source context."""
    start = max(0, match_start - context)
    end = min(len(text), match_end + context)
    snippet = text[start:end].strip()
    snippet = re.sub(r"\s+", " ", snippet)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    """Split text into chunks under a character budget, breaking on
    paragraph/line boundaries where possible. Used to control LLM token
    spend (see COST OPTIMIZATION in the product spec) instead of sending
    whole documents to GPT-4o."""
    if len(text) <= max_chars:
        return [text] if text.strip() else []

    chunks = []
    paragraphs = text.split("\n")
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > max_chars:
            if current.strip():
                chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks


def clamp_confidence(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)