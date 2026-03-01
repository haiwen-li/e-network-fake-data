"""Visualizer Subagent — generates an interactive PyVis HTML network visualization.

Visual encoding of Social Network Analysis concepts:
  - Node size        → degree centrality (number of connections)
  - Node border      → betweenness centrality (broker/gatekeeper role)
  - Node color       → community (Louvain community detection)
  - Node shape       → entity type (circle=person, square=organization, triangle=location)
  - Edge solid/dashed → strong vs. weak tie (Granovetter)
  - Edge thickness   → co-mention frequency (weight)
  - Hover tooltips   → full details on node/edge including closeness centrality and context quotes
"""
from __future__ import annotations
from typing import Optional

import json
import math
from pathlib import Path

from pyvis.network import Network
from rich.console import Console

from src.tools.graph_tools import load_graph_json

console = Console()

OUTPUT_PATH = Path(__file__).parent.parent.parent / "output" / "network.html"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Role → base color (HSL-friendly palette)
ROLE_COLORS = {
    "politician": "#4A90D9",    # blue
    "businessman": "#2ECC71",   # green
    "royal": "#F1C40F",         # gold
    "socialite": "#E91E63",     # pink
    "legal": "#9B59B6",         # purple
    "ngo": "#1ABC9C",           # teal
    "media": "#E67E22",         # orange
    "other": "#95A5A6",         # gray
    "organization": "#34495E",  # dark slate
    "location": "#7F8C8D",      # medium gray
    "vessel": "#2980B9",        # dark blue
}

# Entity type → PyVis shape
ENTITY_SHAPES = {
    "person": "dot",
    "organization": "square",
    "location": "triangle",
    "vessel": "diamond",
}

# Community index → color (cycle through these)
COMMUNITY_COLORS = [
    "#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6",
    "#1ABC9C", "#E67E22", "#34495E", "#E91E63", "#00BCD4",
    "#FF5722", "#607D8B", "#795548", "#4CAF50", "#03A9F4",
]


def _scale(value: float, min_val: float, max_val: float, out_min: float, out_max: float) -> float:
    if max_val == min_val:
        return (out_min + out_max) / 2
    return out_min + (value - min_val) / (max_val - min_val) * (out_max - out_min)


def _node_tooltip(node: dict) -> str:
    lines = [
        f"<b>{node['name']}</b>",
        f"<i>{node.get('entity_type', 'person').capitalize()} · {node.get('role', 'other').capitalize()}</i>",
    ]
    if node.get("description"):
        lines.append(f"<br>{node['description']}")
    lines.append("<hr>")
    lines.append(f"<b>Degree centrality:</b> {node.get('degree_centrality', 0):.4f}")
    lines.append(f"<b>Betweenness centrality:</b> {node.get('betweenness_centrality', 0):.4f}")
    lines.append(f"<b>Closeness centrality:</b> {node.get('closeness_centrality', 0):.4f}")
    lines.append(f"<b>Clustering coefficient:</b> {node.get('clustering_coefficient', 0):.4f}")
    lines.append(f"<b>Community:</b> {node.get('community', '?')}")
    if node.get("aliases"):
        lines.append(f"<b>Also known as:</b> {', '.join(node['aliases'])}")
    return "<br>".join(lines)


def _edge_tooltip(edge: dict, node_map: dict) -> str:
    from_name = node_map.get(edge["from"], {}).get("name", edge["from"])
    to_name = node_map.get(edge["to"], {}).get("name", edge["to"])
    rel_types = edge.get("rel_types", ["associated"])
    tie = edge.get("tie_strength", "strong")
    weight = edge.get("weight", 1)
    docs = edge.get("doc_ids", [])
    contexts = edge.get("contexts", [])

    lines = [
        f"<b>{from_name}</b> ↔ <b>{to_name}</b>",
        f"<i>Tie strength: {tie.upper()} | Co-mentions: {weight}</i>",
        f"<b>Relationship type(s):</b> {', '.join(rel_types)}",
    ]
    if docs:
        lines.append(f"<b>Source documents:</b> {', '.join(docs)}")
    if contexts:
        lines.append("<b>From the documents:</b>")
        for ctx in contexts[:2]:
            lines.append(f"<i>&ldquo;{ctx}&rdquo;</i>")
    return "<br>".join(lines)


