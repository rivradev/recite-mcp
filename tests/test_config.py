from __future__ import annotations

from pathlib import Path

import pytest

from recite_mcp.config import ConfigError, Settings, load_settings


def test_load_settings_prefers_env_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "recite"
    home.mkdir()
    (home / "config.toml").write_text('api_key = "from_file"\n', encoding="utf-8")
    monkeypatch.setenv("RECITE_HOME", str(home))
    monkeypatch.setenv("RECITE_API_KEY", "from_env")

    settings = load_settings()

    assert settings.api_key == "from_env"
    assert settings.recite_home == home


def test_load_settings_uses_file_api_key_when_env_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "recite"
    home.mkdir()
    (home / "config.toml").write_text('api_key = "from_file"\napi_base_url = "https://example.test"\n', encoding="utf-8")
    monkeypatch.setenv("RECITE_HOME", str(home))
    monkeypatch.delenv("RECITE_API_KEY", raising=False)

    settings = load_settings()

    assert settings.api_key == "from_file"
    assert settings.api_base_url == "https://example.test"


def test_load_settings_raises_without_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RECITE_HOME", str(tmp_path / "recite"))
    monkeypatch.delenv("RECITE_API_KEY", raising=False)

    with pytest.raises(ConfigError):
        load_settings(require_api_key=True)


def test_settings_paths_are_derived_from_home(tmp_path: Path) -> None:
    settings = Settings(
        recite_home=tmp_path,
        api_key="test",
        api_base_url="https://recite.rivra.dev",
        request_timeout_sec=30,
    )

    assert settings.ledger_path == tmp_path / "bookkeeping_transactions.csv"
    assert settings.memory_path == tmp_path / "long_term_memory.md"
