from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator


REL_TYPES = {
    "flew_with", "met_with", "employed", "associated", "accused",
    "funded", "owned_property", "introduced", "communicated", "other"
}
TIE_STRENGTHS = {"strong", "weak"}


class Relationship(BaseModel):
    from_id: str
    to_id: str
    rel_type: str = "associated"    # flew_with | met_with | employed | associated | accused | funded | ...
    tie_strength: str = "strong"    # strong (direct, explicit) | weak (indirect, inferred)
    doc_id: str                     # source document id
    date: Optional[str] = None
    context: str = ""               # verbatim quote or summary from document — shown in hover tooltip

    @field_validator("rel_type")
    @classmethod
    def validate_rel_type(cls, v: str) -> str:
        v = v.lower()
        return v if v in REL_TYPES else "other"

    @field_validator("tie_strength")
    @classmethod
    def validate_tie_strength(cls, v: str) -> str:
        v = v.lower()
        return v if v in TIE_STRENGTHS else "strong"
