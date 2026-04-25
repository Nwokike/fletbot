"""Session manager — local conversation storage."""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Session:
    """A conversation session."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = "New Chat"
    messages: list[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def last_message_preview(self) -> str:
        """Get a preview of the last message."""
        if not self.messages:
            return ""
        last = self.messages[-1]
        preview = last.content[:80].replace("\n", " ")
        return preview + "..." if len(last.content) > 80 else preview

    def add_message(self, role: str, content: str) -> Message:
        """Add a message and update metadata."""
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        self.updated_at = time.time()

        # Auto-title from first user message
        if self.title == "New Chat" and role == "user":
            self.title = content[:50].replace("\n", " ")
            if len(content) > 50:
                self.title += "..."

        return msg

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "messages": [asdict(m) for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        messages = [
            Message(
                role=m["role"],
                content=m["content"],
                timestamp=m.get("timestamp", 0),
            )
            for m in data.get("messages", [])
        ]
        return cls(
            id=data["id"],
            title=data.get("title", "New Chat"),
            messages=messages,
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
        )


class SessionManager:
    """Manages conversation sessions stored as local JSON files."""

    def __init__(self, storage_dir: str | Path | None = None):
        if storage_dir is None:
            # Default to storage/data relative to project root
            storage_dir = Path(__file__).parent.parent.parent / "storage" / "data"
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self._dir / f"session_{session_id}.json"

    def create_session(self) -> Session:
        """Create a new empty session."""
        session = Session()
        self.save(session)
        logger.info("Created new session: %s", session.id)
        return session

    def save(self, session: Session) -> None:
        """Persist a session to disk."""
        path = self._session_path(session.id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed to save session %s: %s", session.id, e)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Load a session by ID."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception as e:
            logger.error("Failed to load session %s: %s", session_id, e)
            return None

    def list_sessions(self) -> list[Session]:
        """List all sessions, sorted by most recent first."""
        sessions = []
        for path in self._dir.glob("session_*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(Session.from_dict(data))
            except Exception as e:
                logger.warning("Skipping corrupt session file %s: %s", path, e)

        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        path = self._session_path(session_id)
        if path.exists():
            try:
                os.remove(path)
                logger.info("Deleted session: %s", session_id)
                return True
            except Exception as e:
                logger.error("Failed to delete session %s: %s", session_id, e)
        return False

    def clear_all(self) -> int:
        """Delete all sessions. Returns count of deleted sessions."""
        count = 0
        for path in self._dir.glob("session_*.json"):
            try:
                os.remove(path)
                count += 1
            except Exception:
                pass
        return count