def run(output_path: Optional[str] = None) -> str:
    """Generate the interactive network visualization HTML.

    Args:
        output_path: Override default output path.
    """
    console.rule("[bold blue]Visualizer Agent")

    out = Path(output_path) if output_path else OUTPUT_PATH

    data = load_graph_json()
    nodes = data["nodes"]
    edges = data["edges"]

    if not nodes:
        msg = "No nodes in graph JSON. Run 'python main.py build' first."
        console.print(f"[red]{msg}[/red]")
        return msg

    console.print(f"[cyan]Visualizing {len(nodes)} nodes, {len(edges)} edges[/cyan]")

    # Build lookup
    node_map = {n["id"]: n for n in nodes}

    # Compute scaling ranges
    all_degree = [n.get("degree_centrality", 0) for n in nodes]
    all_between = [n.get("betweenness_centrality", 0) for n in nodes]
    all_weights = [e.get("weight", 1) for e in edges]

    min_deg, max_deg = min(all_degree), max(all_degree)
    min_bet, max_bet = min(all_between), max(all_between)
    min_w, max_w = min(all_weights), max(all_weights)

    # Build PyVis network
    net = Network(
        height="92vh",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="#ecf0f1",
        directed=False,
        notebook=False,
    )
    net.set_options(json.dumps({
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.005,
                "springLength": 120,
                "springConstant": 0.08,
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"iterations": 150},
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 100,
            "hideEdgesOnDrag": True,
        },
        "edges": {
            "smooth": {"type": "dynamic"},
            "color": {"inherit": False},
        },
    }))

    # Add nodes
    for node in nodes:
        entity_type = node.get("entity_type", "person")
        role = node.get("role", "other")
        community = node.get("community", 0)

        # Size: degree centrality → 15..60
        size = _scale(node.get("degree_centrality", 0), min_deg, max_deg, 15, 60)

        # Border width: betweenness centrality → 1..8
        border_width = _scale(node.get("betweenness_centrality", 0), min_bet, max_bet, 1, 8)

        # Color: community
        color_hex = COMMUNITY_COLORS[community % len(COMMUNITY_COLORS)]

        # Shape: entity type
        shape = ENTITY_SHAPES.get(entity_type, "dot")

        net.add_node(
            node["id"],
            label=node["name"],
            title=_node_tooltip(node),
            size=size,
            shape=shape,
            color={
                "background": color_hex,
                "border": ROLE_COLORS.get(role, "#ffffff"),
                "highlight": {"background": color_hex, "border": "#ffffff"},
                "hover": {"background": color_hex, "border": "#ffffff"},
            },
            borderWidth=border_width,
            borderWidthSelected=border_width + 2,
            font={"color": "#ecf0f1", "size": 12},
        )

    # Add edges
    for edge in edges:
        if edge["from"] not in node_map or edge["to"] not in node_map:
            continue

        weight = edge.get("weight", 1)
        tie = edge.get("tie_strength", "strong")

        # Thickness: weight → 1..6
        width = _scale(weight, min_w, max_w, 1, 6)

        # Dashed = weak tie
        dashes = (tie == "weak")

        net.add_edge(
            edge["from"],
            edge["to"],
            title=_edge_tooltip(edge, node_map),
            width=width,
            dashes=dashes,
            color={"color": "#7f8c8d", "highlight": "#ecf0f1", "hover": "#bdc3c7"},
        )

    # Generate HTML and inject legend + ego-network JS
    net.save_graph(str(out))
    _inject_legend_and_controls(out, node_map)

    console.print(f"[green]✓ Visualization saved to {out}[/green]")
    return str(out)


