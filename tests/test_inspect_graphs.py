"""Tests for inspect_graphs.py — graph inspector utilities."""

from unittest.mock import MagicMock

from inspect_graphs import (
    extract_user_id,
    format_node_properties,
    get_all_mem0_graphs,
)


class TestGetAllMem0Graphs:
    def test_filters_by_prefix(self):
        """Only graphs starting with 'mem0_' are returned."""
        mock_db = MagicMock()
        mock_db.list_graphs.return_value = [
            "mem0_alice",
            "mem0_bob",
            "other_graph",
            "mem0_carol",
        ]

        result = get_all_mem0_graphs(mock_db, database_prefix="mem0")

        assert result == ["mem0_alice", "mem0_bob", "mem0_carol"]
        assert "other_graph" not in result

    def test_custom_prefix(self):
        """Supports a custom database prefix."""
        mock_db = MagicMock()
        mock_db.list_graphs.return_value = ["custom_alice", "mem0_bob"]

        result = get_all_mem0_graphs(mock_db, database_prefix="custom")
        assert result == ["custom_alice"]

    def test_empty_list(self):
        """Returns empty list when no graphs match."""
        mock_db = MagicMock()
        mock_db.list_graphs.return_value = ["unrelated_graph"]

        result = get_all_mem0_graphs(mock_db)
        assert result == []


class TestExtractUserId:
    def test_strips_prefix(self):
        assert extract_user_id("mem0_alice") == "alice"
        assert extract_user_id("mem0_bob") == "bob"

    def test_custom_prefix(self):
        assert extract_user_id("custom_carol", database_prefix="custom") == "carol"

    def test_no_matching_prefix(self):
        """Returns full name when prefix doesn't match."""
        assert extract_user_id("other_graph") == "other_graph"

    def test_compound_user_id(self):
        """Handles user IDs that themselves contain underscores."""
        assert extract_user_id("mem0_user_123") == "user_123"


class TestFormatNodeProperties:
    def test_formats_properties(self):
        node = MagicMock()
        node.properties = {"name": "alice", "role": "engineer"}
        result = format_node_properties(node)
        assert "name=" in result
        assert "role=" in result

    def test_filters_embedding(self):
        """Embedding vectors are excluded from display."""
        node = MagicMock()
        node.properties = {"name": "alice", "embedding": [0.1, 0.2, 0.3]}
        result = format_node_properties(node)
        assert "embedding" not in result
        assert "name=" in result

    def test_no_properties_attr(self):
        """Returns empty string for objects without properties."""
        node = object()
        result = format_node_properties(node)
        assert result == ""

    def test_empty_properties_after_filter(self):
        """Returns empty string when only embedding property exists."""
        node = MagicMock()
        node.properties = {"embedding": [0.1]}
        result = format_node_properties(node)
        assert result == ""
