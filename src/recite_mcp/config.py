from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


class ConfigError(RuntimeError):
    pass


@dataclass(slots=True)
class Settings:
    recite_home: Path
    api_key: str | None
    api_base_url: str
    request_timeout_sec: int

    @property
    def ledger_path(self) -> Path:
        return self.recite_home / "bookkeeping_transactions.csv"

    @property
    def memory_path(self) -> Path:
        return self.recite_home / "long_term_memory.md"


def _default_home() -> Path:
    return Path(os.environ.get("RECITE_HOME", Path.home() / ".config" / "recite")).expanduser()


def _load_config_file(home: Path) -> dict:
    config_file = home / "config.toml"
    if not config_file.exists():
        return {}
    return tomllib.loads(config_file.read_text(encoding="utf-8"))


def load_settings(require_api_key: bool = True) -> Settings:
    home = _default_home()
    home.mkdir(parents=True, exist_ok=True)
    config = _load_config_file(home)

    env_key = os.environ.get("RECITE_API_KEY")
    api_key = env_key or config.get("api_key")

    if require_api_key and not api_key:
        raise ConfigError("Missing API key. Set RECITE_API_KEY or RECITE_HOME/config.toml api_key.")

    api_base_url = str(config.get("api_base_url", "https://recite.rivra.dev/apiV1/api/v1")).rstrip("/")
    request_timeout_sec = int(config.get("request_timeout_sec", 30))

    return Settings(
        recite_home=home,
        api_key=api_key,
        api_base_url=api_base_url,
        request_timeout_sec=request_timeout_sec,
    )
