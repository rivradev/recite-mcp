from __future__ import annotations

from pathlib import Path

from recite_mcp.ledger import LedgerRepository
from recite_mcp.models import ReceiptRecord


def test_append_and_read_entries(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    receipt = ReceiptRecord(vendor="Cafe", date="2026-02-22", total=12.0, tax=1.0, currency="USD", category="Meals")

    entry = repo.append_receipt(receipt, source_file="a.jpg")
    rows = repo.read_all()

    assert entry.vendor == "Cafe"
    assert len(rows) == 1
    assert rows[0].vendor == "Cafe"


def test_add_correction_creates_audit_row(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    entry = repo.append_receipt(
        ReceiptRecord(vendor="Shop", date="2026-02-21", total=20.0, tax=2.0, currency="USD", category="Office"),
        source_file="b.jpg",
    )

    correction = repo.add_correction(entry.entry_id, {"category": "Travel"}, reason="wrong category")
    rows = repo.read_all()

    assert correction.entry_type == "correction"
    assert correction.ref_entry_id == entry.entry_id
    assert len(rows) == 2


def test_summary_by_vendor(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    repo.append_receipt(
        ReceiptRecord(vendor="Store", date="2026-02-21", total=20.0, tax=2.0, currency="USD", category="Office"),
        source_file="b.jpg",
    )
    repo.append_receipt(
        ReceiptRecord(vendor="Store", date="2026-02-22", total=30.0, tax=3.0, currency="USD", category="Office"),
        source_file="c.jpg",
    )

    summary = repo.summarize(group_by="vendor")

    assert summary["Store"]["count"] == 2
    assert summary["Store"]["total"] == 50.0

