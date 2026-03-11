from __future__ import annotations

from pathlib import Path

import pytest

from recite_mcp.api_client import ApiClient, ApiClientError
from recite_mcp.config import Settings


class _Response:
    def __init__(
        self,
        status_code: int,
        payload: dict | None = None,
        *,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
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


def test_process_receipt_success(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    payload = {
        "success": True,
        "data": {"vendor": "Store", "date": "2026-02-22", "total": 10.5, "tax": 0.5, "currency": "USD"},
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
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(500, {"error": "failed"})))

    with pytest.raises(ApiClientError):
        client.process_receipt(image)


def test_process_receipt_raises_when_success_is_false(tmp_path: Path) -> None:
    image = tmp_path / "receipt.jpg"
    image.write_bytes(b"fake")
    payload = {"success": False, "error": {"message": "invalid image"}}
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, payload)))

    with pytest.raises(ApiClientError):
        client.process_receipt(image)


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

    assert result["data"]["scan_id"] == "scan_ephemeral"
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/scan")
    assert session.last_kwargs is not None
    assert session.last_kwargs["json"]["ephemeral"] is True
    assert "image_base64" in session.last_kwargs["json"]


def test_scan_receipt_rejects_ephemeral_auto_save_combo(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, {"success": True, "data": {}})))

    with pytest.raises(ApiClientError, match="ephemeral"):
        client.scan_receipt(raw_text="receipt text", ephemeral=True, auto_save=True, project_id="proj_123")


def test_list_transactions_passes_filter_params(tmp_path: Path) -> None:
    session = _Session(
        _Response(
            200,
            {
                "success": True,
                "data": {
                    "transactions": [],
                    "pagination": {"total": 0, "limit": 10, "offset": 5, "has_more": False},
                },
            },
        )
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.list_transactions(start_date="2026-01-01", amount_min=10, offset=5, limit=10)

    assert result["data"]["pagination"]["offset"] == 5
    assert session.last_method == "GET"
    assert session.last_kwargs is not None
    assert session.last_kwargs["params"] == {
        "start_date": "2026-01-01",
        "amount_min": 10,
        "offset": 5,
        "limit": 10,
    }


def test_import_transactions_csv_sets_text_csv_request(tmp_path: Path) -> None:
    session = _Session(_Response(200, {"success": True, "data": {"total": 1, "imported": 1, "failed": 0}}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.import_transactions(
        csv_text="date,amount,transaction_type,category,payment_method\n2026-03-01,12.50,Expense,Food,Card",
        all_or_nothing=True,
        project_id="proj_123",
    )

    assert result["data"]["imported"] == 1
    assert session.last_method == "POST"
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/import/transactions")
    assert session.last_kwargs is not None
    assert session.last_kwargs["headers"]["Content-Type"] == "text/csv"
    assert session.last_kwargs["data"].startswith("date,amount")
    assert session.last_kwargs["params"] == {"all_or_nothing": "true", "project_id": "proj_123"}


def test_import_transactions_requires_exactly_one_source(tmp_path: Path) -> None:
    client = ApiClient(_settings(tmp_path), session=_Session(_Response(200, {"success": True, "data": {}})))

    with pytest.raises(ApiClientError, match="exactly one"):
        client.import_transactions(transactions=[{"date": "2026-03-01"}], csv_text="date,amount")


def test_delete_transaction_handles_no_content_response(tmp_path: Path) -> None:
    session = _Session(_Response(204, None, headers={"Content-Type": ""}))
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.delete_transaction("txn_123")

    assert result == {"status": "deleted", "transaction_id": "txn_123"}
    assert session.last_method == "DELETE"
    assert session.last_url is not None
    assert session.last_url.endswith("/apiV1/api/v1/transactions/txn_123")


def test_export_transactions_returns_csv_body_when_api_responds_with_csv(tmp_path: Path) -> None:
    session = _Session(
        _Response(
            200,
            None,
            text="transaction_id,amount\n1,42.50\n",
            headers={"Content-Type": "text/csv"},
        )
    )
    client = ApiClient(_settings(tmp_path), session=session)

    result = client.export_transactions(format="csv", filters={"project_id": "proj_123"})

    assert result == {
        "content_type": "text/csv",
        "body": "transaction_id,amount\n1,42.50\n",
    }
