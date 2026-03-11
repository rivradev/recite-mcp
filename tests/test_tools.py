from __future__ import annotations

from pathlib import Path
from typing import Any

from recite_mcp.config import Settings
from recite_mcp.models import ReceiptRecord
from recite_mcp.tools import ReciteTools


# ---------------------------------------------------------------------------
# Stub API client — returns kwargs so tests can inspect forwarded args
# ---------------------------------------------------------------------------

class _Client:
    """Minimal stub that records and echoes calls."""

    def process_receipt(self, _path: Path) -> ReceiptRecord:
        return ReceiptRecord(vendor="Bakery", date="2026-02-22", total=8.0, tax=0.8, currency="USD", category="Meals")

    def scan_receipt(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def get_scan(self, scan_id: str) -> dict:
        return {"scan_id": scan_id}

    def create_transaction(self, transaction: dict) -> dict:
        return {"transaction_id": "txn_new", **transaction}

    def list_transactions(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def get_transaction(self, transaction_id: str) -> dict:
        return {"transaction_id": transaction_id}

    def update_transaction(self, transaction_id: str, changes: dict) -> dict:
        return {"transaction_id": transaction_id, "changes": changes}

    def delete_transaction(self, transaction_id: str) -> dict:
        return {"status": "deleted", "transaction_id": transaction_id}

    def import_transactions(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def submit_batch_scans(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def get_batch_scan_status(self, job_id: str) -> dict:
        return {"job_id": job_id, "status": "completed"}

    def get_batch_scan_results(self, job_id: str) -> dict:
        return {"job_id": job_id, "results": []}

    def list_projects(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def create_project(self, *, name: str, description: str | None = None) -> dict:
        return {"project_id": "proj_new", "name": name}

    def update_project(self, project_id: str, **kwargs: Any) -> dict:
        return {"project_id": project_id, **kwargs}

    def delete_project(self, project_id: str) -> dict:
        return {"status": "deleted", "project_id": project_id}

    def get_summary(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def create_webhook(self, *, url: str, events: list[str], secret: str | None = None) -> dict:
        return {"webhook_id": "wh_new", "url": url, "events": events}

    def list_webhooks(self) -> dict:
        return {"webhooks": []}

    def delete_webhook(self, webhook_id: str) -> dict:
        return {"status": "deleted", "webhook_id": webhook_id}

    def create_rule(self, *, rule_type: str, condition: dict, action: dict, priority: int | None = None) -> dict:
        return {"rule_id": "rule_new", "rule_type": rule_type}

    def list_rules(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def delete_rule(self, rule_id: str) -> dict:
        return {"status": "deleted", "rule_id": rule_id}

    def get_usage(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def export_transactions(self, *, format: str, filters: dict | None = None) -> dict:
        return {"format": format, "filters": filters}


def _settings(tmp_path: Path) -> Settings:
    return Settings(recite_home=tmp_path, api_key="x", api_base_url="https://example", request_timeout_sec=20)


def _tools(tmp_path: Path) -> ReciteTools:
    return ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())


# ---------------------------------------------------------------------------
# Legacy process_receipt / batch
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# scan_receipt
# ---------------------------------------------------------------------------

def test_scan_receipt_tool_forwards_ephemeral_request(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    tools = _tools(tmp_path)

    result = tools.scan_receipt(file_path=str(image), ephemeral=True)

    assert result["data"]["ephemeral"] is True
    assert result["data"]["file_path"] == str(image)


def test_scan_receipt_tool_forwards_auto_save_params(tmp_path: Path) -> None:
    tools = _tools(tmp_path)

    result = tools.scan_receipt(
        raw_text="receipt", auto_save=True, project_id="proj_x", save_threshold="medium"
    )

    assert result["data"]["auto_save"] is True
    assert result["data"]["project_id"] == "proj_x"
    assert result["data"]["save_threshold"] == "medium"


def test_scan_receipt_tool_forwards_metadata(tmp_path: Path) -> None:
    tools = _tools(tmp_path)

    result = tools.scan_receipt(image_url="https://example.com/r.jpg", metadata={"source": "email"})

    assert result["data"]["metadata"] == {"source": "email"}


# ---------------------------------------------------------------------------
# get_scan
# ---------------------------------------------------------------------------

def test_get_scan_tool_returns_scan(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_scan("scan_abc")
    assert result["scan_id"] == "scan_abc"


# ---------------------------------------------------------------------------
# transactions
# ---------------------------------------------------------------------------

def test_create_transaction_tool_forwards_payload(tmp_path: Path) -> None:
    txn = {"date": "2026-03-01", "amount": 50.0, "transaction_type": "Expense", "category": "Food", "payment_method": "Card"}
    result = _tools(tmp_path).create_transaction(txn)
    assert result["transaction_id"] == "txn_new"
    assert result["amount"] == 50.0


def test_list_transactions_tool_forwards_filters(tmp_path: Path) -> None:
    result = _tools(tmp_path).list_transactions(start_date="2026-01-01", limit=25)
    assert result["data"]["start_date"] == "2026-01-01"
    assert result["data"]["limit"] == 25


def test_get_transaction_tool_returns_transaction(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_transaction("txn_123")
    assert result["transaction_id"] == "txn_123"


def test_update_transaction_tool_forwards_changes(tmp_path: Path) -> None:
    result = _tools(tmp_path).update_transaction("txn_123", {"amount": 99.0})
    assert result["transaction_id"] == "txn_123"
    assert result["changes"] == {"amount": 99.0}


def test_delete_transaction_tool_returns_deleted(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_transaction("txn_123")
    assert result == {"status": "deleted", "transaction_id": "txn_123"}


# ---------------------------------------------------------------------------
# import_transactions
# ---------------------------------------------------------------------------

def test_import_transactions_tool_forwards_json_payload(tmp_path: Path) -> None:
    txns = [{"date": "2026-03-01", "amount": 10.0}]
    result = _tools(tmp_path).import_transactions(transactions=txns, project_id="proj_x")
    assert result["data"]["transactions"] == txns
    assert result["data"]["project_id"] == "proj_x"


def test_import_transactions_tool_forwards_csv_text(tmp_path: Path) -> None:
    result = _tools(tmp_path).import_transactions(csv_text="date,amount\n2026-03-01,10.0")
    assert result["data"]["csv_text"].startswith("date,amount")


def test_import_transactions_tool_forwards_csv_file_path(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("date,amount\n2026-03-01,10.0")
    result = _tools(tmp_path).import_transactions(csv_file_path=str(csv_file))
    assert result["data"]["csv_file_path"] == str(csv_file)


# ---------------------------------------------------------------------------
# submit_batch_scans
# ---------------------------------------------------------------------------

def test_submit_batch_scans_tool_forwards_items(tmp_path: Path) -> None:
    items = [{"image_url": "https://example.com/r.jpg"}]
    result = _tools(tmp_path).submit_batch_scans(items=items, auto_save=True, project_id="proj_x")
    assert result["data"]["items"] == items
    assert result["data"]["auto_save"] is True


def test_submit_batch_scans_tool_forwards_webhook(tmp_path: Path) -> None:
    result = _tools(tmp_path).submit_batch_scans(
        items=[{"image_url": "https://example.com/r.jpg"}],
        webhook_url="https://my.app/hook",
        webhook_secret="secret",
    )
    assert result["data"]["webhook_url"] == "https://my.app/hook"


# ---------------------------------------------------------------------------
# batch status / results
# ---------------------------------------------------------------------------

def test_get_batch_scan_status_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_batch_scan_status("job_1")
    assert result["job_id"] == "job_1"
    assert result["status"] == "completed"


def test_get_batch_scan_results_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_batch_scan_results("job_1")
    assert result["results"] == []


# ---------------------------------------------------------------------------
# projects
# ---------------------------------------------------------------------------

def test_list_projects_tool_forwards_params(tmp_path: Path) -> None:
    result = _tools(tmp_path).list_projects(status="active", limit=10)
    assert result["data"]["status"] == "active"
    assert result["data"]["limit"] == 10


def test_create_project_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).create_project(name="New Project", description="desc")
    assert result["project_id"] == "proj_new"
    assert result["name"] == "New Project"


def test_update_project_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).update_project("proj_1", name="Renamed", status="archived")
    assert result["project_id"] == "proj_1"


def test_delete_project_tool_returns_deleted(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_project("proj_1")
    assert result == {"status": "deleted", "project_id": "proj_1"}


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_get_summary_tool_passes_grouping_options(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_summary(period="last_30_days", group_by="category")
    assert result["data"] == {"period": "last_30_days", "group_by": "category"}


def test_get_summary_tool_omits_none_params(tmp_path: Path) -> None:
    """None-valued params should not be forwarded to the API client."""
    result = _tools(tmp_path).get_summary(period="current_month")
    # Only non-None values should be present
    assert "group_by" not in result["data"]
    assert result["data"]["period"] == "current_month"


# ---------------------------------------------------------------------------
# webhooks
# ---------------------------------------------------------------------------

def test_create_webhook_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).create_webhook(url="https://my.app/wh", events=["batch.completed"])
    assert result["webhook_id"] == "wh_new"
    assert result["events"] == ["batch.completed"]


def test_list_webhooks_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).list_webhooks()
    assert "webhooks" in result


def test_delete_webhook_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_webhook("wh_1")
    assert result == {"status": "deleted", "webhook_id": "wh_1"}


# ---------------------------------------------------------------------------
# rules
# ---------------------------------------------------------------------------

def test_create_rule_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).create_rule(
        rule_type="vendor_category",
        condition={"vendor": "Starbucks"},
        action={"set_category": "Coffee"},
        priority=1,
    )
    assert result["rule_id"] == "rule_new"
    assert result["rule_type"] == "vendor_category"


def test_list_rules_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).list_rules(limit=10)
    assert result["data"]["limit"] == 10


def test_delete_rule_tool(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_rule("rule_1")
    assert result == {"status": "deleted", "rule_id": "rule_1"}


# ---------------------------------------------------------------------------
# usage / export
# ---------------------------------------------------------------------------

def test_get_usage_tool_forwards_params(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_usage(period="today", breakdown="daily")
    assert result["data"]["period"] == "today"
    assert result["data"]["breakdown"] == "daily"


def test_export_transactions_tool_forwards_format_and_filters(tmp_path: Path) -> None:
    result = _tools(tmp_path).export_transactions(format="csv", filters={"project_id": "proj_x"})
    assert result["format"] == "csv"
    assert result["filters"] == {"project_id": "proj_x"}
