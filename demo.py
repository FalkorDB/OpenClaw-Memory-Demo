#!/usr/bin/env python3
"""OpenClaw Memory Demo — Mem0 + FalkorDB conference showcase.

Demonstrates how FalkorDB provides graph-structured persistent memory
for AI coding assistants via Mem0. Themed around the OpenClaw coding
assistant blog post.

Run:
    python demo.py

CI smoke-test (skips scenes, only tests initialization):
    DEMO_CI_MODE=1 python demo.py
"""

from __future__ import annotations

import os
import time
from typing import Any

from rich.panel import Panel
from rich.progress import track
from rich.table import Table
from rich.tree import Tree

from config import console, init_mem0

# ── Developer profiles ────────────────────────────────────────────────

DEVELOPERS: dict[str, dict[str, Any]] = {
    "alice": {
        "name": "Alice",
        "emoji": "👩‍💻",
        "color": "cyan",
        "role": "Senior Backend Engineer",
        "messages": [
            "I'm a senior Python developer specializing in Django for backend services.",
            "I always use PostgreSQL as my database — it's the best fit for our relational data.",
            "I'm currently building an e-commerce platform with inventory management and payment processing.",
            "I prefer REST APIs with Django REST Framework for all our service endpoints.",
            "I'm strict about type hints everywhere and run mypy in CI to catch bugs early.",
        ],
    },
    "bob": {
        "name": "Bob",
        "emoji": "🧑‍💻",
        "color": "green",
        "role": "Full-Stack Developer",
        "messages": [
            "I work with TypeScript across the full stack — React on the frontend, Node.js on the backend.",
            "Our frontend is built with Next.js and we use Tailwind CSS for all styling.",
            "We use MongoDB as our primary database for its flexible document model.",
            "I'm building a SaaS analytics dashboard that processes real-time event streams.",
            "I prefer functional components with hooks and always use ESLint with strict rules.",
        ],
    },
    "carol": {
        "name": "Carol",
        "emoji": "👩‍🔬",
        "color": "magenta",
        "role": "ML Engineer",
        "messages": [
            "I'm an ML engineer working primarily with PyTorch for deep learning models.",
            "I use Hugging Face Transformers for all our NLP tasks — sentiment analysis, NER, summarization.",
            "My main project is building production NLP pipelines for document processing.",
            "I do most of my prototyping in Jupyter notebooks before moving to production scripts.",
            "We deploy our models on AWS SageMaker with automated retraining pipelines.",
        ],
    },
}


# ── Helpers ────────────────────────────────────────────────────────────


def scene_header(number: int, title: str, emoji: str) -> None:
    """Display a styled scene header panel."""
    console.print()
    console.print(
        Panel(
            f"[bold white]{title}[/bold white]",
            title=f"{emoji}  Scene {number}",
            title_align="left",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )
    console.print()


def format_memories(results: list[dict[str, Any]]) -> str:
    """Extract readable text from Mem0 search results."""
    if not results:
        return "[dim]No memories found[/dim]"
    lines: list[str] = []
    for r in results:
        memory_text = r.get("memory", str(r))
        lines.append(f"• {memory_text}")
    return "\n".join(lines)


def get_graph_stats(m: Any, user_id: str) -> tuple[int, int]:
    """Return (node_count, relationship_count) for a user's graph."""
    try:
        all_data = m.graph.get_all({"user_id": user_id}, limit=1000)
        nodes: set[str] = set()
        relationships = 0
        if isinstance(all_data, list):
            for item in all_data:
                if isinstance(item, dict):
                    src = item.get("source") or item.get("from")
                    tgt = item.get("target") or item.get("to") or item.get("destination")
                    if src:
                        nodes.add(str(src))
                    if tgt:
                        nodes.add(str(tgt))
                    relationships += 1
        return len(nodes), relationships
    except Exception:
        return 0, 0


# ── Scenes ─────────────────────────────────────────────────────────────


def scene_1_onboarding(m: Any) -> list[str]:
    """Scene 1: Onboard three developers with distinct coding profiles."""
    scene_header(1, "Developer Onboarding", "👩‍💻")

    user_ids: list[str] = []

    for user_id, profile in DEVELOPERS.items():
        name = profile["name"]
        color = profile["color"]
        emoji = profile["emoji"]

        console.print(
            f"  {emoji} Onboarding [bold {color}]{name}[/bold {color}] "
            f"— {profile['role']}"
        )

        for msg in track(
            profile["messages"],
            description=f"    Storing {name}'s memories…",
            console=console,
        ):
            m.add(msg, user_id=user_id)
            time.sleep(0.1)

        console.print(
            f"    [green]✓[/green] {len(profile['messages'])} memories stored "
            f"for [bold {color}]{name}[/bold {color}]\n"
        )
        user_ids.append(user_id)

    console.print(
        Panel(
            f"[green]✓ {len(user_ids)} developers onboarded successfully[/green]",
            border_style="green",
        )
    )
    return user_ids


def scene_2_retrieval(m: Any, user_ids: list[str]) -> None:
    """Scene 2: Context-aware code assistance — query each dev's memories."""
    scene_header(2, "Context-Aware Code Assistance", "🔍")

    queries = [
        ("What database should I use for the project?", "Database Preference"),
        ("What's their current project and tech stack?", "Project & Stack"),
        ("What framework or tools do they prefer?", "Frameworks & Tools"),
    ]

    for query, label in queries:
        console.print(f'  [bold yellow]Query:[/bold yellow] "{query}"\n')

        table = Table(
            title=f"🔎 {label}",
            show_header=True,
            header_style="bold bright_blue",
            border_style="bright_blue",
            padding=(0, 1),
        )
        table.add_column("Developer", style="bold", width=10)
        table.add_column("Relevant Memories", ratio=1)

        for user_id in user_ids:
            profile = DEVELOPERS[user_id]
            results = m.search(query, user_id=user_id, limit=3)
            color = profile["color"]
            name = f"[{color}]{profile['emoji']} {profile['name']}[/{color}]"
            table.add_row(name, format_memories(results))

        console.print(table)
        console.print()

    # Graph stats
    console.print("  [bold bright_blue]📊 Knowledge Graph Statistics[/bold bright_blue]\n")

    stats_table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="bright_blue",
        padding=(0, 1),
    )
    stats_table.add_column("Developer", style="bold", width=10)
    stats_table.add_column("Nodes", justify="center", width=10)
    stats_table.add_column("Relationships", justify="center", width=15)

    for user_id in user_ids:
        profile = DEVELOPERS[user_id]
        nodes, rels = get_graph_stats(m, user_id)
        color = profile["color"]
        name = f"[{color}]{profile['emoji']} {profile['name']}[/{color}]"
        stats_table.add_row(name, str(nodes), str(rels))

    console.print(stats_table)
    console.print()


