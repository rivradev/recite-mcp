from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

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
    def from_settings(
        cls, settings: Settings, api_client: ApiClient | object | None = None
    ) -> "ReciteTools":
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

        renamed_to = None
        if rename:
            try:
                renamed_to, _ = self._rename_file(
                    path, receipt.vendor, receipt.date, receipt.total
                )
                path = Path(renamed_to)
            except FileExistsError as exc:
                return ProcessResult(
                    status="error",
                    message=str(exc),
                    receipt=receipt,
                    renamed_to=None,
                    warnings=[],
                )

        entry = self._ledger.append_receipt(receipt, source_file=str(path))
        return ProcessResult(
            status="ok",
            message="processed",
            ledger_entry=entry,
            receipt=receipt,
            renamed_to=renamed_to,
            warnings=[],
        )

    def scan_receipt(
        self,
        *,
        file_path: str | None = None,
        image_url: str | None = None,
        image_base64: str | None = None,
        raw_text: str | None = None,
        auto_save: bool = False,
        save_threshold: str | None = None,
        project_id: str | None = None,
        status: str | None = None,
        image_type: str | None = None,
        idempotency_key: str | None = None,
        metadata: dict[str, Any] | None = None,
        ephemeral: bool = False,
    ) -> dict[str, Any]:
        return self._api_client.scan_receipt(
            file_path=file_path,
            image_url=image_url,
            image_base64=image_base64,
            raw_text=raw_text,
            auto_save=auto_save,
            save_threshold=save_threshold,
            project_id=project_id,
            status=status,
            image_type=image_type,
            idempotency_key=idempotency_key,
            metadata=metadata,
            ephemeral=ephemeral,
        )

    def get_scan(self, scan_id: str) -> dict[str, Any]:
        return self._api_client.get_scan(scan_id)

    def create_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
        return self._api_client.create_transaction(transaction)

    def list_transactions(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        vendor: str | None = None,
        payment_method: str | None = None,
        amount_min: float | int | None = None,
        amount_max: float | int | None = None,
        status: str | None = None,
        project_id: str | None = None,
        source: str | None = None,
        agent_name: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        return self._api_client.list_transactions(
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            category=category,
            vendor=vendor,
            payment_method=payment_method,
            amount_min=amount_min,
            amount_max=amount_max,
            status=status,
            project_id=project_id,
            source=source,
            agent_name=agent_name,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
            format=format,
        )

    def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._api_client.get_transaction(transaction_id)

    def update_transaction(
        self, transaction_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        return self._api_client.update_transaction(transaction_id, changes)

    def delete_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._api_client.delete_transaction(transaction_id)

    def import_transactions(
        self,
        *,
        transactions: list[dict[str, Any]] | None = None,
        csv_text: str | None = None,
        csv_file_path: str | None = None,
        all_or_nothing: bool | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        return self._api_client.import_transactions(
            transactions=transactions,
            csv_text=csv_text,
            csv_file_path=csv_file_path,
            all_or_nothing=all_or_nothing,
            project_id=project_id,
        )

    def submit_batch_scans(
        self,
        *,
        items: list[dict[str, Any]],
        auto_save: bool = False,
        save_threshold: str | None = None,
        project_id: str | None = None,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
    ) -> dict[str, Any]:
        return self._api_client.submit_batch_scans(
            items=items,
            auto_save=auto_save,
            save_threshold=save_threshold,
            project_id=project_id,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
        )

    def get_batch_scan_status(self, job_id: str) -> dict[str, Any]:
        return self._api_client.get_batch_scan_status(job_id)

    def get_batch_scan_results(self, job_id: str) -> dict[str, Any]:
        return self._api_client.get_batch_scan_results(job_id)

    def list_projects(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        return self._api_client.list_projects(
            status=status, limit=limit, offset=offset, format=format
        )

    def create_project(
        self, name: str, description: str | None = None
    ) -> dict[str, Any]:
        return self._api_client.create_project(name=name, description=description)

    def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        return self._api_client.update_project(
            project_id, name=name, description=description, status=status
        )

    def delete_project(self, project_id: str) -> dict[str, Any]:
        return self._api_client.delete_project(project_id)

    def get_summary(
        self,
        *,
        period: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        project_id: str | None = None,
        group_by: str | None = None,
    ) -> dict[str, Any]:
        kwargs = {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "project_id": project_id,
            "group_by": group_by,
        }
        return self._api_client.get_summary(
            **{key: value for key, value in kwargs.items() if value is not None}
        )

    def create_webhook(
        self, url: str, events: list[str], secret: str | None = None
    ) -> dict[str, Any]:
        return self._api_client.create_webhook(url=url, events=events, secret=secret)

    def list_webhooks(self) -> dict[str, Any]:
        return self._api_client.list_webhooks()

    def delete_webhook(self, webhook_id: str) -> dict[str, Any]:
        return self._api_client.delete_webhook(webhook_id)

    def create_rule(
        self,
        *,
        rule_type: str,
        condition: dict[str, Any],
        action: dict[str, Any],
        priority: int | None = None,
    ) -> dict[str, Any]:
        return self._api_client.create_rule(
            rule_type=rule_type, condition=condition, action=action, priority=priority
        )

    def list_rules(
        self, *, limit: int | None = None, offset: int | None = None
    ) -> dict[str, Any]:
        return self._api_client.list_rules(limit=limit, offset=offset)

    def delete_rule(self, rule_id: str) -> dict[str, Any]:
        return self._api_client.delete_rule(rule_id)

    def update_rule(self, rule_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        return self._api_client.update_rule(rule_id, changes)

    def get_categories(self) -> dict[str, Any]:
        return self._api_client.get_categories()

    def create_category(self, name: str) -> dict[str, Any]:
        return self._api_client.create_category(name)

    def delete_category(self, name: str) -> dict[str, Any]:
        return self._api_client.delete_category(name)

    def get_vendors(self) -> dict[str, Any]:
        return self._api_client.get_vendors()

    def create_vendor(self, name: str) -> dict[str, Any]:
        return self._api_client.create_vendor(name)

    def delete_vendor(self, name: str) -> dict[str, Any]:
        return self._api_client.delete_vendor(name)

    def get_usage(
        self, *, period: str | None = None, breakdown: str | None = None
    ) -> dict[str, Any]:
        return self._api_client.get_usage(period=period, breakdown=breakdown)

    def export_transactions(
        self,
        *,
        format: str,
        output_path: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any] | str:
        result = self._api_client.export_transactions(format=format, filters=filters)
        if output_path is not None:
            path = Path(output_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(result["body"], encoding="utf-8")
            return {"status": "ok", "path": str(path), "format": format}
        return result["body"]

    def process_receipts_batch(
        self,
        input_dir: str,
        rename: bool = False,
        dry_run: bool = True,
        recursive: bool = True,
    ) -> BatchProcessResult:
        base = Path(input_dir).expanduser()
        iterator = base.rglob("*") if recursive else base.glob("*")
        files = [
            p
            for p in iterator
            if p.is_file() and p.suffix.lower() in _DEFAULT_EXTENSIONS
        ]

        if dry_run:
            return BatchProcessResult(
                status="ok",
                processed=0,
                failed=0,
                items=[{"file": str(p), "status": "preview"} for p in files],
                preview_count=len(files),
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
                        "entry_id": result.ledger_entry.entry_id
                        if result.ledger_entry
                        else None,
                    }
                )
                processed += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                items.append({"file": str(path), "status": "error", "error": str(exc)})

        return BatchProcessResult(
            status="ok",
            processed=processed,
            failed=failed,
            items=items,
        )

    def update_memory(self, instruction: str, tags: list[str] | None = None) -> dict:
        return asdict(self._memory.add_instruction(instruction, tags=tags))

    def list_memory(self) -> list[dict]:
        return [asdict(entry) for entry in self._memory.list_instructions()]

    def add_ledger_correction(
        self, original_entry_id: str, corrected_fields: dict, reason: str
    ) -> dict:
        return asdict(
            self._ledger.add_correction(
                original_entry_id, corrected_fields=corrected_fields, reason=reason
            )
        )

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
    def _rename_file(
        path: Path, vendor: str, date: str, total: float
    ) -> tuple[str, str | None]:
        # Treat Python None-as-string and other null-like values as absent.
        vendor_normalized = "" if vendor in ("None", "null", "N/A", "") else vendor
        safe_vendor = (
            "".join(
                ch for ch in vendor_normalized if ch.isalnum() or ch in ("-", "_")
            ).strip()
            or "Unknown"
        )
        target = path.with_name(
            f"{date}_{safe_vendor}_{total:.2f}{path.suffix.lower()}"
        )
        if target == path:
            return str(target), None
        if target.exists():
            raise FileExistsError(
                f"Cannot rename: destination already exists: {target.name}"
            )
        # Use replace() instead of rename() so the operation is atomic on
        # Windows (rename() raises FileExistsError on Windows when the
        # destination is present, but we guard against that above).
        path.replace(target)
        return str(target), None
