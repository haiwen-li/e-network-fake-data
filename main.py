#!/usr/bin/env python3
"""Epstein Network — CLI entry point.

Commands:
  fetch          Fetch documents from data-sources.md registry and extract text
  fetch --new-only  Only fetch documents not yet processed
  extract        Extract entities and relationships from fetched text
  extract --doc <id>  Extract from a specific document
  build          Build NetworkX graph + compute SNA metrics
  visualize      Generate output/network.html
  visualize --output <path>  Save to a custom path
  run-all        Run the full pipeline (fetch → extract → build → visualize)
  register-local <path>  Register a local .txt file as a document
  status         Show pipeline status (document counts by state)
"""

from __future__ import annotations
from typing import Dict, List

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

console = Console()


def cmd_fetch(args: List[str]) -> None:
    from src.agents import fetcher
    new_only = "--new-only" in args
    fetcher.run(new_only=new_only)


def cmd_extract(args: List[str]) -> None:
    from src.agents import extractor
    doc_id = None
    if "--doc" in args:
        idx = args.index("--doc")
        doc_id = args[idx + 1] if idx + 1 < len(args) else None
    extractor.run(doc_id=doc_id)


def cmd_build(_args: List[str]) -> None:
    from src.agents import graph_builder
    graph_builder.run()


def cmd_visualize(args: List[str]) -> None:
    from src.agents import visualizer
    output_path = None
    if "--output" in args:
        idx = args.index("--output")
        output_path = args[idx + 1] if idx + 1 < len(args) else None
    result = visualizer.run(output_path=output_path)
    console.print(f"\nOpen visualization: [link]{result}[/link]")
    # Auto-open in browser
    if "--no-open" not in args:
        import webbrowser
        webbrowser.open(f"file://{Path(result).resolve()}")


def cmd_run_all(_args: List[str]) -> None:
    from src.agents import orchestrator
    orchestrator.run("Build the complete Epstein social network visualization end-to-end.")


def cmd_register_local(args: List[str]) -> None:
    """Register a local .txt file as a document in the registry."""
    if not args:
        console.print("[red]Usage: python main.py register-local <path> [--id <id>] [--title <title>][/red]")
        sys.exit(1)

    src_path = Path(args[0])
    if not src_path.exists():
        console.print(f"[red]File not found: {src_path}[/red]")
        sys.exit(1)

    doc_id = src_path.stem
    if "--id" in args:
        idx = args.index("--id")
        doc_id = args[idx + 1] if idx + 1 < len(args) else doc_id

    title = src_path.stem.replace("-", " ").replace("_", " ").title()
    if "--title" in args:
        idx = args.index("--title")
        title = args[idx + 1] if idx + 1 < len(args) else title

    from src.tools.pdf_tools import register_local_txt
    from src.models.document import Document
    from src.tools.storage_tools import upsert_document

    dest = register_local_txt(src_path, doc_id)
    doc = Document(id=doc_id, title=title, url="", local_path=dest, source="local", status="text_extracted")
    upsert_document(doc)

    console.print(f"[green]✓ Registered '{title}' (id={doc_id}) → {dest}[/green]")
    console.print("Now run: python main.py extract --doc", doc_id)


def cmd_status(_args: List[str]) -> None:
    """Show pipeline status."""
    from src.tools.storage_tools import list_documents, list_entities, list_relationships

    docs = list_documents()
    by_status: Dict[str, list] = {}
    for d in docs:
        by_status.setdefault(d.status, []).append(d)

    table = Table(title="Pipeline Status", show_header=True)
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Documents")

    for status in ["pending", "text_extracted", "processed"]:
        group = by_status.get(status, [])
        titles = ", ".join(d.id for d in group[:4])
        if len(group) > 4:
            titles += f" ... (+{len(group)-4})"
        table.add_row(status, str(len(group)), titles)

    console.print(table)

    entities = list_entities()
    rels = list_relationships()
    console.print(f"\nEntities in DB: [bold]{len(entities)}[/bold]")
    console.print(f"Relationships in DB: [bold]{len(rels)}[/bold]")

    graph_json = Path("data/processed/graph.json")
    vis_html = Path("output/network.html")
    console.print(f"Graph JSON: {'[green]✓[/green]' if graph_json.exists() else '[red]✗[/red]'} {graph_json}")
    console.print(f"Visualization: {'[green]✓[/green]' if vis_html.exists() else '[red]✗[/red]'} {vis_html}")


COMMANDS = {
    "fetch": cmd_fetch,
    "extract": cmd_extract,
    "build": cmd_build,
    "visualize": cmd_visualize,
    "run-all": cmd_run_all,
    "register-local": cmd_register_local,
    "status": cmd_status,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        console.print(__doc__)
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print(f"Available commands: {', '.join(COMMANDS)}")
        sys.exit(1)

    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Error: No API key set. Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env[/red]")
        sys.exit(1)

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
