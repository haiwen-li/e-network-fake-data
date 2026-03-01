"""Graph Builder Subagent — builds a NetworkX graph from extracted data and computes SNA metrics.

Reads all entities and relationships from SQLite, constructs a NetworkX undirected graph,
computes Social Network Analysis metrics, and exports to graph.json.
"""

from rich.console import Console

from src.tools.storage_tools import list_entities, list_relationships
from src.tools.graph_tools import build_graph, compute_sna_metrics, export_graph_json

console = Console()


def run() -> str:
    """Build the graph and compute SNA metrics.

    Returns a summary string.
    """
    console.rule("[bold blue]Graph Builder Agent")

    entities = list_entities()
    relationships = list_relationships()

    if not entities:
        msg = "No entities in database. Run 'python main.py extract' first."
        console.print(f"[red]{msg}[/red]")
        return msg

    console.print(f"[cyan]Building graph: {len(entities)} entities, {len(relationships)} relationships[/cyan]")

    G = build_graph(entities, relationships)

    console.print(f"  → Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Remove isolated nodes (entities with no edges) for a cleaner graph
    isolated = [n for n in G.nodes() if G.degree(n) == 0]
    G.remove_nodes_from(isolated)
    if isolated:
        console.print(f"  → Removed {len(isolated)} isolated nodes")

    console.print("  Computing SNA metrics...")
    metrics = compute_sna_metrics(G)

    # Print top nodes by betweenness centrality
    top_brokers = sorted(metrics.items(), key=lambda x: x[1]["betweenness_centrality"], reverse=True)[:5]
    console.print("\n  [bold]Top brokers (betweenness centrality):[/bold]")
    for node_id, m in top_brokers:
        node_attrs = G.nodes[node_id]
        console.print(f"    {node_attrs.get('name', node_id)}: {m['betweenness_centrality']:.4f}")

    top_connected = sorted(metrics.items(), key=lambda x: x[1]["degree_centrality"], reverse=True)[:5]
    console.print("\n  [bold]Most connected (degree centrality):[/bold]")
    for node_id, m in top_connected:
        node_attrs = G.nodes[node_id]
        console.print(f"    {node_attrs.get('name', node_id)}: {m['degree_centrality']:.4f}")

    out_path = export_graph_json(G, metrics)
    console.print(f"\n  [green]✓ Graph exported to {out_path}[/green]")

    summary = (
        f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges. "
        f"Exported to {out_path}."
    )
    return summary
