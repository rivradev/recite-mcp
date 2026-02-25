from __future__ import annotations

import base64
from pathlib import Path

import requests

from recite_mcp.config import Settings
from recite_mcp.models import ReceiptRecord


class ApiClientError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, settings: Settings, session: object | None = None) -> None:
        self._settings = settings
        self._session = session if session is not None else requests.Session()

    def process_receipt(self, file_path: Path) -> ReceiptRecord:
        if not file_path.exists():
            raise ApiClientError(f"Receipt file does not exist: {file_path}")
        if not self._settings.api_key:
            raise ApiClientError("Missing API key.")

        image_base64 = base64.b64encode(file_path.read_bytes()).decode("ascii")
        try:
            response = self._session.post(  # type: ignore[attr-defined]
                f"{self._settings.api_base_url}/scan",
                headers={"Authorization": f"Bearer {self._settings.api_key}", "Content-Type": "application/json"},
                json={"image_base64": image_base64, "auto_save": False},
                timeout=self._settings.request_timeout_sec,
            )
        except Exception as exc:  # noqa: BLE001
            raise ApiClientError(f"Request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ApiClientError(f"Recite API error: {response.status_code}")

        payload = response.json()
        if isinstance(payload, dict) and payload.get("success") is False:
            error = payload.get("error")
            if isinstance(error, dict):
                message = str(error.get("message", "Unknown API error"))
            else:
                message = str(error or "Unknown API error")
            raise ApiClientError(message)

        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(data, dict):
            raise ApiClientError(f"Invalid response payload: {payload}")

        vendor = _pick_first(data, "vendor", "merchant_name", "merchant", "store_name")
        date = _pick_first(data, "date", "transaction_date", "purchase_date")
        total = _pick_first(data, "total", "amount", "total_amount")
        tax = _pick_first(data, "tax", "sales_tax", "tax_amount", default=0.0)
        currency = _pick_first(data, "currency", "currency_code", default="USD")
        category = _pick_first(data, "category", "category_name", default=None)

        try:
            return ReceiptRecord(
                vendor=str(vendor),
                date=str(date),
                total=float(total),
                tax=float(tax),
                currency=str(currency),
                category=str(category) if category is not None else None,
            )
        except Exception as exc:  # noqa: BLE001
            raise ApiClientError(f"Invalid response payload: {payload}") from exc


def _pick_first(payload: dict, *keys: str, default: object | None = None) -> object | None:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default
