"""Tests for config.py — FalkorDB and Mem0 configuration."""

from unittest.mock import MagicMock, patch

import pytest

from config import get_falkordb_config, get_mem0_config, init_mem0


class TestGetFalkordbConfig:
    def test_get_falkordb_config_docker(self, monkeypatch):
        """Docker mode returns localhost:6379 with no credentials."""
        monkeypatch.setenv("FALKORDB_MODE", "docker")
        monkeypatch.delenv("FALKORDB_HOST", raising=False)
        monkeypatch.delenv("FALKORDB_PORT", raising=False)

        cfg = get_falkordb_config()

        assert cfg["host"] == "localhost"
        assert cfg["port"] == 6379
        assert cfg["database"] == "mem0"
        assert "username" not in cfg
        assert "password" not in cfg

    def test_get_falkordb_config_cloud(self, monkeypatch):
        """Cloud mode includes username and password."""
        monkeypatch.setenv("FALKORDB_MODE", "cloud")
        monkeypatch.setenv("FALKORDB_USERNAME", "myuser")
        monkeypatch.setenv("FALKORDB_PASSWORD", "secret")

        cfg = get_falkordb_config()

        assert cfg["username"] == "myuser"
        assert cfg["password"] == "secret"

    def test_get_falkordb_config_cloud_missing_password(self, monkeypatch):
        """Cloud mode exits if FALKORDB_PASSWORD is missing."""
        monkeypatch.setenv("FALKORDB_MODE", "cloud")
        monkeypatch.delenv("FALKORDB_PASSWORD", raising=False)

        with pytest.raises(SystemExit):
            get_falkordb_config()


class TestGetMem0Config:
    def test_get_mem0_config_structure(self, monkeypatch):
        """Config dict has the correct top-level keys and providers."""
        monkeypatch.setenv("FALKORDB_MODE", "docker")

        cfg = get_mem0_config()

        assert "graph_store" in cfg
        assert "llm" in cfg
        assert "embedder" in cfg
        assert cfg["graph_store"]["provider"] == "falkordb"
        assert cfg["llm"]["provider"] == "openai"
        assert cfg["embedder"]["provider"] == "openai"


class TestInitMem0:
    def test_init_mem0_missing_api_key(self, monkeypatch):
        """init_mem0() exits when OPENAI_API_KEY is not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(SystemExit):
            init_mem0()

    def test_init_mem0_success(self, monkeypatch):
        """init_mem0() registers falkordb and returns a Memory instance."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("FALKORDB_MODE", "docker")

        mock_memory_cls = MagicMock()
        fake_memory = MagicMock()
        mock_memory_cls.from_config.return_value = fake_memory
        mock_register = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "mem0": MagicMock(Memory=mock_memory_cls),
                "mem0_falkordb": MagicMock(register=mock_register),
            },
        ):
            result = init_mem0()

        assert result is fake_memory
