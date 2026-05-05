from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

from recite_mcp.config import load_settings
from recite_mcp.resources import ResourceProvider
from recite_mcp.tools import ReciteTools

try:  # pragma: no cover - exercised only when mcp is installed in runtime.
    from mcp.server.fastmcp import FastMCP
except Exception:  # noqa: BLE001
    FastMCP = None  # type: ignore[assignment]


class _SimpleServer:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}
        self.resources: dict[str, Callable[[], Any]] = {}

    def tool(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def _wrap(func: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[name] = func
            return func

        return _wrap

    def resource(self, name: str) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
        def _wrap(func: Callable[[], Any]) -> Callable[[], Any]:
            self.resources[name] = func
            return func

        return _wrap


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def _build_handlers(
    server: Any, tools: ReciteTools, resources: ResourceProvider, settings: Any
) -> Any:
    @server.tool("process_receipt")
    def process_receipt(
        file_path: str,
        rename: bool = False,
        category_hint: str | None = None,
        dry_run: bool = False,
    ) -> dict:
        return _serialize(
            tools.process_receipt(
                file_path=file_path,
                rename=rename,
                category_hint=category_hint,
                dry_run=dry_run,
            )
        )

    @server.tool("process_receipts_batch")
    def process_receipts_batch(
        input_dir: str,
        rename: bool = False,
        dry_run: bool = True,
        recursive: bool = True,
    ) -> dict:
        return _serialize(
            tools.process_receipts_batch(
                input_dir=input_dir, rename=rename, dry_run=dry_run, recursive=recursive
            )
        )

    @server.tool("scan_receipt")
    def scan_receipt(
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
        metadata: dict | None = None,
        ephemeral: bool = False,
    ) -> dict:
        """Scan a receipt using the Recite API to extract financial data.

        Provide exactly one input: file_path, image_url, image_base64, or raw_text.

        Args:
            file_path: Local path to an image.
            image_url: Publicly accessible URL (must use https).
            image_base64: Base64-encoded image data.
            raw_text: Pre-extracted text.
            auto_save: Auto-create a transaction if successful. Requires project_id.
            save_threshold: Confidence threshold for auto-saving.
            project_id: Project UUID. Required if auto_save is True.
            status: Target status of the transaction.
            image_type: MIME type hint for the image.
            idempotency_key: Key to prevent duplicate processing.
            metadata: Custom key-value data.
            ephemeral: Process without saving scan records server-side. Cannot be True if auto_save is True.
        """
        return tools.scan_receipt(
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

    @server.tool("get_scan")
    def get_scan(scan_id: str) -> dict:
        return tools.get_scan(scan_id)

    @server.tool("create_transaction")
    def create_transaction(transaction: dict) -> dict:
        """Create a transaction in the Recite API.

        Required fields:
            date: Transaction date (YYYY-MM-DD).
            amount: Monetary amount (use 'amount', not 'total').
            transaction_type: One of Expense, Income, Asset, Liability, Equity.
            category: Category string.
            payment_method: Payment method string (e.g. "Credit Card").

        Optional fields: vendor, description, project_id, metadata, tags.

        Note: The local ledger uses 'total' for the same concept. When moving
        data from local ledger to API transactions, map 'total' -> 'amount'.
        """
        return tools.create_transaction(transaction)

    @server.tool("list_transactions")
    def list_transactions(
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
    ) -> dict:
        return tools.list_transactions(
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

    @server.tool("get_transaction")
    def get_transaction(transaction_id: str) -> dict:
        return tools.get_transaction(transaction_id)

    @server.tool("update_transaction")
    def update_transaction(transaction_id: str, changes: dict) -> dict:
        return tools.update_transaction(transaction_id, changes)

    @server.tool("delete_transaction")
    def delete_transaction(transaction_id: str) -> dict:
        return tools.delete_transaction(transaction_id)

    @server.tool("import_transactions")
    def import_transactions(
        transactions: list[dict] | None = None,
        csv_text: str | None = None,
        csv_file_path: str | None = None,
        all_or_nothing: bool | None = None,
        project_id: str | None = None,
    ) -> dict:
        """Import multiple transactions at once.

        Provide exactly one data source: transactions (list), csv_text, or csv_file_path.

        Args:
            transactions: List of transaction objects to import.
            csv_text: Raw CSV string content.
            csv_file_path: Local path to a CSV file.
            all_or_nothing: If True, fails the entire import if any transaction fails.
            project_id: Apply all transactions to this project UUID.
        """
        return tools.import_transactions(
            transactions=transactions,
            csv_text=csv_text,
            csv_file_path=csv_file_path,
            all_or_nothing=all_or_nothing,
            project_id=project_id,
        )

    @server.tool("submit_batch_scans")
    def submit_batch_scans(
        items: list[dict],
        auto_save: bool = False,
        save_threshold: str | None = None,
        project_id: str | None = None,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
    ) -> dict:
        """Submit multiple receipts for asynchronous batch processing.

        Args:
            items: List of 1-20 task items. Each must provide exactly one of
                   file_path, image_url, or image_base64.
            auto_save: Auto-create transactions for successful scans.
            save_threshold: Confidence threshold for auto-saving.
            project_id: Apply all auto-saved transactions to this project UUID.
            webhook_url: URL to call when batch completes.
            webhook_secret: HMAC-SHA256 signature secret for the webhook.
        """
        return tools.submit_batch_scans(
            items=items,
            auto_save=auto_save,
            save_threshold=save_threshold,
            project_id=project_id,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
        )

    @server.tool("get_batch_scan_status")
    def get_batch_scan_status(job_id: str) -> dict:
        return tools.get_batch_scan_status(job_id)

    @server.tool("get_batch_scan_results")
    def get_batch_scan_results(job_id: str) -> dict:
        return tools.get_batch_scan_results(job_id)

    @server.tool("list_projects")
    def list_projects(
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict:
        return tools.list_projects(
            status=status, limit=limit, offset=offset, format=format
        )

    @server.tool("create_project")
    def create_project(name: str, description: str | None = None) -> dict:
        return tools.create_project(name=name, description=description)

    @server.tool("update_project")
    def update_project(
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict:
        return tools.update_project(
            project_id, name=name, description=description, status=status
        )

    @server.tool("delete_project")
    def delete_project(project_id: str) -> dict:
        return tools.delete_project(project_id)

    @server.tool("get_summary")
    def get_summary(
        period: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        project_id: str | None = None,
        group_by: str | None = None,
    ) -> dict:
        return tools.get_summary(
            period=period,
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            group_by=group_by,
        )

    @server.tool("create_webhook")
    def create_webhook(url: str, events: list[str], secret: str | None = None) -> dict:
        """Create a webhook subscription.

        Args:
            url: Webhook endpoint URL.
            events: List of event types. Valid values:
                transaction.created, transaction.updated,
                transaction.deleted, batch.completed.
            secret: Optional HMAC-SHA256 signing secret.
        """
        return tools.create_webhook(url=url, events=events, secret=secret)

    @server.tool("list_webhooks")
    def list_webhooks() -> dict:
        return tools.list_webhooks()

    @server.tool("delete_webhook")
    def delete_webhook(webhook_id: str) -> dict:
        return tools.delete_webhook(webhook_id)

    @server.tool("create_rule")
    def create_rule(
        rule_type: str, condition: dict, action: dict, priority: int | None = None
    ) -> dict:
        """Create an automation rule.

        Args:
            rule_type: One of: vendor_category, default_project, processing_preference.
            condition: Condition object (e.g. {"vendor": "Starbucks"}).
            action: Action object (e.g. {"set_category": "Coffee"}).
            priority: Optional priority integer (higher = first).
        """
        return tools.create_rule(
            rule_type=rule_type, condition=condition, action=action, priority=priority
        )

    @server.tool("list_rules")
    def list_rules(limit: int | None = None, offset: int | None = None) -> dict:
        return tools.list_rules(limit=limit, offset=offset)

    @server.tool("delete_rule")
    def delete_rule(rule_id: str) -> dict:
        return tools.delete_rule(rule_id)

    @server.tool("update_rule")
    def update_rule(rule_id: str, changes: dict) -> dict:
        """Partially update a rule. The rule_type cannot be changed.

        Args:
            rule_id: UUID of the rule to update.
            changes: Fields to update. All are optional:
                active (bool), priority (int),
                condition (object, simple rules), action (object, simple rules),
                conditions (array, transaction_rule), actions (array, transaction_rule),
                condition_operator ("AND" or "OR", transaction_rule).
        """
        return tools.update_rule(rule_id, changes)

    @server.tool("get_categories")
    def get_categories() -> dict:
        """List all categories: default (17 built-in) and custom user-added ones."""
        return tools.get_categories()

    @server.tool("create_category")
    def create_category(name: str) -> dict:
        """Add a custom category. Duplicates (case-insensitive) are rejected. Max 100 custom categories.

        Args:
            name: Category name to add.
        """
        return tools.create_category(name)

    @server.tool("delete_category")
    def delete_category(name: str) -> dict:
        """Remove a custom category by name. Default categories cannot be deleted.

        Args:
            name: Exact category name to remove (unencoded).
        """
        return tools.delete_category(name)

    @server.tool("get_vendors")
    def get_vendors() -> dict:
        """List all custom vendors for the authenticated user."""
        return tools.get_vendors()

    @server.tool("create_vendor")
    def create_vendor(name: str) -> dict:
        """Add a custom vendor. Duplicates (case-insensitive) are rejected. Max 500 vendors.

        Args:
            name: Vendor name to add.
        """
        return tools.create_vendor(name)

    @server.tool("delete_vendor")
    def delete_vendor(name: str) -> dict:
        """Remove a custom vendor by name.

        Args:
            name: Exact vendor name to remove (unencoded).
        """
        return tools.delete_vendor(name)

    @server.tool("get_usage")
    def get_usage(period: str | None = None, breakdown: str | None = None) -> dict:
        return tools.get_usage(period=period, breakdown=breakdown)

    @server.tool("export_transactions")
    def export_transactions(
        format: str,
        output_path: str | None = None,
        filters: dict | None = None,
    ) -> dict:
        return tools.export_transactions(
            format=format, output_path=output_path, filters=filters
        )

    @server.tool("upload_bank_statement")
    def upload_bank_statement(
        csv_file_path: str | None = None,
        csv_text: str | None = None,
        account_name: str | None = None,
        statement_date: str | None = None,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        return tools.upload_bank_statement(
            csv_file_path=csv_file_path,
            csv_text=csv_text,
            account_name=account_name,
            statement_date=statement_date,
            source=source,
            metadata=metadata,
        )

    @server.tool("list_bank_statements")
    def list_bank_statements(
        account_name: str | None = None,
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict:
        return tools.list_bank_statements(
            account_name=account_name,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            format=format,
        )

    @server.tool("get_bank_statement")
    def get_bank_statement(statement_id: str) -> dict:
        return tools.get_bank_statement(statement_id)

    @server.tool("delete_bank_statement")
    def delete_bank_statement(statement_id: str) -> dict:
        return tools.delete_bank_statement(statement_id)

    @server.tool("export_bank_statement")
    def export_bank_statement(
        statement_id: str,
        format: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        return tools.export_bank_statement(
            statement_id, format=format, output_path=output_path
        )

    @server.tool("list_bank_transactions")
    def list_bank_transactions(
        statement_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        amount_min: float | int | None = None,
        amount_max: float | int | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict:
        return tools.list_bank_transactions(
            statement_id=statement_id,
            start_date=start_date,
            end_date=end_date,
            amount_min=amount_min,
            amount_max=amount_max,
            status=status,
            limit=limit,
            offset=offset,
            format=format,
        )

    @server.tool("get_bank_transaction")
    def get_bank_transaction(bank_transaction_id: str) -> dict:
        return tools.get_bank_transaction(bank_transaction_id)

    @server.tool("update_bank_transaction")
    def update_bank_transaction(bank_transaction_id: str, changes: dict) -> dict:
        return tools.update_bank_transaction(bank_transaction_id, changes)

    @server.tool("delete_bank_transaction")
    def delete_bank_transaction(bank_transaction_id: str) -> dict:
        return tools.delete_bank_transaction(bank_transaction_id)

    @server.tool("create_reconciliation_link")
    def create_reconciliation_link(
        transaction_id: str,
        bank_transaction_id: str,
        link_type: str | None = None,
        notes: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        return tools.create_reconciliation_link(
            transaction_id=transaction_id,
            bank_transaction_id=bank_transaction_id,
            link_type=link_type,
            notes=notes,
            metadata=metadata,
        )

    @server.tool("list_reconciliation_links")
    def list_reconciliation_links(
        statement_id: str | None = None,
        transaction_id: str | None = None,
        bank_transaction_id: str | None = None,
        link_type: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict:
        return tools.list_reconciliation_links(
            statement_id=statement_id,
            transaction_id=transaction_id,
            bank_transaction_id=bank_transaction_id,
            link_type=link_type,
            status=status,
            limit=limit,
            offset=offset,
            format=format,
        )

    @server.tool("update_reconciliation_link")
    def update_reconciliation_link(link_id: str, changes: dict) -> dict:
        return tools.update_reconciliation_link(link_id, changes)

    @server.tool("delete_reconciliation_link")
    def delete_reconciliation_link(link_id: str) -> dict:
        return tools.delete_reconciliation_link(link_id)

    @server.tool("run_auto_match")
    def run_auto_match(
        statement_id: str | None = None,
        strategy: str | None = None,
        min_confidence: float | None = None,
        dry_run: bool | None = None,
    ) -> dict:
        return tools.run_auto_match(
            statement_id=statement_id,
            strategy=strategy,
            min_confidence=min_confidence,
            dry_run=dry_run,
        )

    @server.tool("get_reconciliation_summary")
    def get_reconciliation_summary(
        statement_id: str | None = None,
    ) -> dict:
        return tools.get_reconciliation_summary(statement_id=statement_id)

    @server.tool("get_reconciliation_recommendations")
    def get_reconciliation_recommendations(
        bank_transaction_id: str,
        limit: int | None = None,
    ) -> dict:
        return tools.get_reconciliation_recommendations(
            bank_transaction_id=bank_transaction_id,
            limit=limit,
        )

    @server.tool("export_reconciliation")
    def export_reconciliation(
        format: str | None = None,
        statement_id: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        return tools.export_reconciliation(
            format=format, statement_id=statement_id, output_path=output_path
        )

    @server.tool("update_memory")
    def update_memory(instruction: str, tags: list[str] | None = None) -> dict:
        return tools.update_memory(instruction=instruction, tags=tags)

    @server.tool("list_memory")
    def list_memory() -> list[dict]:
        return tools.list_memory()

    @server.tool("add_ledger_correction")
    def add_ledger_correction(
        original_entry_id: str, corrected_fields: dict, reason: str
    ) -> dict:
        return tools.add_ledger_correction(
            original_entry_id=original_entry_id,
            corrected_fields=corrected_fields,
            reason=reason,
        )

    @server.tool("summarize_ledger")
    def summarize_ledger(group_by: str = "vendor") -> dict:
        return tools.summarize_ledger(group_by=group_by)

    @server.tool("export_ledger")
    def export_ledger(format: str, output_path: str) -> dict:
        return tools.export_ledger(format=format, output_path=output_path)

    @server.tool("get_config")
    def get_config() -> dict:
        return {
            "recite_home": str(settings.recite_home),
            "api_base_url": settings.api_base_url,
            "request_timeout_sec": settings.request_timeout_sec,
            "has_api_key": bool(settings.api_key),
        }

    @server.tool("validate_setup")
    def validate_setup() -> dict:
        return resources.get_health()

    @server.resource("recite://ledger")
    def recite_ledger() -> list[dict]:
        return resources.get_ledger_rows()

    @server.resource("recite://memory")
    def recite_memory() -> str:
        return resources.get_memory_text()

    @server.resource("recite://health")
    def recite_health() -> dict:
        return resources.get_health()

    return server


def create_server() -> Any:
    # Don't fail hard at process start if RECITE_API_KEY is missing.
    # MCP clients should still be able to connect and call validate_setup/get_config.
    settings = load_settings(require_api_key=False)
    tools = ReciteTools.from_settings(settings)
    resources = ResourceProvider(settings)
    server = FastMCP("recite-mcp") if FastMCP is not None else _SimpleServer()
    return _build_handlers(server, tools, resources, settings)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recite-mcp", add_help=True)
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Print local health/config JSON and exit (does not call the Recite API).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Transport to use when running as an MCP server (default: stdio).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    if args.version:
        try:
            version = importlib.metadata.version("recite-mcp")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
        print(version)
        return

    if args.validate:
        settings = load_settings(require_api_key=False)
        health = ResourceProvider(settings).get_health()
        payload = {
            "config": {
                "recite_home": str(settings.recite_home),
                "api_base_url": settings.api_base_url,
                "request_timeout_sec": settings.request_timeout_sec,
                "has_api_key": bool(settings.api_key),
            },
            "health": health,
        }
        print(json.dumps(payload, indent=2))
        sys.exit(0 if settings.api_key else 1)

    server = create_server()
    if FastMCP is not None and hasattr(server, "run"):
        server.run(transport=args.transport)
        return
    # Fallback mode is primarily for local dev when mcp isn't installed.
    print("recite-mcp initialized (fallback mode)")
    print(f"tools={','.join(sorted(server.tools.keys()))}")
    print(f"resources={','.join(sorted(server.resources.keys()))}")


if __name__ == "__main__":
    main()
