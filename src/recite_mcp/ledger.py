from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from recite_mcp.models import LedgerEntry, ReceiptRecord, utc_now_iso

_HEADERS = [
    "entry_id",
    "timestamp_utc",
    "entry_type",
    "vendor",
    "date",
    "total",
    "tax",
    "currency",
    "category",
    "source_file",
    "ref_entry_id",
    "correction_reason",
]


class LedgerRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_file(self) -> None:
        if self.path.exists():
            return
        with self.path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_HEADERS)
            writer.writeheader()

    def append_receipt(self, receipt: ReceiptRecord, source_file: str) -> LedgerEntry:
        self._ensure_file()
        entry = LedgerEntry(
            entry_id=str(uuid4()),
            timestamp_utc=utc_now_iso(),
            entry_type="receipt",
            vendor=receipt.vendor,
            date=receipt.date,
            total=receipt.total,
            tax=receipt.tax,
            currency=receipt.currency,
            category=receipt.category or "Uncategorized",
            source_file=source_file,
        )
        self._append_entry(entry)
        return entry

    def add_correction(self, original_entry_id: str, corrected_fields: dict, reason: str) -> LedgerEntry:
        self._ensure_file()
        entry = LedgerEntry(
            entry_id=str(uuid4()),
            timestamp_utc=utc_now_iso(),
            entry_type="correction",
            vendor="",
            date="",
            total=0.0,
            tax=0.0,
            currency="",
            category="",
            source_file=json.dumps(corrected_fields, separators=(",", ":")),
            ref_entry_id=original_entry_id,
            correction_reason=reason,
        )
        self._append_entry(entry)
        return entry

    def _append_entry(self, entry: LedgerEntry) -> None:
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_HEADERS)
            writer.writerow(
                {
                    "entry_id": entry.entry_id,
                    "timestamp_utc": entry.timestamp_utc,
                    "entry_type": entry.entry_type,
                    "vendor": entry.vendor,
                    "date": entry.date,
                    "total": f"{entry.total:.2f}",
                    "tax": f"{entry.tax:.2f}",
                    "currency": entry.currency,
                    "category": entry.category,
                    "source_file": entry.source_file,
                    "ref_entry_id": entry.ref_entry_id,
                    "correction_reason": entry.correction_reason,
                }
            )

    def read_all(self) -> list[LedgerEntry]:
        self._ensure_file()
        rows: list[LedgerEntry] = []
        with self.path.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append(
                    LedgerEntry(
                        entry_id=row["entry_id"],
                        timestamp_utc=row["timestamp_utc"],
                        entry_type=row["entry_type"],
                        vendor=row["vendor"],
                        date=row["date"],
                        total=float(row["total"] or 0),
                        tax=float(row["tax"] or 0),
                        currency=row["currency"],
                        category=row["category"],
                        source_file=row["source_file"],
                        ref_entry_id=row.get("ref_entry_id", ""),
                        correction_reason=row.get("correction_reason", ""),
                    )
                )
        return rows

    def summarize(self, group_by: str = "vendor") -> dict[str, dict[str, float | int]]:
        result: dict[str, dict[str, float | int]] = {}
        for row in self.read_all():
            if row.entry_type != "receipt":
                continue
            key = getattr(row, group_by, "unknown") or "unknown"
            if key not in result:
                result[key] = {"count": 0, "total": 0.0}
            result[key]["count"] += 1
            result[key]["total"] = float(result[key]["total"]) + row.total
        return result

    def export_csv(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        return output_path

    def export_json(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(row) for row in self.read_all()]
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path
