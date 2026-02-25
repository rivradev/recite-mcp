from __future__ import annotations

from pathlib import Path

from recite_mcp.config import Settings
from recite_mcp.models import ReceiptRecord
from recite_mcp.tools import ReciteTools


class _Client:
    def process_receipt(self, _path: Path) -> ReceiptRecord:
        return ReceiptRecord(vendor="Bakery", date="2026-02-22", total=8.0, tax=0.8, currency="USD", category="Meals")


def _settings(tmp_path: Path) -> Settings:
    return Settings(recite_home=tmp_path, api_key="x", api_base_url="https://example", request_timeout_sec=20)


def test_process_receipt_tool_writes_ledger(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())

    result = tools.process_receipt(file_path=str(image), rename=False, dry_run=False)

    assert result.status == "ok"
    assert result.ledger_entry is not None
    assert result.ledger_entry.vendor == "Bakery"


def test_batch_dry_run_returns_preview(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"a")
    (tmp_path / "b.jpg").write_bytes(b"b")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())

    batch = tools.process_receipts_batch(input_dir=str(tmp_path), dry_run=True)

    assert batch.status == "ok"
    assert batch.processed == 0
    assert batch.preview_count == 2

