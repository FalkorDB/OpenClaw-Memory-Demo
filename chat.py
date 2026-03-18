"""Interactive coding assistant chatbot with persistent FalkorDB-backed memory.

Uses Mem0 for automatic memory capture and recall, OpenAI for chat completions,
and Rich for polished terminal UI. Memories persist across sessions per user.

Usage:
    python chat.py
    uv run python chat.py
"""

from __future__ import annotations

import sys

import openai
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from config import console, init_mem0

SYSTEM_PROMPT = (
    "You are a helpful coding assistant. You have persistent memory and "
    "remember the developer's preferences, tech stack, and project context."
)

HELP_TEXT = """\
[bold cyan]Available commands:[/bold cyan]
  [green]/memories[/green]          — List all stored memories for current user
  [green]/search <query>[/green]    — Semantic search across memories
  [green]/forget <id>[/green]       — Delete a specific memory by ID
  [green]/graph[/green]             — Show graph stats (nodes & relationships)
  [green]/user <user_id>[/green]    — Switch to a different user persona
  [green]/clear[/green]             — Clear current chat session history
  [green]/help[/green]              — Show this help message
  [green]/quit[/green] or [green]/exit[/green]    — Exit the chatbot
"""


def build_system_message(memories: list[dict]) -> str:
    """Build the system message, injecting recalled memories if any."""
    if not memories:
        return SYSTEM_PROMPT

    memory_lines = "\n".join(
        f"- {entry.get('memory', str(entry))}" for entry in memories
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Here are relevant things you remember about this developer:\n"
        f"{memory_lines}\n\n"
        f"Use these memories naturally in your responses when relevant."
    )


def recall_memories(m, message: str, user_id: str) -> list[dict]:
    """Search for memories relevant to the user message."""
    try:
        results = m.search(message, user_id=user_id)
        if isinstance(results, dict):
            return results.get("results", [])
        return results or []
    except Exception as e:
        console.print(f"[dim red]⚠ Memory recall error: {e}[/dim red]")
        return []


def capture_memories(m, conversation: str, user_id: str) -> None:
    """Let Mem0 extract and store new facts from the conversation."""
    try:
        m.add(conversation, user_id=user_id)
        console.print("[dim]✓ Memories updated[/dim]")
    except Exception as e:
        console.print(f"[dim red]⚠ Memory capture error: {e}[/dim red]")


def get_chat_response(
    client: openai.OpenAI,
    history: list[dict],
    system_msg: str,
) -> str:
    """Call OpenAI chat completions and return the assistant reply."""
    messages = [{"role": "system", "content": system_msg}, *history]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        return resp.choices[0].message.content or ""
    except openai.APIError as e:
        return f"⚠ OpenAI API error: {e}"
    except Exception as e:
        return f"⚠ Unexpected error: {e}"


# ── Slash command handlers ───────────────────────────────────────────


def cmd_memories(m, user_id: str) -> None:
    """List all stored memories for the current user."""
    try:
        all_mems = m.get_all(user_id=user_id)
        results = (
            all_mems.get("results", []) if isinstance(all_mems, dict) else all_mems
        )
    except Exception as e:
        console.print(f"[red]Error fetching memories: {e}[/red]")
        return

    if not results:
        console.print("[yellow]No memories stored yet.[/yellow]")
        return

    table = Table(title=f"Memories for [bold]{user_id}[/bold]", show_lines=True)
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Memory", style="white")

    for entry in results:
        mem_id = entry.get("id", "?")
        memory = entry.get("memory", str(entry))
        table.add_row(str(mem_id), memory)

    console.print(table)


def cmd_search(m, query: str, user_id: str) -> None:
    """Semantic search across memories."""
    if not query:
        console.print("[yellow]Usage: /search <query>[/yellow]")
        return

    try:
        results = m.search(query, user_id=user_id)
        items = results.get("results", []) if isinstance(results, dict) else results
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
        return

    if not items:
        console.print("[yellow]No matching memories found.[/yellow]")
        return

    table = Table(title=f"Search results for '{query}'", show_lines=True)
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Memory", style="white")
    table.add_column("Score", style="cyan", justify="right")

    for entry in items:
        mem_id = str(entry.get("id", "?"))
        memory = entry.get("memory", str(entry))
        score = entry.get("score", "")
        score_str = f"{score:.3f}" if isinstance(score, float) else str(score)
        table.add_row(mem_id, memory, score_str)

    console.print(table)


def cmd_forget(m, memory_id: str, user_id: str) -> None:
    """Delete a specific memory by ID."""
    if not memory_id:
        console.print("[yellow]Usage: /forget <memory_id>[/yellow]")
        return

    try:
        m.delete(memory_id)
        console.print(f"[green]✓ Memory {memory_id} deleted.[/green]")
    except Exception as e:
        console.print(f"[red]Error deleting memory: {e}[/red]")


