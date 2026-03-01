# Agent Guide

## How the Agent Team Works

This project uses the **Orchestrator + Subagents** pattern from the Anthropic SDK.
Each subagent is a Python class/module with:
1. A set of **tool definitions** (JSON schema for Claude)
2. A set of **tool implementations** (Python functions)
3. A **`run()` function** that starts an agentic Claude loop

The Orchestrator uses `tool_use` to invoke subagents. Each subagent uses `tool_use` to call
its own internal tools (e.g. "fetch this URL", "save to database").

## Agent Models

| Agent | API | Model | Why |
|-------|-----|-------|-----|
| Orchestrator | Anthropic | claude-sonnet-4-6 | Strong reasoning to decide pipeline order |
| Fetcher | Anthropic | claude-haiku-4-5 | Simple task: iterate a list, handle errors |
| Extractor | OpenAI | gpt-4o-mini | Cheap structured JSON extraction; uses `response_format=json_object` |
| Graph Builder | — | No LLM | Pure computation |
| Visualizer | — | No LLM | Pure HTML generation |

**Required environment variables** (set in `.env`):
```
ANTHROPIC_API_KEY=sk-ant-...   # used by Orchestrator and Fetcher
OPENAI_API_KEY=sk-proj-...     # used by Extractor
```

The `ORCHESTRATOR_MODEL` and `FETCHER_MODEL` env vars in `.env` are read for reference
but the extractor model is hardcoded to `gpt-4o-mini` in `src/agents/extractor.py`.

## Adding a New Subagent

1. **Create `src/agents/my_agent.py`**:

```python
import json
import anthropic  # or: from openai import OpenAI

MODEL = "claude-haiku-4-5-20251001"

TOOLS = [
    {
        "name": "my_tool",
        "description": "What this tool does.",
        "input_schema": {
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": ["param"],
        },
    },
]

def _dispatch_tool(name: str, inputs: dict) -> str:
    if name == "my_tool":
        return f"Did something with {inputs['param']}"
    return f"Unknown tool: {name}"

def run(task_input: str = "") -> str:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Do your job. Input: {task_input}"}]

    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=2048,
            tools=TOOLS, messages=messages,
        )
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _dispatch_tool(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})

        messages.append({"role": "assistant", "content": response.content})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        if response.stop_reason == "end_turn":
            break

    return "Done."
```

2. **Register it in the Orchestrator** (`src/agents/orchestrator.py`):

Add a new entry to `TOOLS`:
```python
{
    "name": "run_my_agent",
    "description": "What this agent does and when to use it.",
    "input_schema": {"type": "object", "properties": {}, "required": []},
},
```

Add it to `_dispatch()`:
```python
elif name == "run_my_agent":
    return my_agent.run()
```

3. **Add a CLI command** in `main.py` if needed.

## Adding New Tools to an Existing Agent

Open the agent file and:
1. Add a new dict to the `TOOLS` list
2. Add a new `if` branch to `_dispatch_tool()`

The tool will be available to Claude on the next run.

## Modifying the Extraction Prompt

The extraction prompt lives in `src/agents/extractor.py` as `EXTRACTION_SYSTEM`.
It controls what entities and relationships gpt-4o-mini extracts from document text.

To change what's extracted:
- Add new `entity_type` values in the prompt and update `src/models/entity.py`
- Add new `rel_type` values for relationship types
- Adjust `chunk_size` in `src/tools/pdf_tools.py` for longer/shorter context windows

## Debugging

### Check what's in the database
```bash
python main.py status
```

### Inspect SQLite directly
```bash
sqlite3 data/epstein.db
.tables
SELECT * FROM entities LIMIT 10;
SELECT * FROM relationships LIMIT 10;
```

### Re-run extraction for a single document
```bash
python main.py extract --doc maxwell-depo-2016-pt1
```

### Reset the database
```bash
rm data/epstein.db
python main.py fetch  # re-fetches all
```

### Run without the orchestrator
Each agent can be run directly:
```python
from src.agents import fetcher, extractor, graph_builder, visualizer
fetcher.run()
extractor.run()
graph_builder.run()
visualizer.run()
```

## Cost Considerations

| Step | Typical token usage | Model | Approx cost |
|------|-------------------|-------|-------------|
| Fetcher | ~500 tokens/doc | claude-haiku-4-5 | ~$0.001/doc |
| Extractor | ~2k-6k tokens/chunk × N chunks | gpt-4o-mini | ~$0.002/doc |
| Graph Builder | None | — | free |
| Visualizer | None | — | free |

To reduce cost during development:
- Process just 1-2 documents: `python main.py extract --doc <id>`
- Use a smaller chunk size in `pdf_tools.py` (`chunk_size=4000`)

**Seeded data**: `seed_data.py` at the project root pre-populates the database
with 55 entities and 79 relationships from public court records, bypassing
the fetch + extract steps entirely (no API cost). Run: `python seed_data.py`
