"""Tests for MemoryStore — adapted from adkbot's test_memory_store.py.

Covers:
- MEMORY.md read/write/append
- history.jsonl cursor-based append, read, compact
- Context injection formatting
- Edge cases: empty files, oversized entries, cursor recovery
"""

import json

import pytest

from src.agent.memory import (
    DEFAULT_MAX_HISTORY,
    HISTORY_ENTRY_HARD_CAP,
    MemoryStore,
)


@pytest.fixture
def store(tmp_path):
    return MemoryStore(storage_dir=tmp_path)


# ── MEMORY.md basic I/O ────────────────────────────────────────────


class TestMemoryBasicIO:
    def test_read_memory_returns_empty_when_missing(self, store):
        assert store.read_memory() == ""

    def test_write_and_read_memory(self, store):
        store.write_memory("hello")
        assert store.read_memory() == "hello"

    def test_write_overwrites_previous(self, store):
        store.write_memory("first")
        store.write_memory("second")
        assert store.read_memory() == "second"

    def test_append_memory_adds_timestamped_entry(self, store):
        store.append_memory("User prefers dark mode")
        content = store.read_memory()
        assert "User prefers dark mode" in content
        assert "[" in content  # timestamp marker

    def test_append_memory_preserves_existing(self, store):
        store.write_memory("# User Facts")
        store.append_memory("Likes Python")
        content = store.read_memory()
        assert "# User Facts" in content
        assert "Likes Python" in content


# ── Context injection ──────────────────────────────────────────────


class TestMemoryContext:
    def test_get_memory_context_returns_empty_when_no_memory(self, store):
        assert store.get_memory_context() == ""

    def test_get_memory_context_includes_header_and_content(self, store):
        store.write_memory("User is a Python developer")
        ctx = store.get_memory_context()
        assert "Long-term Memory" in ctx
        assert "User is a Python developer" in ctx

    def test_get_recent_history_context_returns_empty_when_no_history(
        self, store
    ):
        assert store.get_recent_history_context() == ""

    def test_get_recent_history_context_includes_entries(self, store):
        store.append_history("Discussed weather")
        store.append_history("Talked about cooking")
        ctx = store.get_recent_history_context()
        assert "Recent Conversation History" in ctx
        assert "Discussed weather" in ctx
        assert "Talked about cooking" in ctx

    def test_get_recent_history_context_respects_max_entries(self, store):
        for i in range(10):
            store.append_history(f"event {i}")
        ctx = store.get_recent_history_context(max_entries=3)
        # Should only contain last 3 entries
        assert "event 7" in ctx
        assert "event 8" in ctx
        assert "event 9" in ctx
        assert "event 0" not in ctx


# ── history.jsonl with cursors ─────────────────────────────────────


class TestHistoryWithCursor:
    def test_append_history_returns_cursor(self, store):
        cursor = store.append_history("event 1")
        assert cursor == 1
        cursor2 = store.append_history("event 2")
        assert cursor2 == 2

    def test_append_history_includes_cursor_in_file(self, store):
        store.append_history("event 1")
        content = store._read_file(store.history_file)
        data = json.loads(content.strip())
        assert data["cursor"] == 1

    def test_cursor_persists_across_appends(self, store):
        store.append_history("event 1")
        store.append_history("event 2")
        cursor = store.append_history("event 3")
        assert cursor == 3

    def test_read_history_returns_all_when_cursor_zero(self, store):
        store.append_history("event 1")
        store.append_history("event 2")
        entries = store.read_history(since_cursor=0)
        assert len(entries) == 2

    def test_read_history_filters_by_cursor(self, store):
        store.append_history("event 1")
        store.append_history("event 2")
        store.append_history("event 3")
        entries = store.read_history(since_cursor=1)
        assert len(entries) == 2
        assert entries[0]["cursor"] == 2

    def test_read_history_returns_empty_when_no_file(self, store):
        entries = store.read_history()
        assert entries == []


# ── History compaction ─────────────────────────────────────────────


class TestHistoryCompaction:
    def test_compact_history_drops_oldest(self, tmp_path):
        store = MemoryStore(storage_dir=tmp_path, max_history_entries=2)
        store.append_history("event 1")
        store.append_history("event 2")
        store.append_history("event 3")
        store.append_history("event 4")
        store.compact_history()
        entries = store.read_history(since_cursor=0)
        assert len(entries) == 2
        assert entries[0]["cursor"] in {3, 4}

    def test_compact_noop_when_under_limit(self, store):
        store.append_history("event 1")
        store.append_history("event 2")
        store.compact_history()
        entries = store.read_history(since_cursor=0)
        assert len(entries) == 2


# ── Hard cap on entry size ─────────────────────────────────────────


class TestHistoryHardCap:
    def test_oversized_entry_is_truncated(self, store):
        huge = "x" * (HISTORY_ENTRY_HARD_CAP + 10_000)
        store.append_history(huge)
        entry = store.read_history(since_cursor=0)[0]
        assert len(entry["content"]) <= HISTORY_ENTRY_HARD_CAP + 50

    def test_custom_max_chars_overrides_default(self, store):
        store.append_history("a" * 500, max_chars=100)
        entry = store.read_history(since_cursor=0)[0]
        assert len(entry["content"]) <= 150  # 100 + "\n... (truncated)"

    def test_normal_sized_entries_unaffected(self, store):
        msg = "normal short entry"
        store.append_history(msg)
        entry = store.read_history(since_cursor=0)[0]
        assert entry["content"] == msg


# ── Cursor recovery ────────────────────────────────────────────────


class TestCursorRecovery:
    def test_next_cursor_recovers_from_missing_cursor_file(self, store):
        store.append_history("event 1")
        store.append_history("event 2")
        # Delete the cursor file
        store._cursor_file.unlink(missing_ok=True)
        # Should recover from scanning history entries
        cursor = store.append_history("event 3")
        assert cursor == 3

    def test_next_cursor_recovers_from_corrupt_cursor_file(self, store):
        store.append_history("event 1")
        # Corrupt the cursor file
        store._cursor_file.write_text("not_a_number", encoding="utf-8")
        cursor = store.append_history("event 2")
        assert cursor == 2

    def test_next_cursor_starts_at_1_for_empty_store(self, store):
        cursor = store.append_history("first event")
        assert cursor == 1


# ── JSONL edge cases ───────────────────────────────────────────────


class TestJSONLEdgeCases:
    def test_read_entries_skips_corrupt_json_lines(self, store):
        with open(store.history_file, "w", encoding="utf-8") as f:
            f.write('{"cursor": 1, "content": "valid"}\n')
            f.write("not valid json\n")
            f.write('{"cursor": 2, "content": "also valid"}\n')
        entries = store.read_history(since_cursor=0)
        assert len(entries) == 2

    def test_read_entries_handles_empty_file(self, store):
        store.history_file.write_text("", encoding="utf-8")
        entries = store.read_history(since_cursor=0)
        assert entries == []
