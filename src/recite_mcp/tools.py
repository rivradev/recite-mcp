from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from recite_mcp.api_client import ApiClient
from recite_mcp.config import Settings
from recite_mcp.ledger import LedgerRepository
from recite_mcp.memory import MemoryRepository
from recite_mcp.models import BatchProcessResult, ProcessResult

_DEFAULT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".pdf")


class ReciteTools:
    def __init__(
        self,
        settings: Settings,
        api_client: ApiClient,
        ledger: LedgerRepository,
        memory: MemoryRepository,
    ) -> None:
        self._settings = settings
        self._api_client = api_client
        self._ledger = ledger
        self._memory = memory

    @classmethod
    def from_settings(cls, settings: Settings, api_client: ApiClient | object | None = None) -> "ReciteTools":
        resolved_client = api_client if api_client is not None else ApiClient(settings)
        return cls(
            settings=settings,
            api_client=resolved_client,  # type: ignore[arg-type]
            ledger=LedgerRepository(settings.ledger_path),
            memory=MemoryRepository(settings.memory_path),
        )

    def process_receipt(
        self,
        file_path: str,
        rename: bool = False,
        category_hint: str | None = None,
        dry_run: bool = False,
    ) -> ProcessResult:
        path = Path(file_path).expanduser()
        receipt = self._api_client.process_receipt(path)
        if category_hint:
            receipt.category = category_hint

        if dry_run:
            return ProcessResult(status="ok", message="dry_run", receipt=receipt)

        entry = self._ledger.append_receipt(receipt, source_file=str(path))
        renamed_to = None
        if rename:
            renamed_to = self._rename_file(path, entry.vendor, entry.date, entry.total)
        return ProcessResult(status="ok", message="processed", ledger_entry=entry, receipt=receipt, renamed_to=renamed_to)

    def process_receipts_batch(
        self,
        input_dir: str,
        rename: bool = False,
        dry_run: bool = True,
        recursive: bool = True,
    ) -> BatchProcessResult:
        base = Path(input_dir).expanduser()
        iterator = base.rglob("*") if recursive else base.glob("*")
        files = [p for p in iterator if p.is_file() and p.suffix.lower() in _DEFAULT_EXTENSIONS]

        if dry_run:
            return BatchProcessResult(
                status="ok",
                processed=0,
                failed=0,
                preview_count=len(files),
                items=[{"file": str(p), "status": "preview"} for p in files],
            )

        items: list[dict] = []
        processed = 0
        failed = 0
        for path in files:
            try:
                result = self.process_receipt(str(path), rename=rename, dry_run=False)
                items.append(
                    {
                        "file": str(path),
                        "status": "ok",
                        "entry_id": result.ledger_entry.entry_id if result.ledger_entry else None,
                    }
                )
                processed += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                items.append({"file": str(path), "status": "error", "error": str(exc)})

        return BatchProcessResult(status="ok", processed=processed, failed=failed, preview_count=len(files), items=items)

    def update_memory(self, instruction: str, tags: list[str] | None = None) -> dict:
        return asdict(self._memory.add_instruction(instruction, tags=tags))

    def list_memory(self) -> list[dict]:
        return [asdict(entry) for entry in self._memory.list_instructions()]

    def add_ledger_correction(self, original_entry_id: str, corrected_fields: dict, reason: str) -> dict:
        return asdict(self._ledger.add_correction(original_entry_id, corrected_fields=corrected_fields, reason=reason))

    def summarize_ledger(self, group_by: str = "vendor") -> dict:
        return self._ledger.summarize(group_by=group_by)

    def export_ledger(self, format: str, output_path: str) -> dict:
        output = Path(output_path).expanduser()
        if format == "csv":
            file_path = self._ledger.export_csv(output)
        elif format == "json":
            file_path = self._ledger.export_json(output)
        else:
            raise ValueError(f"Unsupported format: {format}")
        return {"status": "ok", "path": str(file_path)}

    @staticmethod
    def _rename_file(path: Path, vendor: str, date: str, total: float) -> str:
        safe_vendor = "".join(ch for ch in vendor if ch.isalnum() or ch in ("-", "_")).strip() or "vendor"
        target = path.with_name(f"{date}_{safe_vendor}_{total:.2f}{path.suffix.lower()}")
        if target == path:
            return str(target)
        path.rename(target)
        return str(target)

