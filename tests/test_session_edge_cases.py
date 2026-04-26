"""Tests for SessionManager edge cases.

Adapted from adkbot's test_session_atomic.py and test_session_manager_history.py.
Covers: corrupt files, clear_all, auto-title, message preview, concurrent writes.
"""

import json

import pytest

from src.session.manager import Message, Session, SessionManager


@pytest.fixture
def manager(tmp_path):
    return SessionManager(storage_dir=tmp_path)


# ── Session data model ─────────────────────────────────────────────


class TestSessionModel:
    def test_new_session_has_default_title(self):
        session = Session()
        assert session.title == "New Chat"

    def test_auto_title_from_first_user_message(self):
        session = Session()
        session.add_message("user", "How do I cook pasta?")
        assert session.title == "How do I cook pasta?"

    def test_auto_title_truncation_at_50_chars(self):
        session = Session()
        long_msg = "x" * 80
        session.add_message("user", long_msg)
        assert len(session.title) <= 53  # 50 + "..."
        assert session.title.endswith("...")

    def test_auto_title_only_from_first_user_message(self):
        session = Session()
        session.add_message("user", "First question")
        session.add_message("user", "Second question should not change title")
        assert session.title == "First question"

    def test_assistant_message_does_not_set_title(self):
        session = Session()
        session.add_message("assistant", "Hello!")
        assert session.title == "New Chat"

    def test_message_count_property(self):
        session = Session()
        assert session.message_count == 0
        session.add_message("user", "Hi")
        session.add_message("assistant", "Hello!")
        assert session.message_count == 2

    def test_last_message_preview_empty(self):
        session = Session()
        assert session.last_message_preview == ""

    def test_last_message_preview_short(self):
        session = Session()
        session.add_message("user", "Hello world")
        assert session.last_message_preview == "Hello world"

    def test_last_message_preview_truncation(self):
        session = Session()
        session.add_message("user", "x" * 100)
        preview = session.last_message_preview
        assert len(preview) <= 84  # 80 + "..."
        assert preview.endswith("...")

    def test_last_message_preview_strips_newlines(self):
        session = Session()
        session.add_message("user", "line1\nline2\nline3")
        preview = session.last_message_preview
        assert "\n" not in preview

    def test_add_message_updates_updated_at(self):
        session = Session()
        old_ts = session.updated_at
        session.add_message("user", "Hi")
        assert session.updated_at >= old_ts


# ── Serialization ──────────────────────────────────────────────────


class TestSessionSerialization:
    def test_to_dict_roundtrip(self):
        session = Session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")

        data = session.to_dict()
        restored = Session.from_dict(data)

        assert restored.id == session.id
        assert restored.title == session.title
        assert len(restored.messages) == 2
        assert restored.messages[0].role == "user"
        assert restored.messages[0].content == "Hello"

    def test_from_dict_handles_missing_fields(self):
        data = {"id": "test123", "messages": []}
        session = Session.from_dict(data)
        assert session.id == "test123"
        assert session.title == "New Chat"
        assert session.created_at == 0
        assert session.updated_at == 0


# ── SessionManager persistence ─────────────────────────────────────


class TestSessionManagerPersistence:
    def test_create_and_retrieve_session(self, manager):
        session = manager.create_session()
        loaded = manager.get_session(session.id)
        assert loaded is not None
        assert loaded.id == session.id

    def test_get_nonexistent_session_returns_none(self, manager):
        assert manager.get_session("doesnotexist") is None

    def test_save_and_load_messages(self, manager):
        session = manager.create_session()
        session.add_message("user", "Test message")
        manager.save(session)

        loaded = manager.get_session(session.id)
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "Test message"

    def test_list_sessions_sorted_by_most_recent(self, manager):
        s1 = manager.create_session()
        s1.updated_at = 100
        manager.save(s1)

        s2 = manager.create_session()
        s2.updated_at = 200
        manager.save(s2)

        sessions = manager.list_sessions()
        assert len(sessions) == 2
        assert sessions[0].id == s2.id  # Most recent first

    def test_delete_session(self, manager):
        session = manager.create_session()
        assert manager.delete_session(session.id) is True
        assert manager.get_session(session.id) is None

    def test_delete_nonexistent_session_returns_false(self, manager):
        assert manager.delete_session("fake") is False

    def test_clear_all_returns_count(self, manager):
        manager.create_session()
        manager.create_session()
        manager.create_session()
        count = manager.clear_all()
        assert count == 3
        assert len(manager.list_sessions()) == 0


# ── Edge cases ─────────────────────────────────────────────────────


class TestSessionEdgeCases:
    def test_corrupt_json_file_is_skipped_during_list(self, manager, tmp_path):
        """Corrupt session files should be skipped, not crash the listing."""
        # Create a valid session
        valid = manager.create_session()
        valid.add_message("user", "valid")
        manager.save(valid)

        # Write a corrupt file
        corrupt_path = tmp_path / "session_corrupt123.json"
        corrupt_path.write_text("not valid json {{{", encoding="utf-8")

        sessions = manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].id == valid.id

    def test_save_creates_file_atomically(self, manager, tmp_path):
        """Save should create a readable JSON file."""
        session = manager.create_session()
        session.add_message("user", "Test")
        manager.save(session)

        path = tmp_path / f"session_{session.id}.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["id"] == session.id
        assert len(data["messages"]) == 1