def scene_3_memory_update(m: Any) -> None:
    """Scene 3: Memory evolution — demonstrate tech stack migration."""
    scene_header(3, "Memory Evolution — Tech Stack Migration", "🔄")

    user_id = "alice"
    profile = DEVELOPERS[user_id]
    color = profile["color"]

    # Before
    console.print(
        f"  [bold]Step 1:[/bold] Query [{color}]Alice[/{color}]'s current API preference\n"
    )
    before = m.search("What API style does the team use?", user_id=user_id, limit=3)
    console.print(
        Panel(
            format_memories(before),
            title="[yellow]Before Migration[/yellow]",
            border_style="yellow",
        )
    )

    # Add migration memory
    console.print(
        f"\n  [bold]Step 2:[/bold] [{color}]Alice[/{color}] records a team decision\n"
    )
    migration_msg = (
        "We decided to migrate our REST API to GraphQL using Strawberry. "
        "The team approved the switch last sprint."
    )
    console.print(f'  [dim]Adding:[/dim] "{migration_msg}"\n')
    m.add(migration_msg, user_id=user_id)
    time.sleep(0.5)

    # After
    console.print(
        f"  [bold]Step 3:[/bold] Query [{color}]Alice[/{color}]'s API preference again\n"
    )
    after = m.search("What API style does the team use?", user_id=user_id, limit=3)
    console.print(
        Panel(
            format_memories(after),
            title="[green]After Migration[/green]",
            border_style="green",
        )
    )

    console.print(
        "\n  [bold bright_blue]💡 Key Insight:[/bold bright_blue] "
        "Mem0 + FalkorDB [italic]updates[/italic] existing knowledge — "
        "old preferences evolve, not duplicate.\n"
    )


