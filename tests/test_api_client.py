from __future__ import annotations

from pathlib import Path

import pytest

from recite_mcp.api_client import ApiClient, ApiClientError
from recite_mcp.config import Settings


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _Response:
    def __init__(
        self,
        status_code: int,
        payload: dict | None = None,
        *,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        import json

        self.status_code = status_code
        self._payload = payload
        self.text = text or (json.dumps(payload) if payload is not None else "")
        self.headers = headers or {"Content-Type": "application/json"}

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("No JSON payload configured.")
        return self._payload


class _Session:
    def __init__(self, response: _Response | Exception) -> None:
        self._response = response
        self.last_method: str | None = None
        self.last_url: str | None = None
        self.last_kwargs: dict | None = None

    def request(self, method: str, url: str, **kwargs):  # noqa: ANN001
        self.last_method = method
        self.last_url = url
        self.last_kwargs = kwargs
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    def post(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self.request("POST", args[0], **kwargs)

    def get(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self.request("GET", args[0], **kwargs)

    def patch(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self.request("PATCH", args[0], **kwargs)

    def delete(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self.request("DELETE", args[0], **kwargs)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        recite_home=tmp_path,
        api_key="re_test_123",
        api_base_url="https://recite.rivra.dev/apiV1/api/v1",
        request_timeout_sec=30,
    )


def _settings_no_key(tmp_path: Path) -> Settings:
    return Settings(
        recite_home=tmp_path,
        api_key=None,
        api_base_url="https://recite.rivra.dev/apiV1/api/v1",
        request_timeout_sec=30,
    )


def _ok(data: dict) -> dict:
    """Convenience: build a standard success envelope."""
    return {"success": True, "data": data}


# ---------------------------------------------------------------------------
# process_receipt
# ---------------------------------------------------------------------------


def test_process_receipt_success(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    payload = {
        "success": True,
        "data": {
            "vendor": "Store",
            "date": "2026-02-22",
            "total": 10.5,
            "tax": 0.5,
            "currency": "USD",
        },
        "meta": {"api_version": "v1"},
    }
    session = _Session(_Response(200, payload))
    client = ApiClient(_settings(tmp_path), session=session)

    receipt = client.process_receipt(image)

    assert receipt.vendor == "Store"
    assert receipt.total == 10.5
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/scan")
    assert session.last_kwargs is not None
    assert "image_base64" in session.last_kwargs["json"]
    assert session.last_kwargs["json"]["auto_save"] is False


def test_process_receipt_reads_extracted_data_shape(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    payload = {
        "success": True,
        "data": {
            "scan_id": "scan_123",
            "extracted_data": {
                "vendor": "Nested Store",
                "date": "2026-03-01",
                "amount": 18.25,
                "tax": 1.25,
                "currency": "USD",
                "category": "Food & Dining",
            },
        },
    }
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, payload)))

    receipt = client.process_receipt(image)

    assert receipt.vendor == "Nested Store"
    assert receipt.total == 18.25
    assert receipt.category == "Food & Dining"


def test_process_receipt_raises_on_http_error(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    client = ApiClient(
        _settings(tmp_path), session=_Session(_Response(500, {"error": "failed"}))
    )

    with pytest.raises(ApiClientError):
        client.process_receipt(image)


def test_process_receipt_raises_when_success_is_false(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    payload = {"success": False, "error": {"message": "invalid image"}}
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, payload)))

    with pytest.raises(ApiClientError):
        client.process_receipt(image)


def test_process_receipt_raises_when_file_missing(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="does not exist"):
        client.process_receipt(tmp_path / "nonexistent.jpg")


def test_process_receipt_null_vendor_stored_as_empty_string(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    payload = _ok(
        {"extracted_data": {"amount": 10.0, "date": "2026-01-01", "currency": "USD"}}
    )
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, payload)))
    record = client.process_receipt(image)
    assert record.vendor == "", (
        "null vendor must become empty string, not the string 'None'"
    )


# ---------------------------------------------------------------------------
# scan_receipt — input validation
# ---------------------------------------------------------------------------


def test_scan_receipt_supports_local_file_and_ephemeral_mode(tmp_path: Path) -> None:
    image = tmp_path / "receipt.png"
    image.write_bytes(b"fake")
    payload = {
        "success": True,
        "data": {
            "scan_id": "scan_ephemeral",
            "summary": {"confidence_band": "high", "auto_save_eligible": True},
        },
        "meta": {"request_id": "req_123"},
    }
    session = _Session(_Response(200, payload))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.scan_receipt(file_path=image, ephemeral=True)

    assert result["scan_id"] == "scan_ephemeral"
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/scan")
    assert session.last_kwargs is not None
    assert session.last_kwargs["json"]["ephemeral"] is True
    assert "image_base64" in session.last_kwargs["json"]


