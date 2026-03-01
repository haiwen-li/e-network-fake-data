"""Orchestrator Agent — coordinates the full pipeline via Claude tool_use.

The orchestrator uses claude-sonnet-4-6 with four tools (one per subagent).
It decides which subagents to invoke and in what order, handles retries,
and produces a final summary.

Usage:
    from src.agents.orchestrator import run
    run(goal="Build the complete Epstein network")
"""

import json
import anthropic
from rich.console import Console

from src.agents import fetcher, extractor, graph_builder, visualizer

console = Console()

MODEL = "claude-sonnet-4-6"

# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "run_fetcher",
        "description": (
            "Fetch and extract text from documents listed in docs/data-sources.md. "
            "Saves .txt files to data/text/ and marks documents as text_extracted. "
            "Use new_only=true to only process documents not yet fetched."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "new_only": {
                    "type": "boolean",
                    "description": "If true, only process documents not yet fetched.",
                    "default": False,
                }
            },
            "required": [],
        },
    },
    {
        "name": "run_extractor",
        "description": (
            "Extract entities (people, organizations, locations) and relationships from "
            "fetched document text using Claude. Saves to SQLite database. "
            "Optionally target a specific document by doc_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Optional: only extract from this specific document id.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "run_graph_builder",
        "description": (
            "Build a NetworkX social network graph from all extracted entities and relationships. "
            "Computes SNA metrics: degree centrality, betweenness centrality, closeness centrality, "
            "clustering coefficient, and community detection (Louvain). "
            "Exports to data/processed/graph.json."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "run_visualizer",
        "description": (
            "Generate an interactive HTML network visualization from graph.json. "
            "Encodes SNA metrics visually: node size=degree, border=betweenness, "
            "color=community, shape=entity type. Edge style encodes tie strength. "
            "Hover tooltips show full details including context from source documents. "
            "Saves to output/network.html."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Optional: override the output file path.",
                }
            },
            "required": [],
        },
    },
]

# ── Tool dispatch ─────────────────────────────────────────────────────────────

def _dispatch(name: str, inputs: dict) -> str:
    console.print(f"\n[bold cyan]▶ Running {name}...[/bold cyan]")
    try:
        if name == "run_fetcher":
            return fetcher.run(new_only=inputs.get("new_only", False))
        elif name == "run_extractor":
            return extractor.run(doc_id=inputs.get("doc_id"))
        elif name == "run_graph_builder":
            return graph_builder.run()
        elif name == "run_visualizer":
            return visualizer.run(output_path=inputs.get("output_path"))
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        error_msg = f"ERROR in {name}: {e}"
        console.print(f"[red]{error_msg}[/red]")
        return error_msg


# ── Orchestrator loop ─────────────────────────────────────────────────────────

SYSTEM = """You are a pipeline orchestrator for the Epstein Network project.
Your job is to coordinate a team of specialized agents to build a social network visualization
from publicly available Epstein court documents.

Available agents:
1. run_fetcher    — downloads documents and extracts text
2. run_extractor  — extracts entities and relationships via Claude
3. run_graph_builder — builds NetworkX graph + SNA metrics
4. run_visualizer — generates interactive HTML visualization

Guidelines:
- Always run in order: fetch → extract → build → visualize (unless told otherwise)
- After each step, check the result before proceeding
- If a step reports errors, decide whether to retry or continue
- When all steps complete successfully, provide a clear final summary
"""


def run(goal: str = "Build the complete Epstein social network visualization.") -> str:
    """Run the orchestrator with a high-level goal.

    Args:
        goal: Natural language description of what to accomplish.

    Returns:
        Final summary from the orchestrator.
    """
    console.rule("[bold magenta]Orchestrator Agent")
    console.print(f"[dim]Goal: {goal}[/dim]")

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": goal}]

    final_text = ""

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        tool_results = []
        has_tool_use = False

        for block in response.content:
            if block.type == "text":
                console.print(f"\n[italic]{block.text}[/italic]")
                final_text = block.text
            elif block.type == "tool_use":
                has_tool_use = True
                result = _dispatch(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if response.stop_reason == "end_turn" or not has_tool_use:
            break

    console.rule("[bold magenta]Orchestration Complete")
    return final_text
