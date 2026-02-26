from __future__ import annotations

import sys
import uuid
from pathlib import Path
from shutil import rmtree

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def tmp_path() -> Path:  # type: ignore[override]
    """
    Replacement for pytest's built-in tmp_path fixture.

    Some Windows environments apply restrictive ACLs to pytest-managed temp roots,
    causing PermissionError during setup/cleanup. This fixture keeps test temp
    dirs under the repo (and uses best-effort cleanup) to improve reliability.
    """

    base = ROOT / "_test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    path = base / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        rmtree(path, ignore_errors=True)
