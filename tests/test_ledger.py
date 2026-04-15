from __future__ import annotations

import json
from pathlib import Path

from recite_mcp.ledger import LedgerRepository
from recite_mcp.models import ReceiptRecord


def test_append_and_read_entries(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    receipt = ReceiptRecord(
        vendor="Cafe",
        date="2026-02-22",
        total=12.0,
        tax=1.0,
        currency="USD",
        category="Meals",
    )

    entry = repo.append_receipt(receipt, source_file="a.jpg")
    rows = repo.read_all()

    assert entry.vendor == "Cafe"
    assert len(rows) == 1
    assert rows[0].vendor == "Cafe"


def test_add_correction_creates_audit_row(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    entry = repo.append_receipt(
        ReceiptRecord(
            vendor="Shop",
            date="2026-02-21",
            total=20.0,
            tax=2.0,
            currency="USD",
            category="Office",
        ),
        source_file="b.jpg",
    )

    correction = repo.add_correction(
        entry.entry_id, {"category": "Travel"}, reason="wrong category"
    )
    rows = repo.read_all()

    assert correction.entry_type == "correction"
    assert correction.ref_entry_id == entry.entry_id
    assert len(rows) == 2


def test_correction_stores_corrected_fields_in_dedicated_column(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    entry = repo.append_receipt(
        ReceiptRecord(
            vendor="Shop",
            date="2026-02-21",
            total=20.0,
            tax=2.0,
            currency="USD",
            category="Office",
        ),
        source_file="b.jpg",
    )

    correction = repo.add_correction(
        entry.entry_id, {"category": "Travel"}, reason="wrong category"
    )
    rows = repo.read_all()
    corrected_row = [r for r in rows if r.entry_type == "correction"][0]

    assert corrected_row.source_file == ""
    assert corrected_row.corrected_fields == json.dumps(
        {"category": "Travel"}, separators=(",", ":")
    )
    assert correction.corrected_fields != ""


def test_csv_header_includes_corrected_fields(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    repo._ensure_file()

    header_line = repo.path.read_text(encoding="utf-8").splitlines()[0]
    assert "corrected_fields" in header_line


def test_migrate_adds_missing_corrected_fields_column(tmp_path: Path) -> None:
    """CSV created by old code (no corrected_fields header) is migrated."""
    csv_path = tmp_path / "ledger.csv"
    # Write a 12-column CSV like the old code produced.
    old_header = (
        "entry_id,timestamp_utc,entry_type,vendor,date,"
        "total,tax,currency,category,source_file,"
        "ref_entry_id,correction_reason\n"
    )
    receipt_row = (
        "aaa,2026-01-01T00:00:00+00:00,receipt,Shop,2026-01-01,"
        "20.00,2.00,USD,Office,b.jpg,,\n"
    )
    # Old correction row: JSON in source_file, no corrected_fields column.
    correction_row = (
        'bbb,2026-01-01T00:00:01+00:00,correction,,,0.00,0.00,,,'
        '"{""category"":""Travel""}",aaa,wrong category\n'
    )
    csv_path.write_text(old_header + receipt_row + correction_row, encoding="utf-8")

    repo = LedgerRepository(csv_path)
    rows = repo.read_all()

    # Header should now include corrected_fields.
    header_line = csv_path.read_text(encoding="utf-8").splitlines()[0]
    assert "corrected_fields" in header_line

    # Receipt row is unchanged.
    assert rows[0].vendor == "Shop"
    assert rows[0].source_file == "b.jpg"

    # Correction row is fixed: JSON moved from source_file to corrected_fields.
    correction = [r for r in rows if r.entry_type == "correction"][0]
    assert correction.source_file == ""
    assert "Travel" in correction.corrected_fields


def test_migrate_fixes_legacy_correction_source_file(tmp_path: Path) -> None:
    """Legacy correction rows have JSON moved to corrected_fields on migration."""
    csv_path = tmp_path / "ledger.csv"
    old_header = (
        "entry_id,timestamp_utc,entry_type,vendor,date,"
        "total,tax,currency,category,source_file,"
        "ref_entry_id,correction_reason\n"
    )
    correction_row = (
        'ccc,2026-01-01T00:00:01+00:00,correction,,,0.00,0.00,,,'
        '"{""category"":""Office Supplies""}",orig-id,OCR error\n'
    )
    csv_path.write_text(old_header + correction_row, encoding="utf-8")

    repo = LedgerRepository(csv_path)
    rows = repo.read_all()

    assert len(rows) == 1
    assert rows[0].corrected_fields == '{"category":"Office Supplies"}'
    assert rows[0].source_file == ""
    assert rows[0].ref_entry_id == "orig-id"


def test_read_all_resilient_without_migration(tmp_path: Path) -> None:
    """read_all handles old format even if migration can't run (e.g. read-only)."""
    csv_path = tmp_path / "ledger.csv"
    # 12-column header — but we pass restkey to DictReader so the 13th col
    # would be None-keyed. Simulate the real-world case: header is missing
    # corrected_fields but a correction row has JSON in source_file.
    old_header = (
        "entry_id,timestamp_utc,entry_type,vendor,date,"
        "total,tax,currency,category,source_file,"
        "ref_entry_id,correction_reason,corrected_fields\n"
    )
    correction_row = (
        'ddd,2026-01-01T00:00:01+00:00,correction,,,0.00,0.00,,,'
        '"{""category"":""Travel""}"'
        ",orig-id,OCR error,\n"
    )
    csv_path.write_text(old_header + correction_row, encoding="utf-8")

    repo = LedgerRepository(csv_path)
    rows = repo.read_all()

    # Even though corrected_fields column is empty, read_all should pull
    # the JSON from source_file.
    assert len(rows) == 1
    assert rows[0].corrected_fields == '{"category":"Travel"}'
    assert rows[0].source_file == ""


def test_migrate_recovers_overflow_column(tmp_path: Path) -> None:
    """Rows written with 13 values to a 12-column CSV are recovered."""
    csv_path = tmp_path / "ledger.csv"
    old_header = (
        "entry_id,timestamp_utc,entry_type,vendor,date,"
        "total,tax,currency,category,source_file,"
        "ref_entry_id,correction_reason\n"
    )
    # This correction was written by the fixed code (corrected_fields in col 13)
    # but the CSV header still had only 12 columns.
    correction_row = (
        "eee,2026-01-01T00:00:01+00:00,correction,,,0.00,0.00,,,"
        ",orig-id,OCR error,"
        '"{""category"":""Office Supplies""}"\n'
    )
    csv_path.write_text(old_header + correction_row, encoding="utf-8")

    repo = LedgerRepository(csv_path)
    rows = repo.read_all()

    assert len(rows) == 1
    assert rows[0].corrected_fields == '{"category":"Office Supplies"}'
    assert rows[0].source_file == ""
    assert rows[0].ref_entry_id == "orig-id"


def test_migrate_no_op_when_header_current(tmp_path: Path) -> None:
    """Migration is a no-op when the CSV already has the current header."""
    repo = LedgerRepository(tmp_path / "ledger.csv")
    repo.append_receipt(
        ReceiptRecord(
            vendor="Shop", date="2026-01-01", total=10.0,
            tax=1.0, currency="USD", category="Office",
        ),
        source_file="a.jpg",
    )
    content_before = repo.path.read_text(encoding="utf-8")

    # Trigger _ensure_file again — should not rewrite.
    repo._ensure_file()
    content_after = repo.path.read_text(encoding="utf-8")

    assert content_before == content_after


def test_migrate_empty_file(tmp_path: Path) -> None:
    """An empty file (no header) gets a fresh header written."""
    csv_path = tmp_path / "ledger.csv"
    csv_path.write_text("", encoding="utf-8")

    repo = LedgerRepository(csv_path)
    repo._ensure_file()

    header_line = csv_path.read_text(encoding="utf-8").splitlines()[0]
    assert "corrected_fields" in header_line


def test_add_correction_rejects_empty_corrected_fields(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    entry = repo.append_receipt(
        ReceiptRecord(
            vendor="Shop",
            date="2026-02-21",
            total=20.0,
            tax=2.0,
            currency="USD",
            category="Office",
        ),
        source_file="b.jpg",
    )

    import pytest
    with pytest.raises(ValueError, match="corrected_fields must not be empty"):
        repo.add_correction(entry.entry_id, {}, reason="oops")


def test_summarize_invalid_group_by_raises(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    import pytest
    with pytest.raises(ValueError, match="Invalid group_by field"):
        repo.summarize(group_by="nonexistent_field")


def test_export_csv(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    repo.append_receipt(
        ReceiptRecord(
            vendor="Store",
            date="2026-02-21",
            total=20.0,
            tax=2.0,
            currency="USD",
            category="Office",
        ),
        source_file="b.jpg",
    )

    out = tmp_path / "export.csv"
    result = repo.export_csv(out)

    assert result == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Store" in content
    assert "corrected_fields" in content  # header present


def test_export_json(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    repo.append_receipt(
        ReceiptRecord(
            vendor="Cafe",
            date="2026-02-22",
            total=12.0,
            tax=1.0,
            currency="USD",
            category="Meals",
        ),
        source_file="a.jpg",
    )

    out = tmp_path / "export.json"
    result = repo.export_json(out)

    assert result == out
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["vendor"] == "Cafe"


def test_summary_by_vendor(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    repo.append_receipt(
        ReceiptRecord(
            vendor="Store",
            date="2026-02-21",
            total=20.0,
            tax=2.0,
            currency="USD",
            category="Office",
        ),
        source_file="b.jpg",
    )
    repo.append_receipt(
        ReceiptRecord(
            vendor="Store",
            date="2026-02-22",
            total=30.0,
            tax=3.0,
            currency="USD",
            category="Office",
        ),
        source_file="c.jpg",
    )

    summary = repo.summarize(group_by="vendor")

    assert summary["Store"]["count"] == 2
    assert summary["Store"]["total"] == 50.0

def test_summary_handles_missing_keys(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    repo.append_receipt(
        ReceiptRecord(
            vendor="",
            date="2026-02-21",
            total=20.0,
            tax=2.0,
            currency="USD",
            category="Office",
        ),
        source_file="b.jpg",
    )

    summary = repo.summarize(group_by="vendor")

    assert summary["unknown"]["count"] == 1
    assert summary["unknown"]["total"] == 20.0

def test_summarize_skips_non_receipts(tmp_path: Path) -> None:
    repo = LedgerRepository(tmp_path / "ledger.csv")
    entry = repo.append_receipt(
        ReceiptRecord(
            vendor="Store",
            date="2026-02-21",
            total=20.0,
            tax=2.0,
            currency="USD",
            category="Office",
        ),
        source_file="b.jpg",
    )
    repo.add_correction(entry.entry_id, {"category": "Travel"}, reason="wrong category")

    summary = repo.summarize(group_by="vendor")

    assert summary["Store"]["count"] == 1
    assert summary["Store"]["total"] == 20.0