def cmd_graph(m) -> None:
    """Show graph stats: node and relationship counts."""
    try:
        graph_data = m.graph.get_all()
        nodes = graph_data.get("nodes", []) if isinstance(graph_data, dict) else []
        rels = (
            graph_data.get("relationships", graph_data.get("edges", []))
            if isinstance(graph_data, dict)
            else []
        )

        table = Table(title="Graph Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_row("Nodes", str(len(nodes)))
        table.add_row("Relationships", str(len(rels)))
        console.print(table)

        if nodes:
            node_table = Table(title="Nodes (sample)", show_lines=True)
            node_table.add_column("Label", style="cyan")
            node_table.add_column("Name / ID", style="white")
            for node in nodes[:15]:
                label = node.get("label", node.get("type", "?"))
                name = node.get("name", node.get("id", str(node)))
                node_table.add_row(str(label), str(name))
            if len(nodes) > 15:
                node_table.add_row("...", f"({len(nodes) - 15} more)")
            console.print(node_table)

    except Exception as e:
        console.print(f"[red]Error querying graph: {e}[/red]")


# ── Main loop ────────────────────────────────────────────────────────


def show_welcome(user_id: str) -> None:
    """Display the welcome panel."""
    console.print(
        Panel(
            "[bold cyan]Mem0 + FalkorDB Coding Assistant[/bold cyan]\n\n"
            "An interactive coding assistant with [green]persistent graph memory[/green].\n"
            "Your preferences, tech stack, and project decisions are remembered\n"
            "across sessions — powered by Mem0 and FalkorDB.\n\n"
            f"Current user: [bold yellow]{user_id}[/bold yellow]\n\n"
            "Type [green]/help[/green] for commands, or just start chatting!",
            title="🧠 OpenClaw Memory Demo",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def main() -> None:
    """Run the interactive chatbot loop."""
    m = init_mem0()
    client = openai.OpenAI()

    user_id = "developer"
    history: list[dict[str, str]] = []

    show_welcome(user_id)

    while True:
        try:
            user_input = console.input(
                f"\n[bold green][{user_id}][/bold green] > "
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! 👋[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        # ── Slash commands ────────────────────────────────────────
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in ("/quit", "/exit"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break
            elif cmd == "/help":
                console.print(HELP_TEXT)
            elif cmd == "/memories":
                cmd_memories(m, user_id)
            elif cmd == "/search":
                cmd_search(m, arg, user_id)
            elif cmd == "/forget":
                cmd_forget(m, arg, user_id)
            elif cmd == "/graph":
                cmd_graph(m)
            elif cmd == "/user":
                if not arg:
                    console.print(f"[yellow]Current user: {user_id}[/yellow]")
                    console.print("[yellow]Usage: /user <user_id>[/yellow]")
                else:
                    user_id = arg
                    history.clear()
                    console.print(
                        f"[green]✓ Switched to user [bold]{user_id}[/bold]. "
                        "Chat history cleared; memories persist.[/green]"
                    )
            elif cmd == "/clear":
                history.clear()
                console.print(
                    "[green]✓ Chat history cleared. Memories persist.[/green]"
                )
            else:
                console.print(
                    f"[yellow]Unknown command: {cmd}. Type /help for options.[/yellow]"
                )
            continue

        # ── Auto-recall: search memories ──────────────────────────
        with console.status("[dim]Recalling memories…[/dim]", spinner="dots"):
            memories = recall_memories(m, user_input, user_id)

        if memories:
            summary = ", ".join(entry.get("memory", "…")[:60] for entry in memories[:3])
            suffix = f" (+{len(memories) - 3} more)" if len(memories) > 3 else ""
            console.print(
                f"[dim cyan]📎 Recalled {len(memories)} "
                f"{'memory' if len(memories) == 1 else 'memories'}: "
                f"{summary}{suffix}[/dim cyan]"
            )

        # ── LLM response ─────────────────────────────────────────
        history.append({"role": "user", "content": user_input})
        system_msg = build_system_message(memories)

        with console.status("[dim]Thinking…[/dim]", spinner="dots"):
            reply = get_chat_response(client, history, system_msg)

        history.append({"role": "assistant", "content": reply})

        console.print(
            Panel(
                Markdown(reply),
                title="[bold magenta]Assistant[/bold magenta]",
                border_style="magenta",
                padding=(0, 1),
            )
        )

        # ── Auto-capture: store new memories ─────────────────────
        conversation_text = f"User: {user_input}\nAssistant: {reply}"
        capture_memories(m, conversation_text, user_id)


if __name__ == "__main__":
    main()
