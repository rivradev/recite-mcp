from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(slots=True)
class ReceiptRecord:
    vendor: str
    date: str
    total: float
    tax: float
    currency: str
    category: str | None = None


@dataclass(slots=True)
class LedgerEntry:
    entry_id: str
    timestamp_utc: str
    entry_type: str
    vendor: str
    date: str
    total: float
    tax: float
    currency: str
    category: str
    source_file: str
    ref_entry_id: str = ""
    correction_reason: str = ""


@dataclass(slots=True)
class MemoryEntry:
    timestamp_utc: str
    instruction: str
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProcessResult:
    status: str
    message: str
    ledger_entry: LedgerEntry | None = None
    receipt: ReceiptRecord | None = None
    renamed_to: str | None = None


@dataclass(slots=True)
class BatchProcessResult:
    status: str
    processed: int
    failed: int
    preview_count: int
    items: list[dict]

