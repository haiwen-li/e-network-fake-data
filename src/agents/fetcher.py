"""Fetcher Subagent — downloads and extracts text from documents in the registry.

This agent reads docs/data-sources.md, finds documents with status='pending',
fetches each PDF URL (or registers a local file), extracts text in-memory,
saves a .txt file, and marks the document as 'text_extracted' in the DB.

Claude (haiku) is used to orchestrate tool calls in an agentic loop.
"""
from __future__ import annotations
from typing import List, Optional

import json
import re
from pathlib import Path

import anthropic
from rich.console import Console

from src.models.document import Document
from src.tools.pdf_tools import fetch_pdf_as_text, register_local_txt, text_file_exists
from src.tools.storage_tools import upsert_document, list_documents, set_document_status

console = Console()

REGISTRY_PATH = Path(__file__).parent.parent.parent / "docs" / "data-sources.md"

MODEL = "claude-haiku-4-5-20251001"

# ── Tool definitions for Claude ──────────────────────────────────────────────

TOOLS = [
    {
        "name": "list_pending_documents",
        "description": "Return a list of documents that have not yet been fetched (status=pending).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "fetch_document",
        "description": "Download a PDF from its URL, extract text in-memory, save as .txt, mark as text_extracted.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "The document id"},
                "url": {"type": "string", "description": "The PDF URL to fetch"},
            },
            "required": ["doc_id", "url"],
        },
    },
    {
        "name": "skip_document",
        "description": "Mark a document as text_extracted without fetching (e.g. if URL is unavailable), so it is not retried.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["doc_id", "reason"],
        },
    },
    {
        "name": "report_summary",
        "description": "Report a final summary of what was fetched.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fetched": {"type": "array", "items": {"type": "string"}},
                "skipped": {"type": "array", "items": {"type": "string"}},
                "failed": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["fetched", "skipped", "failed"],
        },
    },
]

# ── Tool implementations ──────────────────────────────────────────────────────

def _list_pending_documents() -> str:
    docs = list_documents(status="pending")
    if not docs:
        return "No pending documents."
    return json.dumps([{"id": d.id, "title": d.title, "url": d.url} for d in docs])


def _fetch_document(doc_id: str, url: str) -> str:
    if text_file_exists(doc_id):
        set_document_status(doc_id, "text_extracted")
        return f"Text file already exists for {doc_id}. Marked as text_extracted."
    try:
        text = fetch_pdf_as_text(url, doc_id)
        set_document_status(doc_id, "text_extracted")
        word_count = len(text.split())
        return f"Successfully extracted {word_count} words from {doc_id}."
    except Exception as e:
        return f"ERROR fetching {doc_id}: {e}"


def _skip_document(doc_id: str, reason: str) -> str:
    set_document_status(doc_id, "text_extracted")
    return f"Skipped {doc_id}: {reason}"


def _dispatch_tool(name: str, inputs: dict) -> str:
    if name == "list_pending_documents":
        return _list_pending_documents()
    elif name == "fetch_document":
        return _fetch_document(inputs["doc_id"], inputs["url"])
    elif name == "skip_document":
        return _skip_document(inputs["doc_id"], inputs["reason"])
    elif name == "report_summary":
        return json.dumps(inputs)
    return f"Unknown tool: {name}"


# ── Registry loader ───────────────────────────────────────────────────────────

def _load_registry() -> List[Document]:
    """Parse data-sources.md YAML block and upsert into DB."""
    import yaml
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    # Extract the fenced yaml block
    match = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if not match:
        raise ValueError("No YAML block found in docs/data-sources.md")
    data = yaml.safe_load(match.group(1))
    docs = []
    for entry in data.get("documents", []):
        doc = Document(
            id=entry["id"],
            title=entry["title"],
            url=entry.get("url", ""),
            source=entry.get("source", ""),
            date=entry.get("date", ""),
            notes=entry.get("notes", ""),
            status="pending",
        )
        # Only insert if not already in DB (preserve existing status)
        from src.tools.storage_tools import get_document
        existing = get_document(doc.id)
        if existing is None:
            upsert_document(doc)
        docs.append(doc)
    return docs


# ── Agent run ─────────────────────────────────────────────────────────────────

def run(new_only: bool = False) -> str:
    """Run the fetcher agent.

    Args:
        new_only: If True, only process documents not yet in the DB.
    """
    console.rule("[bold blue]Fetcher Agent")

    # Load registry into DB
    _load_registry()

    # Build system prompt
    system = (
        "You are a document fetching agent. Your job is to fetch all pending documents "
        "by calling fetch_document for each one. If a URL fails, call skip_document with the reason. "
        "After processing all documents, call report_summary with the results. "
        "Be systematic — list pending docs first, then process each one."
    )

    pending = list_documents(status="pending")
    if not pending:
        console.print("[green]No pending documents to fetch.[/green]")
        return "No pending documents."

    console.print(f"[cyan]Found {len(pending)} pending documents.[/cyan]")

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Please fetch all {len(pending)} pending documents. Start by listing them, then fetch each one."}]

    # Agentic tool-use loop
    final_summary = None
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Collect tool uses in this turn
        tool_results = []
        has_tool_use = False

        for block in response.content:
            if block.type == "text":
                console.print(f"[dim]{block.text}[/dim]")
            elif block.type == "tool_use":
                has_tool_use = True
                console.print(f"[yellow]→ {block.name}({json.dumps(block.input, ensure_ascii=False)[:120]})[/yellow]")
                result = _dispatch_tool(block.name, block.input)
                console.print(f"[green]  ✓ {result[:120]}[/green]")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
                if block.name == "report_summary":
                    final_summary = block.input

        # Append assistant turn + all tool results in one user turn
        messages.append({"role": "assistant", "content": response.content})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if response.stop_reason == "end_turn" or not has_tool_use:
            break

    return json.dumps(final_summary) if final_summary else "Fetch complete."
