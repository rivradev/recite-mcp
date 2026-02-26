from __future__ import annotations

from dataclasses import asdict

from recite_mcp.config import Settings
from recite_mcp.ledger import LedgerRepository


class ResourceProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ledger = LedgerRepository(settings.ledger_path)

    def get_ledger_rows(self) -> list[dict]:
        return [asdict(row) for row in self._ledger.read_all()]

    def get_memory_text(self) -> str:
        if not self._settings.memory_path.exists():
            return ""
        return self._settings.memory_path.read_text(encoding="utf-8")

    def get_health(self) -> dict:
        issues: list[str] = []
        if not self._settings.api_key:
            issues.append("missing_api_key")
        status = "ok" if not issues else "degraded"
        return {
            "status": status,
            "recite_home": str(self._settings.recite_home),
            "ledger_path": str(self._settings.ledger_path),
            "memory_path": str(self._settings.memory_path),
            "has_api_key": bool(self._settings.api_key),
            "issues": issues,
        }
