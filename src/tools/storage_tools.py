"""SQLite storage helpers using sqlite-utils.

Schema:
  documents   — one row per document (id, title, url, local_path, source, date, notes, status)
  entities    — extracted people, orgs, locations
  relationships — edges between entities
"""

from __future__ import annotations
from typing import List, Optional

import json
import sqlite_utils
from pathlib import Path

from src.models.document import Document
from src.models.entity import Entity
from src.models.relationship import Relationship


DB_PATH = Path(__file__).parent.parent.parent / "data" / "epstein.db"


def get_db() -> sqlite_utils.Database:
    db = sqlite_utils.Database(DB_PATH)
    _ensure_schema(db)
    return db


def _ensure_schema(db: sqlite_utils.Database) -> None:
    if "documents" not in db.table_names():
        db["documents"].create({
            "id": str,
            "title": str,
            "url": str,
            "local_path": str,
            "source": str,
            "date": str,
            "notes": str,
            "status": str,
        }, pk="id")

    if "entities" not in db.table_names():
        db["entities"].create({
            "id": str,
            "name": str,
            "aliases": str,   # JSON list
            "entity_type": str,
            "role": str,
            "description": str,
        }, pk="id")

    if "relationships" not in db.table_names():
        db["relationships"].create({
            "id": int,
            "from_id": str,
            "to_id": str,
            "rel_type": str,
            "tie_strength": str,
            "doc_id": str,
            "date": str,
            "context": str,
        }, pk="id")


# ── Documents ────────────────────────────────────────────────────────────────

def upsert_document(doc: Document) -> None:
    db = get_db()
    db["documents"].upsert(doc.model_dump(), pk="id")


def get_document(doc_id: str) -> Document | None:
    db = get_db()
    row = db["documents"].get(doc_id) if doc_id in [r["id"] for r in db["documents"].rows] else None
    return Document(**row) if row else None


def list_documents(status: Optional[str] = None) -> List[Document]:
    db = get_db()
    rows = db["documents"].rows_where("status = ?", [status]) if status else db["documents"].rows
    return [Document(**r) for r in rows]


def set_document_status(doc_id: str, status: str) -> None:
    db = get_db()
    db["documents"].update(doc_id, {"status": status})


# ── Entities ─────────────────────────────────────────────────────────────────

def upsert_entity(entity: Entity) -> None:
    db = get_db()
    row = entity.model_dump()
    row["aliases"] = json.dumps(entity.aliases)
    db["entities"].upsert(row, pk="id")


def get_entity(entity_id: str) -> Entity | None:
    db = get_db()
    try:
        row = db["entities"].get(entity_id)
        row["aliases"] = json.loads(row["aliases"] or "[]")
        return Entity(**row)
    except Exception:
        return None


def list_entities() -> List[Entity]:
    db = get_db()
    result = []
    for row in db["entities"].rows:
        row["aliases"] = json.loads(row["aliases"] or "[]")
        result.append(Entity(**row))
    return result


# ── Relationships ─────────────────────────────────────────────────────────────

def insert_relationship(rel: Relationship) -> None:
    db = get_db()
    db["relationships"].insert(rel.model_dump(exclude={"id"}), ignore=True)


def list_relationships(doc_id: Optional[str] = None) -> List[Relationship]:
    db = get_db()
    if doc_id:
        rows = db["relationships"].rows_where("doc_id = ?", [doc_id])
    else:
        rows = db["relationships"].rows
    return [Relationship(**{k: v for k, v in r.items() if k != "id"}) for r in rows]


def relationship_exists(from_id: str, to_id: str, rel_type: str, doc_id: str) -> bool:
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) FROM relationships WHERE from_id=? AND to_id=? AND rel_type=? AND doc_id=?",
        [from_id, to_id, rel_type, doc_id]
    ).fetchone()[0]
    return count > 0
