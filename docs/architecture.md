# Architecture

## Overview

```
main.py CLI
    │
    ▼
Orchestrator (claude-sonnet-4-6)
    │  uses tool_use to delegate
    ├─► Fetcher (claude-haiku-4-5)
    │       reads data-sources.md YAML
    │       streams PDF → pdfplumber (in-memory)
    │       saves data/text/<id>.txt
    │       marks document: text_extracted
    │
    ├─► Extractor (gpt-4o-mini via OpenAI API)
    │       reads .txt → chunks (6k chars, 300 overlap)
    │       sends each chunk to gpt-4o-mini with extraction prompt
    │       parses JSON → Entity + Relationship models
    │       saves to SQLite (epstein.db)
    │       marks document: processed
    │
    ├─► Graph Builder (no LLM — pure NetworkX)
    │       queries all entities + relationships from SQLite
    │       builds nx.Graph (undirected, aggregated edges)
    │       computes SNA metrics (see below)
    │       exports data/processed/graph.json
    │
    └─► Visualizer (no LLM — PyVis)
            loads graph.json
            creates PyVis Network
            encodes SNA metrics as visual properties
            injects legend HTML
            saves output/network.html
```

## Why This Agent Team Structure?

Each subagent has a **single, well-defined responsibility**:

| Agent | LLM? | Responsibility |
|-------|------|---------------|
| Orchestrator | claude-sonnet-4-6 (Anthropic) | Decides *what* to do next using tool_use |
| Fetcher | claude-haiku-4-5 (Anthropic) | Navigates the document list, handles errors gracefully |
| Extractor | gpt-4o-mini (OpenAI) | Entity/relation extraction from document chunks |
| Graph Builder | None | Pure computation — LLM not needed |
| Visualizer | None | Pure HTML generation — LLM not needed |

Using LLMs only where intelligence is actually needed reduces cost and latency.
The Extractor uses OpenAI's gpt-4o-mini because it offers strong structured JSON output
at low cost (~$0.15/1M input tokens) with `response_format={"type": "json_object"}`
guaranteeing valid JSON responses.

## Agentic Tool-Use Pattern

All Claude agents follow the same loop:

```python
while True:
    response = client.messages.create(
        model=MODEL,
        tools=TOOLS,
        messages=messages,
    )

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = dispatch_tool(block.name, block.input)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})

    messages.append({"role": "assistant", "content": response.content})
    if tool_results:
        messages.append({"role": "user", "content": tool_results})

    if response.stop_reason == "end_turn":
        break
```

Key points:
- All tool results from a single assistant turn are collected and sent **in one user message**
- The loop exits when Claude stops calling tools (`stop_reason == "end_turn"`)
- Each agent manages its own `messages` history independently

## Data Flow

```
docs/data-sources.md (YAML)
    │ _load_registry()
    ▼
epstein.db.documents (status=pending)
    │ fetcher
    ▼
data/text/<id>.txt + epstein.db.documents (status=text_extracted)
    │ extractor
    ▼
epstein.db.entities + epstein.db.relationships + epstein.db.documents (status=processed)
    │ graph_builder
    ▼
data/processed/graph.json
    │ visualizer
    ▼
output/network.html
```

## Database Schema (SQLite)

### `documents`
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Unique slug |
| title | TEXT | Human-readable title |
| url | TEXT | Source URL |
| local_path | TEXT | Path to .txt file |
| source | TEXT | Origin (courtlistener, archive.org, etc.) |
| date | TEXT | Document date |
| notes | TEXT | Why it's relevant |
| status | TEXT | pending / text_extracted / processed |

### `entities`
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | Normalized slug |
| name | TEXT | Full name |
| aliases | TEXT | JSON array of alternate names |
| entity_type | TEXT | person / organization / location / vessel |
| role | TEXT | politician / businessman / royal / socialite / legal / ngo / media / other |
| description | TEXT | Brief description from documents |

### `relationships`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Auto-increment |
| from_id | TEXT | Source entity id |
| to_id | TEXT | Target entity id |
| rel_type | TEXT | flew_with / met_with / employed / associated / accused / funded / ... |
| tie_strength | TEXT | strong / weak |
| doc_id | TEXT | Source document id |
| date | TEXT | Date mentioned (nullable) |
| context | TEXT | Direct quote or paraphrase from document |

---

## Social Network Theory

### Core Concepts Used

#### Degree Centrality
`C_D(v) = deg(v) / (n-1)`

How many direct connections a node has, normalized by the maximum possible.
**Visual encoding**: Node size (larger = more connected).

#### Betweenness Centrality
`C_B(v) = Σ_{s≠v≠t} σ_{st}(v) / σ_{st}`

How often a node appears on the shortest path between other nodes.
High betweenness = **network broker** — controls information/access flow.
**Visual encoding**: Node border thickness.

#### Closeness Centrality
`C_C(v) = (n-1) / Σ_u d(v,u)`

How quickly a node can reach all others.
**Visual encoding**: Shown in hover tooltip.

#### Clustering Coefficient
`C(v) = 2|{e_{jk}}| / deg(v)(deg(v)-1)`

Fraction of a node's neighbors who are also neighbors of each other.
Low coefficient on a high-betweenness node → clear **bridge/broker**.
**Visual encoding**: Shown in hover tooltip.

#### Weak Ties (Granovetter, 1973)
Counterintuitively, *weak* ties (infrequent, indirect connections) are often more
important for information diffusion than strong ties (close, frequent connections).
Weak ties bridge disconnected clusters.
**Visual encoding**: Dashed edges for weak ties, solid for strong.

#### Community Detection (Louvain)
Groups densely connected nodes into communities by maximizing modularity.
Communities often correspond to real-world social circles.
**Visual encoding**: Node color (each color = one detected community).

### Interpreting the Network

| What to look for | SNA concept |
|-----------------|-------------|
| Largest nodes | Most connected individuals (degree centrality) |
| Thickest borders | Brokers who connect otherwise separate groups (betweenness) |
| Dashed edges | Loose associations — potentially underreported connections |
| Same-color clusters | Social circles (legal team, political contacts, business network) |
| Nodes bridging color groups | Key connectors between different worlds |
