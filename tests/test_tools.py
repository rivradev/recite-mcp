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
        return ReceiptRecord(
            vendor="Bakery",
            date="2026-02-22",
            total=8.0,
            tax=0.8,
            currency="USD",
            category="Meals",
        )

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

    def create_webhook(
        self, *, url: str, events: list[str], secret: str | None = None
    ) -> dict:
        return {"webhook_id": "wh_new", "url": url, "events": events}

    def list_webhooks(self) -> dict:
        return {"webhooks": []}

    def delete_webhook(self, webhook_id: str) -> dict:
        return {"status": "deleted", "webhook_id": webhook_id}

    def create_rule(
        self,
        *,
        rule_type: str,
        condition: dict,
        action: dict,
        priority: int | None = None,
    ) -> dict:
        return {"rule_id": "rule_new", "rule_type": rule_type}

    def list_rules(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def delete_rule(self, rule_id: str) -> dict:
        return {"status": "deleted", "rule_id": rule_id}

    def get_usage(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def export_transactions(self, *, format: str, filters: dict | None = None) -> dict:
        return {
            "content_type": "text/csv",
            "body": f"header\nrow1\nrow2",
            "format": format,
            "filters": filters,
        }

    def update_rule(self, rule_id: str, changes: dict) -> dict:
        return {"rule_id": rule_id, **changes}

    def get_categories(self) -> dict:
        return {
            "default_categories": ["Advertising & Marketing"],
            "custom_categories": [],
            "all_categories": ["Advertising & Marketing"],
        }

    def create_category(self, name: str) -> dict:
        return {"name": name}

    def delete_category(self, name: str) -> dict:
        return {"status": "deleted", "name": name}

    def get_vendors(self) -> dict:
        return {"custom_vendors": []}

    def create_vendor(self, name: str) -> dict:
        return {"name": name}

    def delete_vendor(self, name: str) -> dict:
        return {"status": "deleted", "name": name}

    def upload_bank_statement(self, **kwargs: Any) -> dict:
        return {
            "statement_id": "stmt_new",
            "status": "uploaded",
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ("csv_text", "csv_file_path")
            },
        }

    def list_bank_statements(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def get_bank_statement(self, statement_id: str) -> dict:
        return {"statement_id": statement_id}

    def delete_bank_statement(self, statement_id: str) -> dict:
        return {"status": "deleted", "statement_id": statement_id}

    def export_bank_statement(self, statement_id: str, **kwargs: Any) -> dict:
        return {
            "content_type": "text/csv",
            "body": "date,description,amount\n",
            "statement_id": statement_id,
            **kwargs,
        }

    def list_bank_transactions(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def get_bank_transaction(self, bank_transaction_id: str) -> dict:
        return {"bank_transaction_id": bank_transaction_id}

    def update_bank_transaction(self, bank_transaction_id: str, changes: dict) -> dict:
        return {"bank_transaction_id": bank_transaction_id, **changes}

    def delete_bank_transaction(self, bank_transaction_id: str) -> dict:
        return {"status": "deleted", "bank_transaction_id": bank_transaction_id}

    def create_reconciliation_link(self, **kwargs: Any) -> dict:
        return {"link_id": "link_new", **kwargs}

    def list_reconciliation_links(self, **kwargs: Any) -> dict:
        return {"data": kwargs}

    def update_reconciliation_link(self, link_id: str, changes: dict) -> dict:
        return {"link_id": link_id, **changes}

    def delete_reconciliation_link(self, link_id: str) -> dict:
        return {"status": "deleted", "link_id": link_id}

    def run_auto_match(self, **kwargs: Any) -> dict:
        return {"matches_found": 3, "status": "completed", **kwargs}

    def get_reconciliation_summary(self, **kwargs: Any) -> dict:
        return {"matched": 10, "unmatched": 2, **kwargs}

    def get_reconciliation_recommendations(self, **kwargs: Any) -> dict:
        return {"recommendations": [{"tx_id": "tx_1"}], **kwargs}

    def export_reconciliation(self, **kwargs: Any) -> dict:
        return {
            "content_type": "text/csv",
            "body": "link_id,transaction_id\n",
            **kwargs,
        }


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        recite_home=tmp_path,
        api_key="x",
        api_base_url="https://example",
        request_timeout_sec=20,
    )


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


def test_batch_live_run_has_zero_preview_count(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"a")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())

    batch = tools.process_receipts_batch(input_dir=str(tmp_path), dry_run=False)

    assert batch.processed == 1
    assert batch.preview_count is None


def test_rename_file_unknown_vendor_when_none_string(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")

    result, warning = ReciteTools._rename_file(image, "None", "2026-01-01", 12.50)

    assert "Unknown" in Path(result).name
    assert "None" not in Path(result).name
    assert warning is None


def test_rename_file_unknown_vendor_when_empty(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")

    result, warning = ReciteTools._rename_file(image, "", "2026-01-01", 5.00)

    assert "Unknown" in Path(result).name
    assert warning is None


def test_rename_file_target_already_exists_raises(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    # Pre-create the target file to trigger the collision path
    (tmp_path / "2026-01-01_Bakery_8.00.jpg").write_bytes(b"old content")

    import pytest

    with pytest.raises(FileExistsError, match="2026-01-01_Bakery_8.00.jpg"):
        ReciteTools._rename_file(image, "Bakery", "2026-01-01", 8.00)


def test_rename_file_no_collision_has_no_warning(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")

    result, warning = ReciteTools._rename_file(image, "Bakery", "2026-01-01", 8.00)

    assert Path(result).name == "2026-01-01_Bakery_8.00.jpg"
    assert warning is None


def test_process_receipt_rename_collision_returns_error(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    # Pre-create the collision target
    (tmp_path / "2026-02-22_Bakery_8.00.jpg").write_bytes(b"old")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())

    result = tools.process_receipt(file_path=str(image), rename=True, dry_run=False)

    assert result.status == "error"
    assert "2026-02-22_Bakery_8.00.jpg" in result.message
    assert result.ledger_entry is None  # rename failed before ledger write


def test_process_receipt_rename_no_collision_has_empty_warnings(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())

    result = tools.process_receipt(file_path=str(image), rename=True, dry_run=False)

    assert result.warnings == []


def test_process_receipt_dry_run_does_not_write_ledger(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())

    result = tools.process_receipt(file_path=str(image), dry_run=True)

    assert result.status == "ok"
    assert result.message == "dry_run"
    assert result.ledger_entry is None
    # Ledger file should not exist (no write occurred)
    from recite_mcp.config import Settings

    s = _settings(tmp_path)
    assert not s.ledger_path.exists()


def test_export_ledger_csv(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())
    tools.process_receipt(file_path=str(image), dry_run=False)

    out = tmp_path / "out.csv"
    result = tools.export_ledger("csv", str(out))

    assert result["status"] == "ok"
    assert out.exists()
    assert "Bakery" in out.read_text(encoding="utf-8")


def test_get_reconciliation_recommendations_tool_forwards_args(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_reconciliation_recommendations(
        bank_transaction_id="btx_123", limit=5
    )
    assert result["recommendations"] == [{"tx_id": "tx_1"}]
    assert result["bank_transaction_id"] == "btx_123"
    assert result["limit"] == 5


def test_export_ledger_json(tmp_path: Path) -> None:
    import json as json_mod

    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    tools = ReciteTools.from_settings(_settings(tmp_path), api_client=_Client())
    tools.process_receipt(file_path=str(image), dry_run=False)

    out = tmp_path / "out.json"
    result = tools.export_ledger("json", str(out))

    assert result["status"] == "ok"
    payload = json_mod.loads(out.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload[0]["vendor"] == "Bakery"


def test_export_ledger_unsupported_format_raises(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    import pytest

    with pytest.raises(ValueError, match="Unsupported format"):
        tools.export_ledger("xml", str(tmp_path / "out.xml"))


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

    result = tools.scan_receipt(
        image_url="https://example.com/r.jpg", metadata={"source": "email"}
    )

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
    txn = {
        "date": "2026-03-01",
        "amount": 50.0,
        "transaction_type": "Expense",
        "category": "Food",
        "payment_method": "Card",
    }
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
    result = _tools(tmp_path).import_transactions(
        transactions=txns, project_id="proj_x"
    )
    assert result["data"]["transactions"] == txns
    assert result["data"]["project_id"] == "proj_x"


def test_import_transactions_tool_forwards_csv_text(tmp_path: Path) -> None:
    result = _tools(tmp_path).import_transactions(
        csv_text="date,amount\n2026-03-01,10.0"
    )
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
    result = _tools(tmp_path).submit_batch_scans(
        items=items, auto_save=True, project_id="proj_x"
    )
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
    result = _tools(tmp_path).update_project(
        "proj_1", name="Renamed", status="archived"
    )
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
    result = _tools(tmp_path).create_webhook(
        url="https://my.app/wh", events=["batch.completed"]
    )
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
    result = _tools(tmp_path).export_transactions(
        format="csv", filters={"project_id": "proj_x"}
    )
    assert isinstance(result, str)
    assert "header" in result


def test_export_transactions_writes_to_disk_when_output_path_given(
    tmp_path: Path,
) -> None:
    out = tmp_path / "out.csv"
    result = _tools(tmp_path).export_transactions(format="csv", output_path=str(out))
    assert result["status"] == "ok"
    assert result["format"] == "csv"
    assert out.exists()
    assert out.read_text(encoding="utf-8") == "header\nrow1\nrow2"


# ---------------------------------------------------------------------------
# update_rule
# ---------------------------------------------------------------------------


def test_update_rule_tool_forwards_changes(tmp_path: Path) -> None:
    result = _tools(tmp_path).update_rule("rule_1", {"active": False})
    assert result["rule_id"] == "rule_1"
    assert result["active"] is False


def test_update_rule_tool_forwards_all_optional_fields(tmp_path: Path) -> None:
    result = _tools(tmp_path).update_rule("rule_99", {"priority": 5, "active": True})
    assert result["rule_id"] == "rule_99"
    assert result["priority"] == 5


# ---------------------------------------------------------------------------
# categories
# ---------------------------------------------------------------------------


def test_get_categories_tool_returns_all_arrays(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_categories()
    assert "default_categories" in result
    assert "custom_categories" in result
    assert "all_categories" in result


def test_create_category_tool_returns_name(tmp_path: Path) -> None:
    result = _tools(tmp_path).create_category("Equipment Rental")
    assert result["name"] == "Equipment Rental"


def test_delete_category_tool_returns_deleted(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_category("Equipment Rental")
    assert result == {"status": "deleted", "name": "Equipment Rental"}


# ---------------------------------------------------------------------------
# vendors
# ---------------------------------------------------------------------------


def test_get_vendors_tool_returns_custom_vendors(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_vendors()
    assert "custom_vendors" in result


def test_create_vendor_tool_returns_name(tmp_path: Path) -> None:
    result = _tools(tmp_path).create_vendor("Acme Corp")
    assert result["name"] == "Acme Corp"


def test_delete_vendor_tool_returns_deleted(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_vendor("Acme Corp")
    assert result == {"status": "deleted", "name": "Acme Corp"}


def test_export_ledger_unsupported_format(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    import pytest

    with pytest.raises(ValueError, match="Unsupported format: xml"):
        tools.export_ledger(format="xml", output_path=str(tmp_path / "out.xml"))


def test_rename_file_handles_null_vendor(tmp_path: Path) -> None:
    path = tmp_path / "receipt.jpg"
    path.write_text("")
    new_name, new_path = ReciteTools._rename_file(path, "None", "2026-01-01", 10.0)
    assert new_name == str(tmp_path / "2026-01-01_Unknown_10.00.jpg")


def test_rename_file_handles_none_date(tmp_path: Path) -> None:
    path = tmp_path / "receipt.jpg"
    path.write_text("")
    new_name, new_path = ReciteTools._rename_file(path, "Vendor", "None", 10.0)
    assert new_name == str(tmp_path / "None_Vendor_10.00.jpg")


def test_rename_file_handles_none_total(tmp_path: Path) -> None:
    path = tmp_path / "receipt.jpg"
    path.write_text("")
    new_name, new_path = ReciteTools._rename_file(path, "Vendor", "2026-01-01", 0.0)
    assert new_name == str(tmp_path / "2026-01-01_Vendor_0.00.jpg")


# ---------------------------------------------------------------------------
# bank statements
# ---------------------------------------------------------------------------


def test_upload_bank_statement_tool_forwards_csv_text(tmp_path: Path) -> None:
    result = _tools(tmp_path).upload_bank_statement(
        csv_text="date,description,amount\n2026-01-15,Deposit,1000.00",
        account_name="Checking",
    )
    assert result["statement_id"] == "stmt_new"
    assert result["account_name"] == "Checking"


def test_upload_bank_statement_tool_forwards_csv_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "stmt.csv"
    csv_file.write_text("date,description,amount\n2026-01-15,Deposit,500.00")
    result = _tools(tmp_path).upload_bank_statement(
        csv_file_path=str(csv_file), account_name="Savings"
    )
    assert result["statement_id"] == "stmt_new"


def test_list_bank_statements_tool_forwards_params(tmp_path: Path) -> None:
    result = _tools(tmp_path).list_bank_statements(
        account_name="Checking", status="processed", limit=10
    )
    assert result["data"]["account_name"] == "Checking"
    assert result["data"]["limit"] == 10


def test_get_bank_statement_tool_returns_statement(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_bank_statement("stmt_abc")
    assert result["statement_id"] == "stmt_abc"


def test_delete_bank_statement_tool_returns_deleted(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_bank_statement("stmt_123")
    assert result == {"status": "deleted", "statement_id": "stmt_123"}


def test_export_bank_statement_tool_forwards_format(tmp_path: Path) -> None:
    result = _tools(tmp_path).export_bank_statement("stmt_abc", format="csv")
    assert isinstance(result, str)
    assert "date,description" in result


def test_export_bank_statement_writes_to_disk(tmp_path: Path) -> None:
    out = tmp_path / "stmt.csv"
    result = _tools(tmp_path).export_bank_statement(
        "stmt_abc", format="csv", output_path=str(out)
    )
    assert result["status"] == "ok"
    assert out.exists()


# ---------------------------------------------------------------------------
# bank transactions
# ---------------------------------------------------------------------------


def test_list_bank_transactions_tool_forwards_params(tmp_path: Path) -> None:
    result = _tools(tmp_path).list_bank_transactions(
        statement_id="stmt_1", start_date="2026-01-01", limit=20
    )
    assert result["data"]["statement_id"] == "stmt_1"
    assert result["data"]["limit"] == 20


def test_get_bank_transaction_tool_returns_transaction(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_bank_transaction("btxn_abc")
    assert result["bank_transaction_id"] == "btxn_abc"


def test_update_bank_transaction_tool_forwards_changes(tmp_path: Path) -> None:
    result = _tools(tmp_path).update_bank_transaction("btxn_abc", {"status": "matched"})
    assert result["bank_transaction_id"] == "btxn_abc"
    assert result["status"] == "matched"


def test_delete_bank_transaction_tool_returns_deleted(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_bank_transaction("btxn_123")
    assert result == {"status": "deleted", "bank_transaction_id": "btxn_123"}


# ---------------------------------------------------------------------------
# reconciliation
# ---------------------------------------------------------------------------


def test_create_reconciliation_link_tool_forwards_payload(tmp_path: Path) -> None:
    result = _tools(tmp_path).create_reconciliation_link(
        transaction_id="txn_1",
        bank_transaction_id="btxn_1",
        link_type="manual",
    )
    assert result["link_id"] == "link_new"
    assert result["transaction_id"] == "txn_1"


def test_list_reconciliation_links_tool_forwards_params(tmp_path: Path) -> None:
    result = _tools(tmp_path).list_reconciliation_links(
        statement_id="stmt_1", link_type="auto", limit=25
    )
    assert result["data"]["statement_id"] == "stmt_1"
    assert result["data"]["limit"] == 25


def test_update_reconciliation_link_tool_forwards_changes(tmp_path: Path) -> None:
    result = _tools(tmp_path).update_reconciliation_link("link_1", {"status": "broken"})
    assert result["link_id"] == "link_1"
    assert result["status"] == "broken"


def test_delete_reconciliation_link_tool_returns_deleted(tmp_path: Path) -> None:
    result = _tools(tmp_path).delete_reconciliation_link("link_123")
    assert result == {"status": "deleted", "link_id": "link_123"}


def test_run_auto_match_tool_forwards_params(tmp_path: Path) -> None:
    result = _tools(tmp_path).run_auto_match(
        statement_id="stmt_1", strategy="fuzzy", min_confidence=0.8
    )
    assert result["matches_found"] == 3
    assert result["statement_id"] == "stmt_1"


def test_get_reconciliation_summary_tool_forwards_params(tmp_path: Path) -> None:
    result = _tools(tmp_path).get_reconciliation_summary(statement_id="stmt_1")
    assert result["matched"] == 10


def test_export_reconciliation_tool_forwards_format(tmp_path: Path) -> None:
    result = _tools(tmp_path).export_reconciliation(format="csv", statement_id="stmt_1")
    assert isinstance(result, str)
    assert "link_id" in result


def test_export_reconciliation_writes_to_disk(tmp_path: Path) -> None:
    out = tmp_path / "recon.csv"
    result = _tools(tmp_path).export_reconciliation(
        format="csv", statement_id="stmt_1", output_path=str(out)
    )
    assert result["status"] == "ok"
    assert out.exists()
