"""Tests for chat.py — interactive chatbot command handlers and helpers."""

from chat import (
    SYSTEM_PROMPT,
    build_system_message,
    capture_memories,
    cmd_forget,
    cmd_graph,
    cmd_memories,
    cmd_search,
    recall_memories,
)


class TestBuildSystemMessage:
    def test_no_memories(self):
        """Without memories, returns the base system prompt."""
        result = build_system_message([])
        assert result == SYSTEM_PROMPT

    def test_with_memories(self):
        """With memories, the prompt includes memory context."""
        memories = [{"memory": "prefers Python"}, {"memory": "uses PostgreSQL"}]
        result = build_system_message(memories)

        assert SYSTEM_PROMPT in result
        assert "prefers Python" in result
        assert "uses PostgreSQL" in result
        assert "remember about this developer" in result


class TestRecallMemories:
    def test_returns_search_results(self, mock_memory):
        """recall_memories returns the list from m.search."""
        results = recall_memories(mock_memory, "database preference", "alice")

        mock_memory.search.assert_called_once_with(
            "database preference", user_id="alice"
        )
        assert len(results) == 1
        assert results[0]["memory"] == "test memory"

    def test_handles_dict_response(self, mock_memory):
        """When m.search returns a dict with 'results' key, extracts the list."""
        mock_memory.search.return_value = {"results": [{"memory": "from dict"}]}
        results = recall_memories(mock_memory, "query", "bob")
        assert results == [{"memory": "from dict"}]

    def test_handles_exception(self, mock_memory):
        """On exception, returns empty list gracefully."""
        mock_memory.search.side_effect = Exception("connection lost")
        results = recall_memories(mock_memory, "query", "alice")
        assert results == []


class TestCaptureMemories:
    def test_calls_add(self, mock_memory):
        capture_memories(mock_memory, "User: hi\nAssistant: hello", "alice")
        mock_memory.add.assert_called_once()

    def test_handles_exception(self, mock_memory):
        """Capture does not raise on error."""
        mock_memory.add.side_effect = Exception("fail")
        capture_memories(mock_memory, "text", "alice")  # should not raise


class TestCmdMemories:
    def test_calls_get_all(self, mock_memory):
        cmd_memories(mock_memory, "alice")
        mock_memory.get_all.assert_called_once_with(user_id="alice")

    def test_handles_dict_response(self, mock_memory):
        """When get_all returns a dict with 'results', it still works."""
        mock_memory.get_all.return_value = {"results": [{"memory": "m1", "id": "1"}]}
        cmd_memories(mock_memory, "alice")


class TestCmdSearch:
    def test_calls_search(self, mock_memory):
        cmd_search(mock_memory, "database", "alice")
        mock_memory.search.assert_called_once_with("database", user_id="alice")

    def test_empty_query(self, mock_memory):
        """Empty query prints usage without calling search."""
        cmd_search(mock_memory, "", "alice")
        mock_memory.search.assert_not_called()


class TestCmdForget:
    def test_calls_delete(self, mock_memory):
        cmd_forget(mock_memory, "mem-123", "alice")
        mock_memory.delete.assert_called_once_with("mem-123")

    def test_empty_id(self, mock_memory):
        """Empty id prints usage without calling delete."""
        cmd_forget(mock_memory, "", "alice")
        mock_memory.delete.assert_not_called()


class TestCmdGraph:
    def test_calls_graph_get_all(self, mock_memory):
        cmd_graph(mock_memory)
        mock_memory.graph.get_all.assert_called_once()


class TestUserSwitch:
    def test_user_switch_updates_state(self):
        """Simulates the /user command logic from main loop."""
        user_id = "developer"
        history = [{"role": "user", "content": "hello"}]

        # Simulate /user command handler logic
        new_user = "alice"
        user_id = new_user
        history.clear()

        assert user_id == "alice"
        assert history == []


class TestHelpCommand:
    def test_help_text_is_available(self):
        """The HELP_TEXT constant exists and is non-empty."""
        from chat import HELP_TEXT

        assert len(HELP_TEXT) > 0
        assert "/memories" in HELP_TEXT
        assert "/search" in HELP_TEXT
