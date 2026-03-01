"""NetworkX graph construction and Social Network Analysis helpers."""
from __future__ import annotations
from typing import Dict, List, Tuple

import json
from collections import defaultdict
from pathlib import Path

import networkx as nx

try:
    import community as community_louvain  # python-louvain
    HAS_LOUVAIN = True
except ImportError:
    HAS_LOUVAIN = False

from src.models.entity import Entity
from src.models.relationship import Relationship

GRAPH_JSON_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "graph.json"
GRAPH_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)


def build_graph(entities: List[Entity], relationships: List[Relationship]) -> nx.Graph:
    """Build an undirected NetworkX graph from entities and relationships."""
    G = nx.Graph()

    for e in entities:
        G.add_node(e.id, **{
            "name": e.name,
            "entity_type": e.entity_type,
            "role": e.role,
            "description": e.description,
            "aliases": e.aliases,
        })

    # Aggregate edges: multiple relationships between same pair → heavier edge
    edge_data: Dict[Tuple, Dict] = defaultdict(lambda: {
        "weight": 0,
        "rel_types": set(),
        "tie_strength": "weak",
        "contexts": [],
        "doc_ids": set(),
    })

    for r in relationships:
        key = tuple(sorted([r.from_id, r.to_id]))
        edge_data[key]["weight"] += 1
        edge_data[key]["rel_types"].add(r.rel_type)
        edge_data[key]["doc_ids"].add(r.doc_id)
        if r.context:
            edge_data[key]["contexts"].append(r.context[:300])
        # Upgrade to strong if any relationship is strong
        if r.tie_strength == "strong":
            edge_data[key]["tie_strength"] = "strong"

    for (u, v), data in edge_data.items():
        if G.has_node(u) and G.has_node(v):
            G.add_edge(u, v,
                weight=data["weight"],
                rel_types=list(data["rel_types"]),
                tie_strength=data["tie_strength"],
                contexts=data["contexts"][:3],  # keep top 3
                doc_ids=list(data["doc_ids"]),
            )

    return G


def compute_sna_metrics(G: nx.Graph) -> Dict[str, Dict]:
    """Compute Social Network Analysis metrics for all nodes.

    Returns a dict: node_id -> {degree_centrality, betweenness_centrality,
                                closeness_centrality, clustering_coefficient, community}
    """
    if G.number_of_nodes() == 0:
        return {}

    degree_c = nx.degree_centrality(G)
    between_c = nx.betweenness_centrality(G, normalized=True)
    close_c = nx.closeness_centrality(G)
    clustering = nx.clustering(G)

    # Community detection
    communities = {}
    if HAS_LOUVAIN and G.number_of_edges() > 0:
        partition = community_louvain.best_partition(G)
        communities = partition
    else:
        # Fallback: connected components as communities
        for i, component in enumerate(nx.connected_components(G)):
            for node in component:
                communities[node] = i

    metrics = {}
    for node in G.nodes():
        metrics[node] = {
            "degree_centrality": round(degree_c.get(node, 0), 4),
            "betweenness_centrality": round(between_c.get(node, 0), 4),
            "closeness_centrality": round(close_c.get(node, 0), 4),
            "clustering_coefficient": round(clustering.get(node, 0), 4),
            "community": communities.get(node, 0),
        }

    return metrics


def export_graph_json(G: nx.Graph, metrics: Dict[str, Dict]) -> str:
    """Serialize graph + metrics to JSON for the visualizer."""
    data = {
        "nodes": [],
        "edges": [],
    }

    for node_id, attrs in G.nodes(data=True):
        node_metrics = metrics.get(node_id, {})
        data["nodes"].append({
            "id": node_id,
            **attrs,
            **node_metrics,
        })

    for u, v, attrs in G.edges(data=True):
        data["edges"].append({
            "from": u,
            "to": v,
            **{k: (list(v2) if isinstance(v2, set) else v2) for k, v2 in attrs.items()},
        })

    GRAPH_JSON_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(GRAPH_JSON_PATH)


def load_graph_json() -> dict:
    """Load the exported graph JSON."""
    if not GRAPH_JSON_PATH.exists():
        raise FileNotFoundError("Graph JSON not found. Run 'python main.py build' first.")
    return json.loads(GRAPH_JSON_PATH.read_text(encoding="utf-8"))