def _inject_legend_and_controls(html_path: Path, node_map: dict) -> None:
    """Inject a legend panel and ego-network click handler into the PyVis HTML."""
    html = html_path.read_text(encoding="utf-8")

    legend_html = """
<style>
  #sna-legend {
    position: fixed; top: 12px; right: 12px;
    background: rgba(20,20,40,0.92); color: #ecf0f1;
    border: 1px solid #4a4a6a; border-radius: 8px;
    padding: 14px 18px; font-family: sans-serif; font-size: 13px;
    max-width: 260px; z-index: 999;
  }
  #sna-legend h3 { margin: 0 0 8px; font-size: 14px; color: #a29bfe; }
  #sna-legend .section { margin-top: 10px; }
  #sna-legend .section-title { font-weight: bold; color: #74b9ff; margin-bottom: 4px; }
  #sna-legend .row { display: flex; align-items: center; margin: 3px 0; gap: 8px; }
  #sna-legend .swatch { width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }
  #sna-legend .circle { border-radius: 50%; }
  #sna-legend .line { width: 24px; height: 3px; flex-shrink: 0; }
  #sna-legend .line.dashed { background: repeating-linear-gradient(90deg,#7f8c8d 0,#7f8c8d 4px,transparent 4px,transparent 8px); }
  #sna-legend .line.solid { background: #7f8c8d; }
</style>
<div id="sna-legend">
  <h3>Epstein Network — SNA Legend</h3>

  <div class="section">
    <div class="section-title">Node Size</div>
    <div class="row"><span>Larger = higher degree centrality (more direct connections)</span></div>
  </div>

  <div class="section">
    <div class="section-title">Node Border</div>
    <div class="row"><span>Thicker border = higher betweenness centrality (network broker)</span></div>
  </div>

  <div class="section">
    <div class="section-title">Node Color</div>
    <div class="row"><span>Color = detected community (Louvain algorithm)</span></div>
  </div>

  <div class="section">
    <div class="section-title">Node Shape</div>
    <div class="row"><div class="swatch circle" style="background:#aaa"></div> Person</div>
    <div class="row"><div class="swatch" style="background:#aaa;border-radius:0"></div> Organization</div>
    <div class="row"><div class="swatch" style="background:#aaa;clip-path:polygon(50% 0,100% 100%,0 100%)"></div> Location</div>
  </div>

  <div class="section">
    <div class="section-title">Edge Style (Granovetter)</div>
    <div class="row"><div class="line solid"></div> Strong tie — direct, explicit connection</div>
    <div class="row"><div class="line dashed"></div> Weak tie — indirect / inferred</div>
  </div>

  <div class="section">
    <div class="section-title">Edge Thickness</div>
    <div class="row"><span>Thicker = more co-mentions across documents</span></div>
  </div>

  <div class="section" style="margin-top:12px; font-size:11px; color:#b2bec3;">
    Hover over any node or edge for details.<br>
    Click a node to highlight its ego network.
  </div>
</div>
"""

    # Patch vis.js tooltips to render HTML (by default vis.js uses innerText, not innerHTML)
    tooltip_fix_js = """
<style>
  .vis-tooltip {
    font-family: sans-serif;
    font-size: 13px;
    background: rgba(20,20,40,0.95) !important;
    color: #ecf0f1 !important;
    border: 1px solid #4a4a6a !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
    max-width: 320px;
    line-height: 1.6;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
  }
  .vis-tooltip b { color: #a29bfe; }
  .vis-tooltip i { color: #b2bec3; }
  .vis-tooltip hr { border-color: #4a4a6a; margin: 6px 0; }
</style>
<script>
  // vis.js sets tooltip content as innerText (plain text); we re-render it as HTML.
  network.on("showPopup", function() {
    setTimeout(function() {
      var el = document.querySelector(".vis-tooltip");
      if (el) { el.innerHTML = el.innerText; }
    }, 0);
  });
</script>
"""

    # Inject legend + tooltip fix before </body>
    html = html.replace("</body>", legend_html + tooltip_fix_js + "</body>")
    html_path.write_text(html, encoding="utf-8")
