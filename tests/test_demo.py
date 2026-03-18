"""Tests for demo.py — scripted demo scenes."""

from unittest.mock import MagicMock, patch

from demo import (
    DEVELOPERS,
    format_memories,
    get_graph_stats,
    scene_1_onboarding,
    scene_2_retrieval,
    scene_3_memory_update,
    scene_4_isolation_proof,
    scene_5_persistence,
    main,
)


class TestScene1Onboarding:
    def test_add_called_for_all_messages(self, mock_memory):
        """m.add is called once per message per developer (5×3 = 15)."""
        scene_1_onboarding(mock_memory)

        total_messages = sum(len(p["messages"]) for p in DEVELOPERS.values())
        assert mock_memory.add.call_count == total_messages
        assert total_messages == 15

    def test_returns_all_user_ids(self, mock_memory):
        """Returns a list containing all 3 developer ids."""
        user_ids = scene_1_onboarding(mock_memory)

        assert len(user_ids) == 3
        assert set(user_ids) == set(DEVELOPERS.keys())


class TestScene2Retrieval:
    def test_search_called_for_each_user_and_query(self, mock_memory):
        """3 queries × 3 users = 9 search calls (plus graph stats)."""
        user_ids = list(DEVELOPERS.keys())
        scene_2_retrieval(mock_memory, user_ids)

        # 3 queries × 3 users = 9, plus graph.get_all calls for stats
        assert mock_memory.search.call_count == 9


class TestScene3MemoryUpdate:
    def test_search_and_add_calls(self, mock_memory):
        """Scene 3 searches twice and adds the migration message."""
        scene_3_memory_update(mock_memory)

        assert mock_memory.search.call_count == 2
        assert mock_memory.add.call_count == 1
        # Verify migration message content
        add_call_args = mock_memory.add.call_args
        assert (
            "GraphQL" in add_call_args[0][0] or "migrate" in add_call_args[0][0].lower()
        )


class TestScene4IsolationProof:
    def test_searches_alice_and_carol(self, mock_memory):
        """Scene 4 searches for 'PyTorch deep learning' in alice and carol."""
        scene_4_isolation_proof(mock_memory)

        search_calls = mock_memory.search.call_args_list
        user_ids_searched = [
            call.kwargs.get("user_id") or call[1].get("user_id")
            for call in search_calls
        ]
        assert "alice" in user_ids_searched
        assert "carol" in user_ids_searched
        assert mock_memory.search.call_count == 2


class TestScene5Persistence:
    def test_creates_new_memory_and_searches(self, mock_memory):
        """Scene 5 creates a fresh Memory instance and searches on it."""
        new_mock = MagicMock()
        new_mock.search.return_value = [{"memory": "persisted memory", "id": "2"}]

        with patch("demo.init_mem0", return_value=new_mock):
            scene_5_persistence(mock_memory)

        # The new instance should have been used for 3 queries
        assert new_mock.search.call_count == 3


class TestMainCIMode:
    def test_ci_mode_skips_scenes(self, monkeypatch):
        """DEMO_CI_MODE=1 skips all scenes after initialization."""
        monkeypatch.setenv("DEMO_CI_MODE", "1")

        mock_mem = MagicMock()
        with patch("demo.init_mem0", return_value=mock_mem):
            main()

        # In CI mode, no scene functions are called — m.add/search never invoked
        mock_mem.add.assert_not_called()
        mock_mem.search.assert_not_called()


class TestHelpers:
    def test_format_memories_empty(self):
        assert "No memories found" in format_memories([])

    def test_format_memories_with_results(self):
        results = [{"memory": "likes Python"}, {"memory": "uses Django"}]
        output = format_memories(results)
        assert "likes Python" in output
        assert "uses Django" in output

    def test_get_graph_stats(self):
        m = MagicMock()
        m.graph.get_all.return_value = [
            {"source": "alice", "target": "python"},
            {"source": "alice", "target": "django"},
        ]
        nodes, rels = get_graph_stats(m, "alice")
        assert nodes == 3  # alice, python, django
        assert rels == 2

    def test_get_graph_stats_exception(self):
        m = MagicMock()
        m.graph.get_all.side_effect = Exception("connection error")
        nodes, rels = get_graph_stats(m, "alice")
        assert nodes == 0
        assert rels == 0
