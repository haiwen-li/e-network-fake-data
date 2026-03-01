from __future__ import annotations
from typing import List
from pydantic import BaseModel, field_validator
import re


ENTITY_TYPES = {"person", "organization", "location", "vessel"}
ROLES = {"politician", "businessman", "royal", "socialite", "legal", "ngo", "media", "other"}


class Entity(BaseModel):
    id: str                        # URL-safe slug, e.g. "jeffrey-epstein"
    name: str
    aliases: List[str] = []
    entity_type: str = "person"    # person | organization | location | vessel
    role: str = "other"            # politician | businessman | royal | socialite | legal | ngo | media | other
    description: str = ""

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        return re.sub(r"[^a-z0-9-]", "-", v.lower().strip())

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        v = v.lower()
        return v if v in ENTITY_TYPES else "person"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.lower()
        return v if v in ROLES else "other"
