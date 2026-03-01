"""Extractor Subagent — uses OpenAI to extract entities and relationships from document text.

For each document with status='text_extracted', it:
  1. Reads the .txt file and splits into chunks
  2. Sends each chunk to gpt-4o-mini with a structured extraction prompt
  3. Parses the JSON response and saves entities + relationships to SQLite
  4. Marks the document as 'processed'
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

import json
import re
from pathlib import Path

from openai import OpenAI
from rich.console import Console

from src.models.entity import Entity
from src.models.relationship import Relationship
from src.tools.pdf_tools import read_text_file, chunk_text
from src.tools.storage_tools import (
    list_documents, upsert_entity, insert_relationship,
    set_document_status, relationship_exists
)

console = Console()

MODEL = "gpt-4o-mini"

EXTRACTION_SYSTEM = """You are an expert at extracting structured information from legal documents.
Given a passage from an Epstein-related court document, extract:

1. ENTITIES: people, organizations, locations, and vessels (boats/planes) mentioned.
2. RELATIONSHIPS: direct connections between entities mentioned in the text.

For each relationship, assess tie strength:
- "strong": explicitly stated direct interaction (flew together, met with, employed, accused)
- "weak": indirect/inferred connection (knew of, associated with, mentioned in same context)

Respond with ONLY valid JSON in this exact format:
{
  "entities": [
    {
      "name": "Full Name",
      "entity_type": "person|organization|location|vessel",
      "role": "politician|businessman|royal|socialite|legal|ngo|media|other",
      "description": "Brief description based on this document",
      "aliases": []
    }
  ],
  "relationships": [
    {
      "from_name": "Entity A",
      "to_name": "Entity B",
      "rel_type": "flew_with|met_with|employed|associated|accused|funded|owned_property|introduced|communicated|other",
      "tie_strength": "strong|weak",
      "date": "YYYY-MM-DD or null",
      "context": "Brief direct quote or paraphrase explaining this relationship from the text (max 200 chars)"
    }
  ]
}

Only extract entities and relationships that are clearly mentioned in the provided text.
Do not infer or hallucinate connections not supported by the text."""


def _name_to_id(name: str) -> str:
    """Convert an entity name to a URL-safe id slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def _extract_from_chunk(client: OpenAI, chunk: str, doc_id: str) -> dict:
    """Extract entities and relationships from a single text chunk."""
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": f"Document ID: {doc_id}\n\nText passage:\n\n{chunk}"},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        console.print(f"[red]JSON parse error for chunk of {doc_id}[/red]")
        return {"entities": [], "relationships": []}


def _save_extraction(data: dict, doc_id: str) -> Tuple[int, int]:
    """Save extracted entities and relationships; return (entity_count, rel_count)."""
    entity_count = 0
    rel_count = 0

    # Map from extracted name → slug id (for relationship resolution)
    name_to_id: Dict[str, str] = {}

    for e_data in data.get("entities", []):
        name = e_data.get("name", "").strip()
        if not name or len(name) < 2:
            continue
        entity_id = _name_to_id(name)
        name_to_id[name.lower()] = entity_id
        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=e_data.get("entity_type", "person"),
            role=e_data.get("role", "other"),
            description=e_data.get("description", ""),
            aliases=e_data.get("aliases", []),
        )
        upsert_entity(entity)
        entity_count += 1

    for r_data in data.get("relationships", []):
        from_name = r_data.get("from_name", "").strip().lower()
        to_name = r_data.get("to_name", "").strip().lower()
        from_id = name_to_id.get(from_name) or _name_to_id(from_name)
        to_id = name_to_id.get(to_name) or _name_to_id(to_name)

        if not from_id or not to_id or from_id == to_id:
            continue

        rel = Relationship(
            from_id=from_id,
            to_id=to_id,
            rel_type=r_data.get("rel_type", "associated"),
            tie_strength=r_data.get("tie_strength", "strong"),
            doc_id=doc_id,
            date=r_data.get("date"),
            context=r_data.get("context", "")[:500],
        )

        if not relationship_exists(from_id, to_id, rel.rel_type, doc_id):
            insert_relationship(rel)
            rel_count += 1

    return entity_count, rel_count


def run(doc_id: Optional[str] = None) -> str:
    """Run the extractor agent.

    Args:
        doc_id: If provided, only process this document. Otherwise processes all text_extracted docs.
    """
    console.rule("[bold blue]Extractor Agent")

    if doc_id:
        docs = [d for d in list_documents(status="text_extracted") if d.id == doc_id]
    else:
        docs = list_documents(status="text_extracted")

    if not docs:
        console.print("[green]No documents ready for extraction.[/green]")
        return "No documents to extract."

    console.print(f"[cyan]Extracting from {len(docs)} document(s)...[/cyan]")

    client = OpenAI()
    total_entities = 0
    total_rels = 0

    for doc in docs:
        console.print(f"\n[bold]{doc.title}[/bold] ({doc.id})")
        try:
            text = read_text_file(doc.id)
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
            continue

        chunks = chunk_text(text, chunk_size=6000, overlap=300)
        console.print(f"  → {len(chunks)} chunk(s), {len(text)} chars")

        doc_entities = 0
        doc_rels = 0

        for i, chunk in enumerate(chunks):
            console.print(f"  Chunk {i+1}/{len(chunks)}...", end=" ")
            extracted = _extract_from_chunk(client, chunk, doc.id)
            e, r = _save_extraction(extracted, doc.id)
            doc_entities += e
            doc_rels += r
            console.print(f"+{e} entities, +{r} relationships")

        total_entities += doc_entities
        total_rels += doc_rels
        set_document_status(doc.id, "processed")
        console.print(f"  [green]✓ {doc_entities} entities, {doc_rels} relationships[/green]")

    summary = f"Extraction complete. {total_entities} entities, {total_rels} relationships across {len(docs)} document(s)."
    console.print(f"\n[bold green]{summary}[/bold green]")
    return summary
