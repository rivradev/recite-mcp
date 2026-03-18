from __future__ import annotations

from pathlib import Path

from recite_mcp.config import Settings
from recite_mcp.resources import ResourceProvider


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        recite_home=tmp_path,
        api_key="x",
        api_base_url="https://example",
        request_timeout_sec=20,
    )


def test_health_resource_reports_ok(tmp_path: Path) -> None:
    provider = ResourceProvider(_settings(tmp_path))
    health = provider.get_health()

    assert health["status"] == "ok"
    assert health["has_api_key"] is True
    assert health["issues"] == []


def test_health_resource_reports_missing_api_key(tmp_path: Path) -> None:
    settings = Settings(
        recite_home=tmp_path,
        api_key=None,
        api_base_url="https://example",
        request_timeout_sec=20,
    )
    provider = ResourceProvider(settings)
    health = provider.get_health()

    assert health["status"] == "degraded"
    assert health["has_api_key"] is False
    assert "missing_api_key" in health["issues"]


def test_memory_resource_reads_file(tmp_path: Path) -> None:
    memory_file = tmp_path / "long_term_memory.md"
    memory_file.write_text("hello", encoding="utf-8")
    provider = ResourceProvider(_settings(tmp_path))

    assert provider.get_memory_text() == "hello"
