"""Memory system — file-based long-term memory for FletBot.

Adapted from adkbot's MemoryStore pattern:
- ``MEMORY.md`` for long-term facts the AI remembers about the user
- ``history.jsonl`` for conversation summaries across sessions
- Context injection for the system prompt

Consumer-simplified: no Git, no Dream, no Consolidator.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Hard cap on individual history entries to prevent unbounded growth.
HISTORY_ENTRY_HARD_CAP = 16_000

# Default max entries in history.jsonl before compaction drops oldest.
DEFAULT_MAX_HISTORY = 200


class MemoryStore:
    """Pure file I/O layer for persistent memory.

    Files managed:
    - ``storage/memory/MEMORY.md`` — long-term user facts
    - ``storage/memory/history.jsonl`` — conversation summaries (JSONL)
    - ``storage/memory/.cursor`` — auto-incrementing cursor counter
    """

    def __init__(
        self,
        storage_dir: str | Path | None = None,
        max_history_entries: int = DEFAULT_MAX_HISTORY,
    ):
        if storage_dir is None:
            storage_dir = (
                Path(__file__).parent.parent.parent / "storage" / "memory"
            )
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

        self.max_history_entries = max_history_entries
        self.memory_file = self._dir / "MEMORY.md"
        self.history_file = self._dir / "history.jsonl"
        self._cursor_file = self._dir / ".cursor"

    # ── MEMORY.md (long-term facts) ─────────────────────────────────

    def read_memory(self) -> str:
        """Read the long-term memory file."""
        return self._read_file(self.memory_file)

    def write_memory(self, content: str) -> None:
        """Overwrite the long-term memory file."""
        self.memory_file.write_text(content, encoding="utf-8")

    def append_memory(self, fact: str) -> None:
        """Append a fact to the memory file."""
        existing = self.read_memory()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n- [{timestamp}] {fact.strip()}"
        self.memory_file.write_text(
            existing + entry, encoding="utf-8"
        )

    # ── Context injection ───────────────────────────────────────────

    def get_memory_context(self) -> str:
        """Return memory formatted for injection into the system prompt."""
        long_term = self.read_memory().strip()
        if not long_term:
            return ""
        return f"## Long-term Memory\n{long_term}"

    # ── history.jsonl — append-only conversation summaries ──────────

    def append_history(
        self, entry: str, *, max_chars: int | None = None
    ) -> int:
        """Append an entry to history.jsonl and return its cursor.

        Each entry is a JSON object with: cursor, timestamp, content.
        """
        limit = max_chars if max_chars is not None else HISTORY_ENTRY_HARD_CAP
        cursor = self._next_cursor()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")

        content = entry.rstrip()
        if len(content) > limit:
            logger.warning(
                "History entry exceeds %d chars (%d); truncating.",
                limit,
                len(content),
            )
            content = content[:limit] + "\n... (truncated)"

        record = {"cursor": cursor, "timestamp": ts, "content": content}
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._cursor_file.write_text(str(cursor), encoding="utf-8")
        return cursor

    def read_history(self, since_cursor: int = 0) -> list[dict[str, Any]]:
        """Return history entries with cursor > since_cursor."""
        entries = self._read_entries()
        return [e for e in entries if e.get("cursor", 0) > since_cursor]

    def compact_history(self) -> None:
        """Drop oldest entries if file exceeds max_history_entries."""
        if self.max_history_entries <= 0:
            return
        entries = self._read_entries()
        if len(entries) <= self.max_history_entries:
            return
        kept = entries[-self.max_history_entries :]
        self._write_entries(kept)

    def get_recent_history_context(self, max_entries: int = 5) -> str:
        """Return recent history summaries for context injection."""
        entries = self._read_entries()
        if not entries:
            return ""
        recent = entries[-max_entries:]
        lines = []
        for e in recent:
            lines.append(f"- [{e.get('timestamp', '?')}] {e.get('content', '')}")
        return "## Recent Conversation History\n" + "\n".join(lines)

    # ── JSONL helpers ───────────────────────────────────────────────

    def _read_entries(self) -> list[dict[str, Any]]:
        """Read all entries from history.jsonl."""
        entries: list[dict[str, Any]] = []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        return entries

    def _write_entries(self, entries: list[dict[str, Any]]) -> None:
        """Overwrite history.jsonl with the given entries."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _next_cursor(self) -> int:
        """Read cursor counter and return next value."""
        if self._cursor_file.exists():
            try:
                return (
                    int(self._cursor_file.read_text(encoding="utf-8").strip())
                    + 1
                )
            except (ValueError, OSError):
                pass
        # Fall back to scanning history entries
        entries = self._read_entries()
        if entries:
            cursors = [
                e["cursor"]
                for e in entries
                if isinstance(e.get("cursor"), int)
            ]
            if cursors:
                return max(cursors) + 1
        return 1

    # ── Generic helpers ─────────────────────────────────────────────

    @staticmethod
    def _read_file(path: Path) -> str:
        """Read a text file, returning empty string if missing."""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
