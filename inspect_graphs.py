"""Graph inspector for the OpenClaw Memory Demo.

Connects directly to FalkorDB and displays the raw graph structure
for each user's memory graph. Useful for understanding how memories
are stored as nodes and relationships.

Prerequisites:
- FalkorDB running (local Docker or FalkorDB Cloud — see .env)
- At least one user's memories created (run the demo or chatbot first)

Usage:
    python inspect_graphs.py
    uv run python inspect_graphs.py
"""

from typing import Dict, List

from falkordb import FalkorDB
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from config import console, get_falkordb_config


def get_all_mem0_graphs(db: FalkorDB, database_prefix: str = "mem0") -> List[str]:
    """List all graphs with the mem0 prefix."""
    all_graphs = db.list_graphs()
    return [g for g in all_graphs if g.startswith(f"{database_prefix}_")]


def extract_user_id(graph_name: str, database_prefix: str = "mem0") -> str:
    """Extract user_id from graph name (e.g., 'mem0_alice' -> 'alice')."""
    prefix = f"{database_prefix}_"
    if graph_name.startswith(prefix):
        return graph_name[len(prefix) :]
    return graph_name


def get_graph_nodes(db: FalkorDB, graph_name: str, limit: int = 100) -> List[Dict]:
    """Get nodes from a graph with a limit."""
    graph = db.select_graph(graph_name)
    result = graph.query(
        f"MATCH (n) RETURN id(n) AS id, labels(n) AS labels, n AS node LIMIT {limit}"
    )

    nodes = []
    if result.result_set:
        header = [h[1] if isinstance(h, (list, tuple)) else h for h in result.header]
        for row in result.result_set:
            nodes.append(dict(zip(header, row)))

    return nodes


def get_graph_relationships(
    db: FalkorDB, graph_name: str, limit: int = 100
) -> List[Dict]:
    """Get relationships from a graph with a limit."""
    graph = db.select_graph(graph_name)
    result = graph.query(
        f"""
        MATCH (a)-[r]->(b)
        RETURN id(a) AS source_id, a.name AS source,
               type(r) AS relationship,
               id(b) AS target_id, b.name AS target,
               r AS rel_props
        LIMIT {limit}
        """
    )

    relationships = []
    if result.result_set:
        header = [h[1] if isinstance(h, (list, tuple)) else h for h in result.header]
        for row in result.result_set:
            relationships.append(dict(zip(header, row)))

    return relationships


def format_node_properties(node: object) -> str:
    """Format node properties for display, filtering out embedding vectors."""
    if not hasattr(node, "properties"):
        return ""

    props = node.properties
    display_props = {k: v for k, v in props.items() if k != "embedding"}

    if not display_props:
        return ""

    return ", ".join(f"{k}={repr(v)}" for k, v in display_props.items())


