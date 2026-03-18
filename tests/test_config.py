"""Smoke tests for the OpenClaw Memory Demo configuration module."""

import os
from unittest.mock import patch

from config import get_falkordb_config, get_mem0_config


def test_get_falkordb_config_defaults():
    """Default config returns docker mode with localhost:6379."""
    with patch.dict(os.environ, {}, clear=True):
        cfg = get_falkordb_config()
    assert cfg["host"] == "localhost"
    assert cfg["port"] == 6379
    assert cfg["database"] == "mem0"
    assert "username" not in cfg
    assert "password" not in cfg


def test_get_falkordb_config_custom_host():
    """Custom host and port are picked up from env vars."""
    env = {"FALKORDB_HOST": "db.example.com", "FALKORDB_PORT": "6380"}
    with patch.dict(os.environ, env, clear=True):
        cfg = get_falkordb_config()
    assert cfg["host"] == "db.example.com"
    assert cfg["port"] == 6380


def test_get_falkordb_config_cloud_mode():
    """Cloud mode includes username and password."""
    env = {
        "FALKORDB_MODE": "cloud",
        "FALKORDB_USERNAME": "admin",
        "FALKORDB_PASSWORD": "secret",
    }
    with patch.dict(os.environ, env, clear=True):
        cfg = get_falkordb_config()
    assert cfg["username"] == "admin"
    assert cfg["password"] == "secret"


def test_get_mem0_config_structure():
    """Mem0 config contains the expected top-level keys."""
    cfg = get_mem0_config()
    assert "graph_store" in cfg
    assert "llm" in cfg
    assert "embedder" in cfg
    assert cfg["graph_store"]["provider"] == "falkordb"
    assert cfg["llm"]["provider"] == "openai"
    assert cfg["embedder"]["provider"] == "openai"
