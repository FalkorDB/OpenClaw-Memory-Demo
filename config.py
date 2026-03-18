"""Shared configuration for the OpenClaw Memory Demo.

Reads settings from .env and builds the Mem0 + FalkorDB config dict.
Supports two FalkorDB modes: 'docker' (local) and 'cloud' (FalkorDB Cloud).
"""

import os
import sys

from dotenv import load_dotenv
from rich.console import Console

console = Console()

load_dotenv()


def get_falkordb_config() -> dict:
    """Build FalkorDB connection config based on FALKORDB_MODE."""
    mode = os.getenv("FALKORDB_MODE", "docker").lower()
    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", "6379"))

    cfg = {
        "host": host,
        "port": port,
        "database": "mem0",
    }

    if mode == "cloud":
        username = os.getenv("FALKORDB_USERNAME", "default")
        password = os.getenv("FALKORDB_PASSWORD", "")
        if not password:
            console.print(
                "[red]Error: FALKORDB_PASSWORD is required when FALKORDB_MODE=cloud[/red]"
            )
            sys.exit(1)
        cfg["username"] = username
        cfg["password"] = password

    return cfg


def get_mem0_config() -> dict:
    """Build the full Mem0 configuration dict."""
    return {
        "graph_store": {
            "provider": "falkordb",
            "config": get_falkordb_config(),
        },
        "llm": {
            "provider": "openai",
            "config": {"model": "gpt-4o-mini"},
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "embedding_dims": 1536,
            },
        },
    }


def init_mem0():
    """Initialize and return a Mem0 Memory instance with FalkorDB backend."""
    from mem0 import Memory
    from mem0_falkordb import register

    register()

    if not os.getenv("OPENAI_API_KEY"):
        console.print(
            "[red]Error: OPENAI_API_KEY not set![/red]\n"
            "Copy .env.example to .env and add your key:\n"
            "  cp .env.example .env\n"
            "  # edit .env with your OpenAI API key"
        )
        sys.exit(1)

    config = get_mem0_config()
    mode = os.getenv("FALKORDB_MODE", "docker")

    try:
        m = Memory.from_config(config)
        console.print(
            f"[green]✓ Connected to FalkorDB ({mode} mode)[/green]"
        )
        return m
    except Exception as e:
        console.print(
            f"[red]Failed to connect to FalkorDB ({mode} mode):[/red]\n{e}\n\n"
            "[yellow]Start FalkorDB with:[/yellow]\n"
            "  docker compose up -d"
        )
        sys.exit(1)