def scene_4_isolation_proof(m: Any) -> None:
    """Scene 4: Prove per-user graph isolation."""
    scene_header(4, "Per-User Graph Isolation Proof", "🔒")

    query = "PyTorch deep learning"

    # Alice search
    console.print(
        '  [bold]Test:[/bold] Search for [bold]"PyTorch"[/bold] in '
        "[cyan]Alice[/cyan]'s memories (backend dev)\n"
    )
    alice_results = m.search(query, user_id="alice", limit=5)

    if not alice_results:
        console.print(
            "  [green]✓[/green] [dim]No results[/dim] — "
            "Alice's graph has no PyTorch knowledge\n"
        )
    else:
        console.print(
            Panel(
                format_memories(alice_results),
                title="[yellow]Alice — Unexpected Results[/yellow]",
                border_style="yellow",
            )
        )

    # Carol search
    console.print(
        '  [bold]Test:[/bold] Search for [bold]"PyTorch"[/bold] in '
        "[magenta]Carol[/magenta]'s memories (ML engineer)\n"
    )
    carol_results = m.search(query, user_id="carol", limit=5)

    if carol_results:
        console.print(
            "  [green]✓[/green] Carol's graph returns PyTorch memories:\n"
        )
        console.print(
            Panel(
                format_memories(carol_results),
                title="[green]Carol — PyTorch Memories Found[/green]",
                border_style="green",
            )
        )
    else:
        console.print(
            "  [yellow]⚠[/yellow] No results — Carol's memories may need "
            "time to index\n"
        )

    # Isolation tree
    tree = Tree(
        "🔒 [bold bright_blue]FalkorDB Graph Isolation[/bold bright_blue]"
    )
    for user_id, profile in DEVELOPERS.items():
        color = profile["color"]
        branch = tree.add(
            f"[{color}]{profile['emoji']} {profile['name']}[/{color}]"
        )
        branch.add(f"[dim]Graph:[/dim] [bold]mem0_{user_id}[/bold]")
        branch.add(f"[dim]Role:[/dim] {profile['role']}")
        nodes, rels = get_graph_stats(m, user_id)
        branch.add(f"[dim]Nodes:[/dim] {nodes}  [dim]Rels:[/dim] {rels}")

    console.print()
    console.print(tree)
    console.print(
        "\n  [bold bright_blue]💡 Key Insight:[/bold bright_blue] "
        "Each developer gets a [bold]separate FalkorDB graph[/bold] — "
        "isolation is architectural, not just filtered.\n"
    )


def scene_5_persistence(m: Any) -> None:
    """Scene 5: Cross-session persistence — survive agent restarts."""
    scene_header(5, "Cross-Session Persistence", "💾")

    console.print(
        "  [bold]Simulating agent restart…[/bold]\n"
        "  [dim]Creating a brand-new Memory instance "
        "(as if the coding assistant restarted)[/dim]\n"
    )

    m2 = init_mem0()
    console.print()

    queries = [
        ("alice", "What programming language and framework does Alice use?"),
        ("bob", "What frontend framework and database does Bob prefer?"),
        ("carol", "What ML framework and deployment platform does Carol use?"),
    ]

    table = Table(
        title="🔄 Memories After Simulated Restart",
        show_header=True,
        header_style="bold bright_blue",
        border_style="bright_blue",
        padding=(0, 1),
    )
    table.add_column("Developer", style="bold", width=10)
    table.add_column("Query", ratio=1)
    table.add_column("Retrieved Memory", ratio=2)

    for user_id, query in queries:
        profile = DEVELOPERS[user_id]
        results = m2.search(query, user_id=user_id, limit=2)
        color = profile["color"]
        name = f"[{color}]{profile['emoji']} {profile['name']}[/{color}]"
        table.add_row(name, f"[dim]{query}[/dim]", format_memories(results))

    console.print(table)

    console.print(
        "\n  [bold bright_blue]💡 Key Insight:[/bold bright_blue] "
        "Memories [bold]persist in FalkorDB[/bold] across restarts. "
        "Your coding assistant remembers everything — "
        "that's the core value of graph-structured memory.\n"
    )


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run the full OpenClaw Memory Demo."""
    console.print(
        Panel(
            "[bold white]Mem0 + FalkorDB — Graph Memory for AI Coding Assistants[/bold white]\n\n"
            "[dim]Showcasing persistent, graph-structured developer memory\n"
            "powered by FalkorDB's knowledge graph engine.[/dim]",
            title="🧠 OpenClaw Memory Demo",
            title_align="left",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )

    m = init_mem0()

    # CI smoke-test: only verify initialization succeeds
    if os.getenv("DEMO_CI_MODE"):
        console.print(
            "\n[yellow]CI_MODE active — skipping scenes, "
            "initialization verified ✓[/yellow]"
        )
        return

    users = scene_1_onboarding(m)
    scene_2_retrieval(m, users)
    scene_3_memory_update(m)
    scene_4_isolation_proof(m)
    scene_5_persistence(m)

    # Final summary
    console.print(
        Panel(
            "[bold green]✅ Demo Complete![/bold green]\n\n"
            "[white]Key Takeaways:[/white]\n"
            "  • [cyan]Graph-structured memory[/cyan] captures rich developer context\n"
            "  • [cyan]Per-user isolation[/cyan] via separate FalkorDB graphs\n"
            "  • [cyan]Memory evolution[/cyan] — knowledge updates, not duplicates\n"
            "  • [cyan]Cross-session persistence[/cyan] — survives agent restarts\n\n"
            "[dim]Learn more → github.com/FalkorDB • mem0.ai[/dim]",
            title="🎬 OpenClaw Memory Demo",
            title_align="left",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


if __name__ == "__main__":
    main()