def test_scan_receipt_rejects_ephemeral_auto_save_combo(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="ephemeral"):
        client.scan_receipt(
            raw_text="receipt text",
            ephemeral=True,
            auto_save=True,
            project_id="proj_123",
        )


def test_scan_receipt_rejects_auto_save_without_project_id(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="project_id"):
        client.scan_receipt(raw_text="receipt text", auto_save=True)


def test_scan_receipt_rejects_non_https_image_url(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="https"):
        client.scan_receipt(image_url="http://example.com/receipt.jpg")


def test_scan_receipt_rejects_zero_inputs(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.scan_receipt()


def test_scan_receipt_rejects_multiple_inputs(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.scan_receipt(image_url="https://example.com/r.jpg", raw_text="text")


def test_scan_receipt_with_image_url(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"scan_id": "scan_url"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.scan_receipt(image_url="https://example.com/receipt.jpg")

    assert result["scan_id"] == "scan_url"
    assert session.last_kwargs["json"]["image_url"] == "https://example.com/receipt.jpg"
    assert "image_base64" not in session.last_kwargs["json"]


def test_scan_receipt_with_image_base64(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"scan_id": "scan_b64"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.scan_receipt(image_base64="abc123==")

    assert result["scan_id"] == "scan_b64"
    assert session.last_kwargs["json"]["image_base64"] == "abc123=="


def test_scan_receipt_with_raw_text(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"scan_id": "scan_text"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.scan_receipt(raw_text="Starbucks\nTotal: $4.50")

    assert result["scan_id"] == "scan_text"
    assert session.last_kwargs["json"]["raw_text"] == "Starbucks\nTotal: $4.50"


def test_scan_receipt_guesses_image_type_from_file_extension(tmp_path: Path) -> None:
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")
    session = _Session(_Response(200, _ok({"scan_id": "s"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.scan_receipt(file_path=image)

    assert session.last_kwargs["json"].get("image_type") == "image/png"


def test_scan_receipt_raises_when_file_missing(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="does not exist"):
        client.scan_receipt(file_path=tmp_path / "missing.jpg")


def test_scan_receipt_auto_save_sends_project_id(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"scan_id": "s", "transaction_id": "txn_1"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.scan_receipt(
        raw_text="receipt", auto_save=True, project_id="proj_abc"
    )

    assert result["transaction_id"] == "txn_1"
    assert session.last_kwargs["json"]["auto_save"] is True
    assert session.last_kwargs["json"]["project_id"] == "proj_abc"


# ---------------------------------------------------------------------------
# CRUD — transactions
# ---------------------------------------------------------------------------


def test_list_transactions_passes_filter_params(tmp_path: Path) -> None:
    session = _Session(
        _Response(
            200,
            _ok(
                {
                    "transactions": [],
                    "pagination": {
                        "total": 0,
                        "limit": 10,
                        "offset": 5,
                        "has_more": False,
                    },
                }
            ),
        )
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.list_transactions(
        start_date="2026-01-01", amount_min=10, offset=5, limit=10
    )

    assert result["pagination"]["offset"] == 5
    assert session.last_method == "GET"
    assert session.last_kwargs["params"] == {
        "start_date": "2026-01-01",
        "amount_min": 10,
        "offset": 5,
        "limit": 10,
    }


def test_list_transactions_omits_none_params(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"transactions": [], "pagination": {}})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.list_transactions(limit=10)

    assert "start_date" not in session.last_kwargs["params"]
    assert session.last_kwargs["params"] == {"limit": 10}


def test_create_transaction_sends_payload_dropping_none(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"transaction_id": "txn_new"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.create_transaction(
        {
            "date": "2026-03-01",
            "amount": 42.50,
            "transaction_type": "Expense",
            "category": "Food",
            "payment_method": "Card",
            "vendor": None,  # should be dropped
        }
    )

    assert result["transaction_id"] == "txn_new"
    assert "vendor" not in session.last_kwargs["json"]
    assert session.last_method == "POST"


def test_get_transaction_sends_correct_url(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"transaction_id": "txn_abc"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_transaction("txn_abc")

    assert result["transaction_id"] == "txn_abc"
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/transactions/txn_abc")


def test_update_transaction_sends_patch_dropping_none(tmp_path: Path) -> None:
    session = _Session(
        _Response(200, _ok({"transaction_id": "txn_abc", "amount": 99.0}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.update_transaction("txn_abc", {"amount": 99.0, "vendor": None})

    assert result["amount"] == 99.0
    assert session.last_method == "PATCH"
    assert "vendor" not in session.last_kwargs["json"]
    assert session.last_url is not None
    assert session.last_url.endswith("/transactions/txn_abc")


def test_delete_transaction_handles_no_content_response(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_transaction("txn_123")

    assert result == {"status": "deleted", "transaction_id": "txn_123"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/transactions/txn_123")


# ---------------------------------------------------------------------------
# import_transactions
# ---------------------------------------------------------------------------


def test_import_transactions_csv_sets_text_csv_request(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"total": 1, "imported": 1, "failed": 0})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.import_transactions(
        csv_text="date,amount,transaction_type,category,payment_method\n2026-03-01,12.50,Expense,Food,Card",
        all_or_nothing=True,
        project_id="proj_123",
    )

    assert result["imported"] == 1
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/import/transactions")
    assert session.last_kwargs["headers"]["Content-Type"] == "text/csv"
    assert session.last_kwargs["data"].startswith("date,amount")
    assert session.last_kwargs["params"] == {
        "all_or_nothing": "true",
        "project_id": "proj_123",
    }


def test_import_transactions_csv_file_path_reads_from_disk(tmp_path: Path) -> None:
    csv_file = tmp_path / "txns.csv"
    csv_file.write_text(
        "date,amount,transaction_type,category,payment_method\n2026-03-01,50.0,Expense,Food,Card"
    )
    session = _Session(_Response(200, _ok({"total": 1, "imported": 1, "failed": 0})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.import_transactions(csv_file_path=csv_file, all_or_nothing=False)

    assert result["imported"] == 1
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/import/transactions")
    assert session.last_kwargs["headers"]["Content-Type"] == "text/csv"
    # data is a file-like object (may be closed after context exit but ref still held)
    assert hasattr(session.last_kwargs["data"], "read")
    assert session.last_kwargs["params"] == {"all_or_nothing": "false"}


def test_import_transactions_json_sends_application_json(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"total": 2, "imported": 2, "failed": 0})))
    client = ApiClient(_settings(tmp_path), session=session)

    txns = [{"date": "2026-03-01", "amount": 10.0}]
    result = client.import_transactions(transactions=txns, project_id="proj_x")

    assert result["imported"] == 2
    assert session.last_kwargs["json"] == {"transactions": txns, "project_id": "proj_x"}
    assert (
        "params" not in session.last_kwargs or session.last_kwargs.get("params") is None
    )


def test_import_transactions_requires_exactly_one_source(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.import_transactions(
            transactions=[{"date": "2026-03-01"}], csv_text="date,amount"
        )


def test_import_transactions_rejects_zero_sources(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.import_transactions()


# ---------------------------------------------------------------------------
# submit_batch_scans
# ---------------------------------------------------------------------------


def test_submit_batch_scans_sends_correct_payload(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"job_id": "job_1", "status": "processing"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.submit_batch_scans(
        items=[{"image_url": "https://example.com/r.jpg"}],
        auto_save=True,
        project_id="proj_x",
    )

    assert result["job_id"] == "job_1"
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/batch/scans")
    assert session.last_kwargs["json"]["auto_save"] is True
    assert session.last_kwargs["json"]["project_id"] == "proj_x"


def test_submit_batch_scans_converts_file_path_to_base64(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake-image-data")
    session = _Session(_Response(200, _ok({"job_id": "job_2", "status": "processing"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.submit_batch_scans(items=[{"file_path": str(image)}])

    sent_items = session.last_kwargs["json"]["items"]
    assert len(sent_items) == 1
    assert "image_base64" in sent_items[0]
    assert "file_path" not in sent_items[0]
    # base64 of b"fake-image-data"
    import base64

    assert sent_items[0]["image_base64"] == base64.b64encode(b"fake-image-data").decode(
        "ascii"
    )
    assert sent_items[0].get("image_type") == "image/jpeg"


def test_submit_batch_scans_rejects_non_https_url_in_item(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="https"):
        client.submit_batch_scans(items=[{"image_url": "http://example.com/r.jpg"}])


def test_submit_batch_scans_rejects_multiple_inputs_per_item(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.submit_batch_scans(
            items=[
                {
                    "image_url": "https://example.com/r.jpg",
                    "image_base64": "abc==",
                }
            ]
        )


def test_submit_batch_scans_rejects_zero_inputs_per_item(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.submit_batch_scans(items=[{"metadata": {"note": "oops"}}])


def test_submit_batch_scans_rejects_non_dict_item(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="object"):
        client.submit_batch_scans(items=["https://example.com/r.jpg"])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# batch status / results
# ---------------------------------------------------------------------------


def test_get_batch_scan_status_sends_correct_url(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"job_id": "job_99", "status": "completed"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_batch_scan_status("job_99")

    assert result["job_id"] == "job_99"
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/batch/scans/job_99")


def test_get_batch_scan_results_sends_correct_url(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"job_id": "job_99", "results": []})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_batch_scan_results("job_99")

    assert result["results"] == []
    assert session.last_url is not None
    assert session.last_url.endswith("/batch/scans/job_99/results")


# ---------------------------------------------------------------------------
# get_scan
# ---------------------------------------------------------------------------


def test_get_scan_sends_correct_url(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"scan_id": "scan_xyz"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_scan("scan_xyz")

    assert result["scan_id"] == "scan_xyz"
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/scan/scan_xyz")


# ---------------------------------------------------------------------------
# projects
# ---------------------------------------------------------------------------


def test_create_project_sends_name_and_description(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"project_id": "proj_new", "name": "Q1"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.create_project(name="Q1", description="Quarter 1")

    assert result["project_id"] == "proj_new"
    assert session.last_method == "POST"
    assert session.last_kwargs["json"] == {"name": "Q1", "description": "Quarter 1"}


def test_create_project_omits_none_description(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"project_id": "proj_2"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.create_project(name="Minimal")

    assert "description" not in session.last_kwargs["json"]


def test_update_project_sends_patch(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"project_id": "proj_1"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.update_project("proj_1", name="New Name", status="archived")

    assert session.last_method == "PATCH"
    assert session.last_url is not None
    assert session.last_url.endswith("/projects/proj_1")
    assert session.last_kwargs["json"] == {"name": "New Name", "status": "archived"}


def test_delete_project_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_project("proj_1")

    assert result == {"status": "deleted", "project_id": "proj_1"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert session.last_url.endswith("/projects/proj_1")


def test_list_projects_sends_status_filter(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"projects": [], "pagination": {}})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.list_projects(status="active", limit=20)

    assert session.last_method == "GET"
    assert session.last_kwargs["params"] == {"status": "active", "limit": 20}


# ---------------------------------------------------------------------------
# webhooks
# ---------------------------------------------------------------------------


def test_create_webhook_sends_url_and_events(tmp_path: Path) -> None:
    session = _Session(
        _Response(200, _ok({"webhook_id": "wh_1", "url": "https://my.app/wh"}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.create_webhook(url="https://my.app/wh", events=["batch.completed"])

    assert result["webhook_id"] == "wh_1"
    assert session.last_kwargs["json"]["events"] == ["batch.completed"]
    assert "secret" not in session.last_kwargs["json"]


def test_create_webhook_includes_secret_when_provided(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"webhook_id": "wh_2"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.create_webhook(
        url="https://my.app/wh", events=["transaction.created"], secret="mysecret"
    )

    assert session.last_kwargs["json"]["secret"] == "mysecret"


def test_delete_webhook_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_webhook("wh_1")

    assert result == {"status": "deleted", "webhook_id": "wh_1"}
    assert session.last_url is not None
    assert session.last_url.endswith("/webhooks/wh_1")


# ---------------------------------------------------------------------------
# rules
# ---------------------------------------------------------------------------


def test_create_rule_sends_full_payload(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"rule_id": "rule_1"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.create_rule(
        rule_type="vendor_category",
        condition={"vendor": "Starbucks"},
        action={"set_category": "Coffee"},
        priority=1,
    )

    assert result["rule_id"] == "rule_1"
    assert session.last_kwargs["json"]["priority"] == 1
    assert session.last_kwargs["json"]["condition"] == {"vendor": "Starbucks"}


def test_create_rule_omits_priority_when_none(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"rule_id": "rule_2"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.create_rule(
        rule_type="vendor_category",
        condition={"vendor": "Costco"},
        action={"set_category": "Wholesale"},
    )

    assert "priority" not in session.last_kwargs["json"]


def test_delete_rule_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_rule("rule_1")

    assert result == {"status": "deleted", "rule_id": "rule_1"}


# ---------------------------------------------------------------------------
# summary, usage, export
# ---------------------------------------------------------------------------


def test_get_summary_sends_all_params(tmp_path: Path) -> None:
    session = _Session(
        _Response(200, _ok({"totals": {"income": 0, "expense": 0, "net": 0}}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    client.get_summary(period="last_30_days", group_by="category", project_id="proj_x")

    assert session.last_method == "GET"
    assert session.last_kwargs["params"] == {
        "period": "last_30_days",
        "group_by": "category",
        "project_id": "proj_x",
    }


def test_get_usage_sends_period_and_breakdown(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"quota": {"remaining": 50}})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_usage(period="current_month", breakdown="daily")

    assert result["quota"]["remaining"] == 50
    assert session.last_kwargs["params"] == {
        "period": "current_month",
        "breakdown": "daily",
    }


def test_export_transactions_returns_csv_body_when_api_responds_with_csv(
    tmp_path: Path,
) -> None:
    session = _Session(
        _Response(
            200,
            None,
            text="transaction_id,amount\n1,42.50\n",
            headers={"Content-Type": "text/csv"},
        )
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.export_transactions(
        format="csv", filters={"project_id": "proj_123"}
    )

    assert result == {
        "content_type": "text/csv",
        "body": "transaction_id,amount\n1,42.50\n",
    }


def test_export_transactions_json_returns_envelope(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"transactions": [], "total_count": 0})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.export_transactions(format="json")

    assert result["content_type"] == "application/json"
    assert '"total_count": 0' in result["body"]
    assert session.last_kwargs["json"]["format"] == "json"


# ---------------------------------------------------------------------------
# _request — generic behaviour
# ---------------------------------------------------------------------------


def test_missing_api_key_raises_before_network(tmp_path: Path) -> None:
    # Session that would succeed if called — but it should never be reached
    client = ApiClient(
        _settings_no_key(tmp_path), session=_Session(_Response(200, _ok({})))
    )

    with pytest.raises(ApiClientError, match="Missing API key"):
        client.get_usage()


def test_request_wraps_network_exception_as_api_client_error(tmp_path: Path) -> None:
    import requests as req

    client = ApiClient(
        _settings(tmp_path), session=_Session(req.ConnectionError("timeout"))
    )

    with pytest.raises(ApiClientError, match="Request failed"):
        client.get_usage()


def test_request_raises_on_400_with_structured_error(tmp_path: Path) -> None:
    payload = {
        "success": False,
        "error": {"code": "INVALID_REQUEST", "message": "bad date"},
    }
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(400, payload)))

    with pytest.raises(ApiClientError, match="bad date"):
        client.get_usage()


def test_request_raises_on_401_with_plain_error(tmp_path: Path) -> None:
    payload = {
        "success": False,
        "error": {"code": "INVALID_API_KEY", "message": "key revoked"},
    }
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(401, payload)))

    with pytest.raises(ApiClientError, match="key revoked"):
        client.get_scan("scan_1")


def test_request_handles_empty_body_non_204(tmp_path: Path) -> None:
    # Some endpoints may return 200 with empty body
    session = _Session(
        _Response(200, None, text="", headers={"Content-Type": "application/json"})
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.list_webhooks()

    assert result == {"status": "ok"}


def test_request_raises_on_success_false_with_200(tmp_path: Path) -> None:
    payload = {"success": False, "error": {"message": "quota exceeded"}}
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, payload)))

    with pytest.raises(ApiClientError, match="quota exceeded"):
        client.scan_receipt(raw_text="text")


def test_request_raises_on_invalid_json_body(tmp_path: Path) -> None:
    # Response claims JSON content-type but body is not valid JSON
    response = _Response(
        200, None, text="not-json", headers={"Content-Type": "application/json"}
    )
    # Patch json() to raise
    response._payload = None

    class _BrokenResponse(_Response):
        def json(self):
            raise ValueError("invalid json")

    br = _BrokenResponse(
        200, None, text="not-json", headers={"Content-Type": "application/json"}
    )
    client = ApiClient(_settings(tmp_path), session=_Session(br))

    with pytest.raises(ApiClientError, match="Invalid JSON"):
        client.get_usage()


# ---------------------------------------------------------------------------
# URL path quoting
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------


class _CountingSession:
    """Session that raises on the first N calls, then succeeds."""

    def __init__(
        self, fail_count: int, exc: Exception, success_response: _Response
    ) -> None:
        self._fail_count = fail_count
        self._exc = exc
        self._success = success_response
        self.call_count = 0

    def request(self, method: str, url: str, **kwargs):  # noqa: ANN001
        self.call_count += 1
        if self.call_count <= self._fail_count:
            raise self._exc
        return self._success


def test_retry_succeeds_after_transient_failures(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """ConnectionResetError on first 2 calls, success on 3rd."""
    import recite_mcp.api_client as mod

    monkeypatch.setattr(mod, "_RETRY_BACKOFF_BASE", 0.0)  # no delay in tests

    session = _CountingSession(
        2, ConnectionResetError("reset"), _Response(200, _ok({"ok": True}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_usage()

    assert result["ok"] is True
    assert session.call_count == 3


def test_retry_exhausted_raises_api_client_error(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """ConnectionResetError on all 3 calls -> ApiClientError with 'retries' in message."""
    import recite_mcp.api_client as mod

    monkeypatch.setattr(mod, "_RETRY_BACKOFF_BASE", 0.0)

    session = _CountingSession(
        3, ConnectionResetError("reset"), _Response(200, _ok({}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    with pytest.raises(ApiClientError, match="retries"):
        client.get_usage()
    assert session.call_count == 3


def test_non_retryable_error_raises_immediately(tmp_path: Path) -> None:
    """ValueError (non-retryable) -> immediate ApiClientError, no retry."""
    session = _CountingSession(3, ValueError("bad value"), _Response(200, _ok({})))
    client = ApiClient(_settings(tmp_path), session=session)

    with pytest.raises(ApiClientError, match="Request failed"):
        client.get_usage()
    assert session.call_count == 1


def test_path_segment_with_special_chars_is_url_encoded(tmp_path: Path) -> None:
    """IDs containing slashes or spaces must be percent-encoded in URLs."""
    session = _Session(_Response(200, _ok({"transaction_id": "txn/weird id"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.get_transaction("txn/weird id")

    assert session.last_url is not None
    assert "txn/weird" not in session.last_url  # raw slash would break routing
    assert "txn%2Fweird%20id" in session.last_url


# ---------------------------------------------------------------------------
# update_rule (PATCH /rules/:id)
# ---------------------------------------------------------------------------


def test_update_rule_sends_patch_with_provided_fields(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"rule_id": "rule_1", "active": False})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.update_rule("rule_1", {"active": False})

    assert result["rule_id"] == "rule_1"
    assert result["active"] is False
    assert session.last_method == "PATCH"
    assert session.last_url is not None
    assert session.last_url.endswith("/rules/rule_1")
    assert session.last_kwargs["json"] == {"active": False}


def test_update_rule_drops_none_values(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"rule_id": "rule_1"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.update_rule("rule_1", {"active": False, "priority": None})

    assert "priority" not in session.last_kwargs["json"]


def test_update_rule_url_encodes_rule_id(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"rule_id": "rule/special"})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.update_rule("rule/special", {"active": True})

    assert session.last_url is not None
    assert "rule%2Fspecial" in session.last_url


# ---------------------------------------------------------------------------
# categories (GET / POST / DELETE)
# ---------------------------------------------------------------------------


def test_get_categories_returns_all_arrays(tmp_path: Path) -> None:
    data = {
        "default_categories": ["Advertising & Marketing"],
        "custom_categories": ["Equipment Rental"],
        "all_categories": ["Advertising & Marketing", "Equipment Rental"],
    }
    session = _Session(_Response(200, _ok(data)))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_categories()

    assert result["default_categories"] == ["Advertising & Marketing"]
    assert result["custom_categories"] == ["Equipment Rental"]
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/categories")


def test_create_category_sends_name_and_returns_it(tmp_path: Path) -> None:
    session = _Session(_Response(201, _ok({"name": "Equipment Rental"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.create_category("Equipment Rental")

    assert result["name"] == "Equipment Rental"
    assert session.last_method == "POST"
    assert session.last_kwargs["json"] == {"name": "Equipment Rental"}
    assert session.last_url is not None
    assert session.last_url.endswith("/categories")


def test_delete_category_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_category("Equipment Rental")

    assert result == {"status": "deleted", "name": "Equipment Rental"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert "Equipment%20Rental" in session.last_url


def test_delete_category_url_encodes_special_chars(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    client.delete_category("Food & Dining")

    assert session.last_url is not None
    assert "Food%20%26%20Dining" in session.last_url


# ---------------------------------------------------------------------------
# vendors (GET / POST / DELETE)
# ---------------------------------------------------------------------------


def test_get_vendors_returns_custom_vendors(tmp_path: Path) -> None:
    data = {"custom_vendors": ["Acme Corp", "XYZ Ltd"]}
    session = _Session(_Response(200, _ok(data)))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_vendors()

    assert result["custom_vendors"] == ["Acme Corp", "XYZ Ltd"]
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/vendors")


def test_create_vendor_sends_name_and_returns_it(tmp_path: Path) -> None:
    session = _Session(_Response(201, _ok({"name": "Acme Corp"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.create_vendor("Acme Corp")

    assert result["name"] == "Acme Corp"
    assert session.last_method == "POST"
    assert session.last_kwargs["json"] == {"name": "Acme Corp"}
    assert session.last_url is not None
    assert session.last_url.endswith("/vendors")


def test_delete_vendor_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_vendor("Acme Corp")

    assert result == {"status": "deleted", "name": "Acme Corp"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert "Acme%20Corp" in session.last_url


def test_delete_vendor_url_encodes_special_chars(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    client.delete_vendor("Café & Bistro")

    assert session.last_url is not None
    assert "Caf%C3%A9%20%26%20Bistro" in session.last_url


def test_api_client_list_rules_without_params(tmp_path: Path) -> None:
    session = _Session(_Response(200, {"success": True, "data": []}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.list_rules()
    assert result == []


def test_api_client_request_handles_none_data(tmp_path: Path) -> None:
    # payload is a list (not dict), so it falls through to 'return {"data": payload}'
    session = _Session(_Response(200, [{"a": "b"}]))
    client = ApiClient(_settings(tmp_path), session=session)
    result = client.list_rules()
    assert result == {"data": [{"a": "b"}]}


def test_api_client_request_handles_dict_without_data(tmp_path: Path) -> None:
    session = _Session(_Response(200, {"success": True, "something": "else"}))
    client = ApiClient(_settings(tmp_path), session=session)
    result = client.list_rules()
    assert result == {"success": True, "something": "else"}


def test_api_client_dispatch_request_unsupported_session(tmp_path: Path) -> None:
    class UnsupportedSession:
        pass

    client = ApiClient(_settings(tmp_path), session=UnsupportedSession())
    with pytest.raises(
        ApiClientError, match="Configured session does not support HTTP requests"
    ):
        client.list_rules()


def test_api_client_dispatch_request_fallback_method(tmp_path: Path) -> None:
    class FallbackSession:
        def get(self, url, **kwargs):
            return _Response(200, {"success": True, "data": []})

    client = ApiClient(_settings(tmp_path), session=FallbackSession())
    result = client.list_rules()
    assert result == []


def test_api_client_extract_error_message_non_json(tmp_path: Path) -> None:
    class BadJson:
        status_code = 500
        text = "Internal Server Error Text"

        def json(self):
            raise Exception("no json")

    from recite_mcp.api_client import _extract_error_message

    assert (
        _extract_error_message(BadJson())
        == "Recite API error (500): Internal Server Error Text"
    )


def test_api_client_extract_error_message_non_json_empty_text(tmp_path: Path) -> None:
    class BadJsonEmpty:
        status_code = 502
        text = ""

        def json(self):
            raise Exception("no json")

    from recite_mcp.api_client import _extract_error_message

    assert _extract_error_message(BadJsonEmpty()) == "Recite API error: 502"


def test_api_client_extract_error_message_generic_payload(tmp_path: Path) -> None:
    class JsonListResponse:
        status_code = 404

        def json(self):
            return ["not", "a", "dict"]

    from recite_mcp.api_client import _extract_error_message

    assert _extract_error_message(JsonListResponse()) == "Recite API error: 404"


def test_api_client_extract_error_message_from_payload_string(tmp_path: Path) -> None:
    from recite_mcp.api_client import _extract_error_message_from_payload

    payload = {"error": "A string error message"}
    assert _extract_error_message_from_payload(payload) == "A string error message"


def test_api_client_extract_error_message_from_payload_fallback(tmp_path: Path) -> None:
    from recite_mcp.api_client import _extract_error_message_from_payload

    payload = {}
    assert _extract_error_message_from_payload(payload) == "Unknown API error"


# ---------------------------------------------------------------------------
# bank statements
# ---------------------------------------------------------------------------


def test_upload_bank_statement_sends_csv_text(tmp_path: Path) -> None:
    session = _Session(
        _Response(200, _ok({"statement_id": "stmt_1", "status": "uploaded"}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.upload_bank_statement(
        csv_text="date,description,amount\n2026-01-15,Deposit,1000.00",
        account_name="Checking",
        statement_date="2026-01-15",
    )

    assert result["statement_id"] == "stmt_1"
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/bank-statements")
    assert session.last_kwargs["headers"]["Content-Type"] == "text/csv"
    assert session.last_kwargs["data"].startswith("date,description")
    assert session.last_kwargs["params"]["account_name"] == "Checking"
    assert session.last_kwargs["params"]["statement_date"] == "2026-01-15"


def test_upload_bank_statement_sends_csv_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "stmt.csv"
    csv_file.write_text("date,description,amount\n2026-01-15,Deposit,500.00")
    session = _Session(
        _Response(200, _ok({"statement_id": "stmt_2", "status": "uploaded"}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.upload_bank_statement(
        csv_file_path=csv_file, account_name="Savings"
    )

    assert result["statement_id"] == "stmt_2"
    assert session.last_method == "POST"
    assert session.last_kwargs["headers"]["Content-Type"] == "text/csv"
    assert hasattr(session.last_kwargs["data"], "read")
    assert session.last_kwargs["params"]["account_name"] == "Savings"


def test_upload_bank_statement_rejects_both_sources(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.upload_bank_statement(
            csv_text="date,amount",
            csv_file_path="/some/file.csv",
        )


def test_upload_bank_statement_rejects_zero_sources(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, _ok({}))))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.upload_bank_statement(account_name="Checking")


def test_list_bank_statements_passes_filter_params(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"statements": [], "pagination": {}})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.list_bank_statements(
        account_name="Checking", status="processed", limit=10, offset=5
    )

    assert session.last_method == "GET"
    assert session.last_kwargs["params"] == {
        "account_name": "Checking",
        "status": "processed",
        "limit": 10,
        "offset": 5,
    }


def test_get_bank_statement_sends_correct_url(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"statement_id": "stmt_abc"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_bank_statement("stmt_abc")

    assert result["statement_id"] == "stmt_abc"
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/bank-statements/stmt_abc")


def test_delete_bank_statement_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_bank_statement("stmt_123")

    assert result == {"status": "deleted", "statement_id": "stmt_123"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert session.last_url.endswith("/bank-statements/stmt_123")


def test_export_bank_statement_sends_correct_url(tmp_path: Path) -> None:
    session = _Session(
        _Response(
            200,
            None,
            text="date,description,amount\n2026-01-15,Deposit,1000.00\n",
            headers={"Content-Type": "text/csv"},
        )
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.export_bank_statement("stmt_abc", format="csv")

    assert result == {
        "content_type": "text/csv",
        "body": "date,description,amount\n2026-01-15,Deposit,1000.00\n",
    }
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/bank-statements/stmt_abc/export")
    assert session.last_kwargs["params"] == {"format": "csv"}


# ---------------------------------------------------------------------------
# bank transactions
# ---------------------------------------------------------------------------


def test_list_bank_transactions_passes_filter_params(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"transactions": [], "pagination": {}})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.list_bank_transactions(
        statement_id="stmt_1", start_date="2026-01-01", amount_min=10, limit=20
    )

    assert session.last_method == "GET"
    assert session.last_kwargs["params"] == {
        "statement_id": "stmt_1",
        "start_date": "2026-01-01",
        "amount_min": 10,
        "limit": 20,
    }


def test_get_bank_transaction_sends_correct_url(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"bank_transaction_id": "btxn_abc"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_bank_transaction("btxn_abc")

    assert result["bank_transaction_id"] == "btxn_abc"
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/bank-transactions/btxn_abc")


def test_update_bank_transaction_sends_patch_dropping_none(tmp_path: Path) -> None:
    session = _Session(
        _Response(200, _ok({"bank_transaction_id": "btxn_abc", "status": "matched"}))
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.update_bank_transaction(
        "btxn_abc", {"status": "matched", "notes": None}
    )

    assert result["status"] == "matched"
    assert session.last_method == "PATCH"
    assert "notes" not in session.last_kwargs["json"]
    assert session.last_url is not None
    assert session.last_url.endswith("/bank-transactions/btxn_abc")


def test_delete_bank_transaction_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_bank_transaction("btxn_123")

    assert result == {"status": "deleted", "bank_transaction_id": "btxn_123"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert session.last_url.endswith("/bank-transactions/btxn_123")


# ---------------------------------------------------------------------------
# reconciliation
# ---------------------------------------------------------------------------


def test_create_reconciliation_link_sends_payload(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"link_id": "link_1", "status": "active"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.create_reconciliation_link(
        transaction_id="txn_1",
        bank_transaction_id="btxn_1",
        link_type="manual",
    )

    assert result["link_id"] == "link_1"
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/reconciliation/links")
    assert session.last_kwargs["json"]["transaction_id"] == "txn_1"
    assert session.last_kwargs["json"]["bank_transaction_id"] == "btxn_1"
    assert session.last_kwargs["json"]["link_type"] == "manual"


def test_list_reconciliation_links_passes_filter_params(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"links": [], "pagination": {}})))
    client = ApiClient(_settings(tmp_path), session=session)

    client.list_reconciliation_links(statement_id="stmt_1", link_type="auto", limit=25)

    assert session.last_method == "GET"
    assert session.last_kwargs["params"] == {
        "statement_id": "stmt_1",
        "link_type": "auto",
        "limit": 25,
    }


def test_update_reconciliation_link_sends_patch(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"link_id": "link_1", "status": "broken"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.update_reconciliation_link("link_1", {"status": "broken"})

    assert result["status"] == "broken"
    assert session.last_method == "PATCH"
    assert session.last_url is not None
    assert session.last_url.endswith("/reconciliation/links/link_1")
    assert session.last_kwargs["json"] == {"status": "broken"}


def test_delete_reconciliation_link_returns_status_deleted(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_reconciliation_link("link_123")

    assert result == {"status": "deleted", "link_id": "link_123"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert session.last_url.endswith("/reconciliation/links/link_123")


def test_run_auto_match_sends_payload(tmp_path: Path) -> None:
    session = _Session(_Response(200, _ok({"matches_found": 5, "status": "completed"})))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.run_auto_match(
        statement_id="stmt_1", strategy="fuzzy", min_confidence=0.8
    )

    assert result["matches_found"] == 5
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/reconciliation/auto-match")
    assert session.last_kwargs["json"]["statement_id"] == "stmt_1"
    assert session.last_kwargs["json"]["strategy"] == "fuzzy"
    assert session.last_kwargs["json"]["min_confidence"] == 0.8


def test_get_reconciliation_summary_sends_statement_id(tmp_path: Path) -> None:
    session = _Session(
        _Response(
            200,
            _ok({"matched": 10, "unmatched": 3, "total": 13}),
        )
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.get_reconciliation_summary(statement_id="stmt_1")

    assert result["matched"] == 10
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/reconciliation/summary")
    assert session.last_kwargs["params"] == {"statement_id": "stmt_1"}


def test_export_reconciliation_returns_csv(tmp_path: Path) -> None:
    session = _Session(
        _Response(
            200,
            None,
            text="link_id,transaction_id,bank_transaction_id\nlink_1,txn_1,btxn_1\n",
            headers={"Content-Type": "text/csv"},
        )
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.export_reconciliation(format="csv", statement_id="stmt_1")

    assert result == {
        "content_type": "text/csv",
        "body": "link_id,transaction_id,bank_transaction_id\nlink_1,txn_1,btxn_1\n",
    }
    assert session.last_method == "GET"
    assert session.last_url is not None
    assert session.last_url.endswith("/reconciliation/export")
    assert session.last_kwargs["params"] == {
        "format": "csv",
        "statement_id": "stmt_1",
    }
