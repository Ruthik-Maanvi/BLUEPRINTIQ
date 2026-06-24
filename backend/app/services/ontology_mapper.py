"""
Deterministic construction ontology mapper.

This is the core of the NO FAKE INTELLIGENCE rule: materials are detected by
matching real extracted document text against a known ontology of
construction materials (app/data/ontology.json), NOT by asking an LLM to
hallucinate a plausible-sounding material list. The LLM (gpt_analyzer.py) is
used only as an optional *enhancement* layer on top of this deterministic
pass -- never as a replacement for it. See docs/decisions.md.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.utils.helpers import make_snippet

# CHANGE THIS LINE:
ONTOLOGY_PATH = Path(__file__).resolve().parents[1] / "data" / "construction_ontology.json"


@dataclass
class OntologyMatch:
    material_name: str
    category: str
    primary_stage: str
    secondary_stage: str | None
    unit_hint: str | None
    matched_alias: str
    match_type: str  # 'canonical' | 'alias'
    evidence: str
    occurrence_count: int


class OntologyMapper:
    def __init__(self, ontology_path: Path = ONTOLOGY_PATH):
        with open(ontology_path, "r") as f:
            data = json.load(f)
        self.stage_order: list[str] = data["stages_order"]
        self.entries: list[dict] = data["materials"]
        # Pre-compile one regex per alias for fast, word-boundary-safe matching.
        self._compiled: list[tuple[dict, str, re.Pattern]] = []
        for entry in self.entries:
            for alias in entry["aliases"]:
                pattern = re.compile(
                    r"(?<![a-zA-Z0-9])" + re.escape(alias) + r"(?![a-zA-Z0-9])",
                    re.IGNORECASE,
                )
                self._compiled.append((entry, alias, pattern))

    def match_text(self, text: str) -> list[OntologyMatch]:
        """Scan a block of text (one OCR page, one chunk) for ontology
        material mentions. Returns one OntologyMatch per distinct material
        found, with the first occurrence's surrounding text as evidence."""
        if not text:
            return []

        matches_by_material: dict[str, OntologyMatch] = {}
        for entry, alias, pattern in self._compiled:
            found = list(pattern.finditer(text))
            if not found:
                continue
            material_name = entry["material_name"]
            first = found[0]
            evidence = make_snippet(text, first.start(), first.end())
            match_type = "canonical" if alias == entry["aliases"][0] else "alias"

            existing = matches_by_material.get(material_name)
            if existing is None or len(found) > existing.occurrence_count:
                matches_by_material[material_name] = OntologyMatch(
                    material_name=material_name,
                    category=entry["category"],
                    primary_stage=entry["primary_stage"],
                    secondary_stage=entry.get("secondary_stage"),
                    unit_hint=entry.get("unit_hint"),
                    matched_alias=alias,
                    match_type=match_type,
                    evidence=evidence,
                    occurrence_count=len(found),
                )
        return list(matches_by_material.values())

    def match_strength(self, match: OntologyMatch) -> float:
        """Base confidence contribution from the ontology match itself,
        before OCR/LLM signals are blended in (see reasoning_engine.py)."""
        base = 0.90 if match.match_type == "canonical" else 0.80
        frequency_bonus = min(0.08, 0.02 * (match.occurrence_count - 1))
        return round(min(1.0, base + frequency_bonus), 2)

    def find_entry(self, material_name: str) -> dict | None:
        for entry in self.entries:
            if entry["material_name"] == material_name:
                return entry
        return None


_mapper_singleton: OntologyMapper | None = None


def get_ontology_mapper() -> OntologyMapper:
    global _mapper_singleton
    if _mapper_singleton is None:
        _mapper_singleton = OntologyMapper()
    return _mapper_singleton