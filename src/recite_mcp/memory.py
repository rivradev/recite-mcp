from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from recite_mcp.models import MemoryEntry, utc_now_iso


class MemoryRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_file(self) -> None:
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def add_instruction(
        self, instruction: str, tags: list[str] | None = None
    ) -> MemoryEntry:
        self._ensure_file()
        normalized = instruction.strip().lower()
        existing = self.list_instructions()

        for entry in existing:
            if entry.instruction.strip().lower() == normalized:
                entry.timestamp_utc = utc_now_iso()
                entry.tags = tags or entry.tags
                self._rewrite_all(existing)
                return entry

        entry = MemoryEntry(
            timestamp_utc=utc_now_iso(), instruction=instruction, tags=tags or []
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
        return entry

    def _rewrite_all(self, entries: list[MemoryEntry]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(asdict(entry)) + "\n")

    def list_instructions(self) -> list[MemoryEntry]:
        self._ensure_file()
        entries: list[MemoryEntry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            entries.append(
                MemoryEntry(
                    timestamp_utc=str(payload["timestamp_utc"]),
                    instruction=str(payload["instruction"]),
                    tags=list(payload.get("tags", [])),
                )
            )
        return entries
