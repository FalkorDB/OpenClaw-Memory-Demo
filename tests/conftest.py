"""Shared pytest fixtures for the OpenClaw Memory Demo test suite."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def mock_memory():
    """Return a MagicMock mimicking mem0.Memory."""
    m = MagicMock()
    m.add.return_value = {"id": "test-id"}
    m.search.return_value = [{"memory": "test memory", "id": "1"}]
    m.get_all.return_value = [{"memory": "test memory", "id": "1"}]
    m.delete.return_value = None
    m.graph.get_all.return_value = [
        {"source": "alice", "target": "python", "relationship": "PREFERS"}
    ]
    return m


@pytest.fixture()
def mock_env(monkeypatch):
    """Set required env vars for tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("FALKORDB_MODE", "docker")