def display_user_graph(
    db: FalkorDB, graph_name: str, user_id: str, detailed: bool = False
) -> None:
    """Display graph structure for a single user."""
    console.print(f"\n[bold cyan]User: {user_id}[/bold cyan]")
    console.print(f"[dim]Graph: {graph_name}[/dim]\n")

    nodes = get_graph_nodes(db, graph_name)
    relationships = get_graph_relationships(db, graph_name)

    if not nodes and not relationships:
        console.print("[yellow]  Empty graph — no data[/yellow]")
        return

    # Summary stats
    console.print(f"  [green]Nodes:[/green] {len(nodes)}")
    console.print(f"  [green]Relationships:[/green] {len(relationships)}\n")

    # Nodes table
    if nodes:
        node_table = Table(
            title=f"Nodes in {user_id}'s Graph",
            show_header=True,
            header_style="bold yellow",
        )
        node_table.add_column("ID", style="dim")
        node_table.add_column("Labels", style="cyan")
        node_table.add_column("Name", style="green")
        if detailed:
            node_table.add_column("Properties", style="dim", no_wrap=False)

        for node_data in nodes[:20]:
            node = node_data.get("node")
            labels_list = node_data.get("labels", [])
            node_id = str(node_data.get("id", "?"))

            if hasattr(node, "properties"):
                name = node.properties.get("name", "(unnamed)")
            else:
                name = "(unnamed)"

            labels_str = ", ".join(labels_list) if labels_list else "(no label)"

            if detailed:
                node_table.add_row(
                    node_id, labels_str, name, format_node_properties(node)
                )
            else:
                node_table.add_row(node_id, labels_str, name)

        console.print(node_table)

    # Relationships table
    if relationships:
        rel_table = Table(
            title=f"Relationships in {user_id}'s Graph",
            show_header=True,
            header_style="bold magenta",
        )
        rel_table.add_column("Source", style="cyan")
        rel_table.add_column("Relationship", style="yellow")
        rel_table.add_column("Target", style="green")
        if detailed:
            rel_table.add_column("Mentions", style="dim")

        for rel in relationships[:20]:
            source = rel.get("source", "(unknown)")
            target = rel.get("target", "(unknown)")
            rel_type = rel.get("relationship", "?")

            if detailed:
                rel_props = rel.get("rel_props")
                mentions = "?"
                if hasattr(rel_props, "properties"):
                    mentions = str(rel_props.properties.get("mentions", "?"))
                rel_table.add_row(source, rel_type, target, mentions)
            else:
                rel_table.add_row(source, rel_type, target)

        console.print(rel_table)

    # Tree visualization
    if relationships:
        console.print(f"\n[bold]Graph Structure Preview for {user_id}:[/bold]")
        tree = Tree(f"[bold cyan]{user_id}[/bold cyan]")

        rel_by_source: Dict[str, List[Dict]] = {}
        for rel in relationships[:10]:
            source = rel.get("source", "?")
            if source not in rel_by_source:
                rel_by_source[source] = []
            rel_by_source[source].append(rel)

        for source, rels in list(rel_by_source.items())[:5]:
            source_branch = tree.add(f"[cyan]{source}[/cyan]")
            for r in rels[:3]:
                rel_type = r.get("relationship", "?")
                target = r.get("target", "?")
                source_branch.add(
                    f"--[[yellow]{rel_type}[/yellow]]--> [green]{target}[/green]"
                )

        console.print(tree)


def main() -> None:
    """Inspect all mem0 graphs stored in FalkorDB."""
    console.print(
        Panel.fit(
            "[bold magenta]mem0-falkordb Graph Inspector[/bold magenta]\n\n"
            "View raw graph structure for each user's memory",
            border_style="magenta",
        )
    )

    # Connect using shared config (supports docker & cloud modes)
    falkordb_cfg = get_falkordb_config()
    conn_kwargs = {k: v for k, v in falkordb_cfg.items() if k != "database"}

    try:
        db = FalkorDB(**conn_kwargs)
        mode = "cloud" if "username" in conn_kwargs else "docker"
        console.print(f"\n[green]✓ Connected to FalkorDB ({mode} mode)[/green]")
    except Exception as e:
        console.print(
            f"[red]Failed to connect to FalkorDB:[/red]\n{e}\n\n"
            "[yellow]Make sure FalkorDB is running:[/yellow]\n"
            "  docker compose up -d"
        )
        return

    # Find all mem0 graphs
    database_prefix = falkordb_cfg.get("database", "mem0")
    mem0_graphs = get_all_mem0_graphs(db, database_prefix=database_prefix)

    if not mem0_graphs:
        console.print(
            "\n[yellow]No mem0 graphs found![/yellow]\n"
            "Run the demo or chatbot first to create some user memories."
        )
        return

    console.print(f"\n[cyan]Found {len(mem0_graphs)} user graph(s):[/cyan]")
    for graph_name in mem0_graphs:
        user_id = extract_user_id(graph_name, database_prefix)
        console.print(f"  • {graph_name} ([bold]{user_id}[/bold])")

    # Display each user's graph
    for graph_name in mem0_graphs:
        user_id = extract_user_id(graph_name, database_prefix)
        display_user_graph(db, graph_name, user_id, detailed=True)

    # Summary
    console.print(
        Panel.fit(
            "[bold green]Inspection Complete![/bold green]\n\n"
            "[cyan]Key Observations:[/cyan]\n"
            "• Each user has a separate FalkorDB graph\n"
            "• Nodes represent entities (people, places, concepts)\n"
            "• Relationships show how entities are connected\n"
            "• Properties store metadata (created, mentions, embeddings)\n\n"
            "[dim]This is the power of graph-structured memory![/dim]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
