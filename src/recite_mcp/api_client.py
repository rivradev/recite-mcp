from __future__ import annotations

import base64
import json
import mimetypes
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from recite_mcp.config import Settings
from recite_mcp.models import ReceiptRecord

_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 0.5
_RETRYABLE_EXCEPTIONS = (ConnectionResetError, ConnectionError, OSError)


class ApiClientError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, settings: Settings, session: object | None = None) -> None:
        self._settings = settings
        self._session = session if session is not None else requests.Session()

    def process_receipt(self, file_path: Path) -> ReceiptRecord:
        data = self.scan_receipt(file_path=file_path, auto_save=False)
        if not isinstance(data, dict):
            raise ApiClientError(f"Invalid response payload: {data}")

        extracted = data.get("extracted_data", data)
        if not isinstance(extracted, dict):
            raise ApiClientError(f"Invalid response payload: {data}")

        vendor = _pick_first(
            extracted, "vendor", "merchant_name", "merchant", "store_name"
        )
        date = _pick_first(extracted, "date", "transaction_date", "purchase_date")
        total = _pick_first(extracted, "total", "amount", "total_amount", default=0.0)
        tax = _pick_first(extracted, "tax", "sales_tax", "tax_amount", default=0.0)
        currency = _pick_first(extracted, "currency", "currency_code", default="USD")
        category = _pick_first(extracted, "category", "category_name", default=None)

        try:
            return ReceiptRecord(
                vendor=str(vendor) if vendor is not None else "",
                date=str(date),
                total=float(total),
                tax=float(tax),
                currency=str(currency),
                category=str(category) if category is not None else None,
            )
        except Exception as exc:  # noqa: BLE001
            raise ApiClientError(f"Invalid response payload: {data}") from exc

    def scan_receipt(
        self,
        *,
        file_path: str | Path | None = None,
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
        payload = self._build_scan_payload(
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
        return self._request("POST", "/scan", json=payload)

    def get_scan(self, scan_id: str) -> dict[str, Any]:
        return self._request("GET", f"/scan/{_quote_path(scan_id)}")

    def create_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
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
        return self._request("POST", "/transactions", json=_drop_none(transaction))

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
        params = _drop_none(
            {
                "start_date": start_date,
                "end_date": end_date,
                "transaction_type": transaction_type,
                "category": category,
                "vendor": vendor,
                "payment_method": payment_method,
                "amount_min": amount_min,
                "amount_max": amount_max,
                "status": status,
                "project_id": project_id,
                "source": source,
                "agent_name": agent_name,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "limit": limit,
                "offset": offset,
                "format": format,
            }
        )
        return self._request("GET", "/transactions", params=params)

    def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._request("GET", f"/transactions/{_quote_path(transaction_id)}")

    def update_transaction(
        self, transaction_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/transactions/{_quote_path(transaction_id)}",
            json=_drop_none(changes),
        )

    def delete_transaction(self, transaction_id: str) -> dict[str, Any]:
        self._request("DELETE", f"/transactions/{_quote_path(transaction_id)}")
        return {"status": "deleted", "transaction_id": transaction_id}

    def import_transactions(
        self,
        *,
        transactions: list[dict[str, Any]] | None = None,
        csv_text: str | None = None,
        csv_file_path: str | Path | None = None,
        all_or_nothing: bool | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Import multiple transactions at once.

        Provide exactly one data source: transactions (list), csv_text, or csv_file_path.

        Args:
            transactions: List of transaction objects to import.
            csv_text: Raw CSV string content.
            csv_file_path: Local path to a CSV file.
            all_or_nothing: If True, fails the entire import if any transaction fails.
            project_id: Apply all transactions to this project UUID.
        """
        provided = [
            transactions is not None,
            csv_text is not None,
            csv_file_path is not None,
        ]
        if sum(provided) != 1:
            raise ApiClientError(
                "Provide exactly one of transactions, csv_text, or csv_file_path."
            )

        if transactions is not None:
            payload = {"transactions": transactions}
            if all_or_nothing is not None:
                payload["all_or_nothing"] = all_or_nothing
            if project_id is not None:
                payload["project_id"] = project_id
            return self._request("POST", "/import/transactions", json=payload)

        params = _drop_none(
            {
                "all_or_nothing": _bool_query_param(all_or_nothing)
                if all_or_nothing is not None
                else None,
                "project_id": project_id,
            }
        )

        if csv_text is not None:
            return self._request(
                "POST",
                "/import/transactions",
                params=params,
                data=csv_text,
                headers={"Content-Type": "text/csv"},
            )

        # We know csv_file_path is not None because exactly one source was provided
        with open(Path(str(csv_file_path)).expanduser(), "rb") as f:
            return self._request(
                "POST",
                "/import/transactions",
                params=params,
                data=f,
                headers={"Content-Type": "text/csv"},
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
        normalized_items = [self._normalize_batch_item(item) for item in items]
        payload: dict[str, Any] = {"items": normalized_items, "auto_save": auto_save}
        optional_fields = {
            "save_threshold": save_threshold,
            "project_id": project_id,
            "webhook_url": webhook_url,
            "webhook_secret": webhook_secret,
        }
        payload.update(_drop_none(optional_fields))
        return self._request("POST", "/batch/scans", json=payload)

    def get_batch_scan_status(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/batch/scans/{_quote_path(job_id)}")

    def get_batch_scan_results(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/batch/scans/{_quote_path(job_id)}/results")

    def list_projects(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {"status": status, "limit": limit, "offset": offset, "format": format}
        )
        return self._request("GET", "/projects", params=params)

    def create_project(
        self, *, name: str, description: str | None = None
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/projects",
            json=_drop_none({"name": name, "description": description}),
        )

    def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        payload = _drop_none(
            {"name": name, "description": description, "status": status}
        )
        return self._request(
            "PATCH", f"/projects/{_quote_path(project_id)}", json=payload
        )

    def delete_project(self, project_id: str) -> dict[str, Any]:
        self._request("DELETE", f"/projects/{_quote_path(project_id)}")
        return {"status": "deleted", "project_id": project_id}

    def get_summary(
        self,
        *,
        period: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        project_id: str | None = None,
        group_by: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "project_id": project_id,
                "group_by": group_by,
            }
        )
        return self._request("GET", "/summary", params=params)

    def create_webhook(
        self, *, url: str, events: list[str], secret: str | None = None
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/webhooks",
            json=_drop_none({"url": url, "events": events, "secret": secret}),
        )

    def list_webhooks(self) -> dict[str, Any]:
        return self._request("GET", "/webhooks")

    def delete_webhook(self, webhook_id: str) -> dict[str, Any]:
        self._request("DELETE", f"/webhooks/{_quote_path(webhook_id)}")
        return {"status": "deleted", "webhook_id": webhook_id}

    def create_rule(
        self,
        *,
        rule_type: str,
        condition: dict[str, Any],
        action: dict[str, Any],
        priority: int | None = None,
    ) -> dict[str, Any]:
        payload = {"rule_type": rule_type, "condition": condition, "action": action}
        if priority is not None:
            payload["priority"] = priority
        return self._request("POST", "/rules", json=payload)

    def list_rules(
        self, *, limit: int | None = None, offset: int | None = None
    ) -> dict[str, Any]:
        return self._request(
            "GET", "/rules", params=_drop_none({"limit": limit, "offset": offset})
        )

    def delete_rule(self, rule_id: str) -> dict[str, Any]:
        self._request("DELETE", f"/rules/{_quote_path(rule_id)}")
        return {"status": "deleted", "rule_id": rule_id}

    def update_rule(self, rule_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/rules/{_quote_path(rule_id)}",
            json=_drop_none(changes),
        )

    def get_categories(self) -> dict[str, Any]:
        return self._request("GET", "/categories")

    def create_category(self, name: str) -> dict[str, Any]:
        return self._request("POST", "/categories", json={"name": name})

    def delete_category(self, name: str) -> dict[str, Any]:
        self._request("DELETE", f"/categories/{_quote_path(name)}")
        return {"status": "deleted", "name": name}

    def get_vendors(self) -> dict[str, Any]:
        return self._request("GET", "/vendors")

    def create_vendor(self, name: str) -> dict[str, Any]:
        return self._request("POST", "/vendors", json={"name": name})

    def delete_vendor(self, name: str) -> dict[str, Any]:
        self._request("DELETE", f"/vendors/{_quote_path(name)}")
        return {"status": "deleted", "name": name}

    def get_usage(
        self, *, period: str | None = None, breakdown: str | None = None
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/usage",
            params=_drop_none({"period": period, "breakdown": breakdown}),
        )

    def export_transactions(
        self, *, format: str, filters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        result = self._request(
            "POST", "/export", json=_drop_none({"format": format, "filters": filters})
        )
        if "content_type" not in result:
            return {"content_type": "application/json", "body": json.dumps(result)}
        return result

    def upload_bank_statement(
        self,
        *,
        csv_file_path: str | Path | None = None,
        csv_text: str | None = None,
        account_name: str | None = None,
        statement_date: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        provided = [csv_file_path is not None, csv_text is not None]
        if sum(provided) != 1:
            raise ApiClientError("Provide exactly one of csv_file_path or csv_text.")

        params = _drop_none(
            {
                "account_name": account_name,
                "statement_date": statement_date,
                "source": source,
                "metadata": json.dumps(metadata) if metadata is not None else None,
            }
        )

        if csv_text is not None:
            return self._request(
                "POST",
                "/bank-statements",
                params=params,
                data=csv_text,
                headers={"Content-Type": "text/csv"},
            )

        with open(Path(str(csv_file_path)).expanduser(), "rb") as f:
            return self._request(
                "POST",
                "/bank-statements",
                params=params,
                data=f,
                headers={"Content-Type": "text/csv"},
            )

    def list_bank_statements(
        self,
        *,
        account_name: str | None = None,
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {
                "account_name": account_name,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "offset": offset,
                "format": format,
            }
        )
        return self._request("GET", "/bank-statements", params=params)

    def get_bank_statement(self, statement_id: str) -> dict[str, Any]:
        return self._request("GET", f"/bank-statements/{_quote_path(statement_id)}")

    def delete_bank_statement(self, statement_id: str) -> dict[str, Any]:
        self._request("DELETE", f"/bank-statements/{_quote_path(statement_id)}")
        return {"status": "deleted", "statement_id": statement_id}

    def export_bank_statement(
        self, statement_id: str, *, format: str | None = None
    ) -> dict[str, Any]:
        result = self._request(
            "GET",
            f"/bank-statements/{_quote_path(statement_id)}/export",
            params=_drop_none({"format": format}),
        )
        if "content_type" not in result:
            return {"content_type": "application/json", "body": json.dumps(result)}
        return result

    def list_bank_transactions(
        self,
        *,
        statement_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        amount_min: float | int | None = None,
        amount_max: float | int | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {
                "statement_id": statement_id,
                "start_date": start_date,
                "end_date": end_date,
                "amount_min": amount_min,
                "amount_max": amount_max,
                "status": status,
                "limit": limit,
                "offset": offset,
                "format": format,
            }
        )
        return self._request("GET", "/bank-transactions", params=params)

    def get_bank_transaction(self, bank_transaction_id: str) -> dict[str, Any]:
        return self._request(
            "GET", f"/bank-transactions/{_quote_path(bank_transaction_id)}"
        )

    def update_bank_transaction(
        self, bank_transaction_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/bank-transactions/{_quote_path(bank_transaction_id)}",
            json=_drop_none(changes),
        )

    def delete_bank_transaction(self, bank_transaction_id: str) -> dict[str, Any]:
        self._request(
            "DELETE", f"/bank-transactions/{_quote_path(bank_transaction_id)}"
        )
        return {"status": "deleted", "bank_transaction_id": bank_transaction_id}

    def create_reconciliation_link(
        self,
        *,
        transaction_id: str,
        bank_transaction_id: str,
        link_type: str | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "transaction_id": transaction_id,
            "bank_transaction_id": bank_transaction_id,
        }
        payload.update(
            _drop_none(
                {
                    "link_type": link_type,
                    "notes": notes,
                    "metadata": metadata,
                }
            )
        )
        return self._request("POST", "/reconciliation/links", json=payload)

    def list_reconciliation_links(
        self,
        *,
        statement_id: str | None = None,
        transaction_id: str | None = None,
        bank_transaction_id: str | None = None,
        link_type: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {
                "statement_id": statement_id,
                "transaction_id": transaction_id,
                "bank_transaction_id": bank_transaction_id,
                "link_type": link_type,
                "status": status,
                "limit": limit,
                "offset": offset,
                "format": format,
            }
        )
        return self._request("GET", "/reconciliation/links", params=params)

    def update_reconciliation_link(
        self, link_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/reconciliation/links/{_quote_path(link_id)}",
            json=_drop_none(changes),
        )

    def delete_reconciliation_link(self, link_id: str) -> dict[str, Any]:
        self._request("DELETE", f"/reconciliation/links/{_quote_path(link_id)}")
        return {"status": "deleted", "link_id": link_id}

    def run_auto_match(
        self,
        *,
        statement_id: str | None = None,
        strategy: str | None = None,
        min_confidence: float | None = None,
        dry_run: bool | None = None,
    ) -> dict[str, Any]:
        payload = _drop_none(
            {
                "statement_id": statement_id,
                "strategy": strategy,
                "min_confidence": min_confidence,
                "dry_run": dry_run,
            }
        )
        return self._request("POST", "/reconciliation/auto-match", json=payload)

    def get_reconciliation_summary(
        self, *, statement_id: str | None = None
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/reconciliation/summary",
            params=_drop_none({"statement_id": statement_id}),
        )

    def get_reconciliation_recommendations(
        self,
        *,
        bank_transaction_id: str,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/reconciliation/recommend",
            json=_drop_none({"bank_transaction_id": bank_transaction_id, "limit": limit}),
        )

    def export_reconciliation(
        self,
        *,
        format: str | None = None,
        statement_id: str | None = None,
    ) -> dict[str, Any]:
        result = self._request(
            "GET",
            "/reconciliation/export",
            params=_drop_none({"format": format, "statement_id": statement_id}),
        )
        if "content_type" not in result:
            return {"content_type": "application/json", "body": json.dumps(result)}
        return result

    def _build_scan_payload(
        self,
        *,
        file_path: str | Path | None,
        image_url: str | None,
        image_base64: str | None,
        raw_text: str | None,
        auto_save: bool,
        save_threshold: str | None,
        project_id: str | None,
        status: str | None,
        image_type: str | None,
        idempotency_key: str | None,
        metadata: dict[str, Any] | None,
        ephemeral: bool,
    ) -> dict[str, Any]:
        provided_inputs = [
            file_path is not None,
            image_url is not None,
            image_base64 is not None,
            raw_text is not None,
        ]
        if sum(provided_inputs) != 1:
            raise ApiClientError(
                "Provide exactly one of file_path, image_url, image_base64, or raw_text."
            )
        if ephemeral and auto_save:
            raise ApiClientError("ephemeral and auto_save cannot both be true.")
        if auto_save and not project_id:
            raise ApiClientError("project_id is required when auto_save is true.")
        if image_url is not None and not image_url.startswith("https://"):
            raise ApiClientError("image_url must use https://.")

        payload: dict[str, Any] = {"auto_save": auto_save, "ephemeral": ephemeral}

        if file_path is not None:
            resolved = Path(file_path).expanduser()
            encoded = self._encode_image_file(resolved)
            payload["image_base64"] = encoded
            if image_type is None:
                image_type = _guess_image_type(resolved)
        elif image_url is not None:
            payload["image_url"] = image_url
        elif image_base64 is not None:
            payload["image_base64"] = image_base64
        else:
            payload["raw_text"] = raw_text

        payload.update(
            _drop_none(
                {
                    "save_threshold": save_threshold,
                    "project_id": project_id,
                    "status": status,
                    "image_type": image_type,
                    "idempotency_key": idempotency_key,
                    "metadata": metadata,
                }
            )
        )
        return payload

    def _normalize_batch_item(self, item: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise ApiClientError("Each batch item must be an object.")

        normalized = dict(item)
        file_path = normalized.pop("file_path", None)
        image_url = normalized.get("image_url")
        image_base64 = normalized.get("image_base64")

        provided_inputs = [
            file_path is not None,
            image_url is not None,
            image_base64 is not None,
        ]
        if sum(provided_inputs) != 1:
            raise ApiClientError(
                "Each batch item must provide exactly one of file_path, image_url, or image_base64."
            )

        if file_path is not None:
            resolved = Path(file_path).expanduser()
            normalized["image_base64"] = self._encode_image_file(resolved)
            normalized.setdefault("image_type", _guess_image_type(resolved))
        elif image_url is not None and not str(image_url).startswith("https://"):
            raise ApiClientError("Batch image_url values must use https://.")

        return _drop_none(normalized)

    def _encode_image_file(self, file_path: Path) -> str:
        if not file_path.exists():
            raise ApiClientError(f"Receipt file does not exist: {file_path}")
        return base64.b64encode(file_path.read_bytes()).decode("ascii")

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not self._settings.api_key:
            raise ApiClientError("Missing API key.")

        request_headers = {"Authorization": f"Bearer {self._settings.api_key}"}
        if headers is not None:
            request_headers.update(headers)
        elif json is not None:
            request_headers["Content-Type"] = "application/json"

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = self._dispatch_request(
                    method=method,
                    url=f"{self._settings.api_base_url}{path}",
                    headers=request_headers,
                    params=params,
                    json=json,
                    data=data,
                    timeout=self._settings.request_timeout_sec,
                )
                break
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_BACKOFF_BASE * (2**attempt))
                continue
            except Exception as exc:  # noqa: BLE001
                raise ApiClientError(f"Request failed: {exc}") from exc
        else:
            raise ApiClientError(
                f"Request failed after {_MAX_RETRIES} retries: {last_exc}"
            ) from last_exc

        if response.status_code >= 400:
            raise ApiClientError(_extract_error_message(response))

        if response.status_code == 204:
            return {"status": "ok"}

        content_type = str(
            getattr(response, "headers", {}).get("Content-Type", "")
        ).lower()
        if not content_type or "json" in content_type:
            text = getattr(response, "text", "")
            if not text:
                return {"status": "ok"}
            try:
                payload = response.json()
            except Exception as exc:  # noqa: BLE001
                raise ApiClientError("Invalid JSON response from Recite API.") from exc
            if isinstance(payload, dict) and payload.get("success") is False:
                raise ApiClientError(_extract_error_message_from_payload(payload))

            if (
                isinstance(payload, dict)
                and "data" in payload
                and payload.get("success") == True
            ):
                return payload["data"]

            if isinstance(payload, dict):
                return payload
            return {"data": payload}

        return {"content_type": content_type, "body": getattr(response, "text", "")}

    def _dispatch_request(self, **kwargs: Any) -> Any:
        request = getattr(self._session, "request", None)
        if callable(request):
            res = request(**kwargs)
            if res is not None:
                return res

        method_name = str(kwargs["method"]).lower()
        fallback = getattr(self._session, method_name, None)
        if callable(fallback):
            return fallback(
                kwargs["url"],
                **{k: v for k, v in kwargs.items() if k not in ("method", "url")},
            )
        raise ApiClientError("Configured session does not support HTTP requests.")


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _pick_first(
    payload: dict[str, Any], *keys: str, default: object | None = None
) -> object | None:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default


def _guess_image_type(path: Path) -> str | None:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed


def _quote_path(value: str) -> str:
    return quote(value, safe="")


def _bool_query_param(value: bool) -> str:
    return "true" if value else "false"


def _extract_error_message(response: Any) -> str:
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001
        text = str(getattr(response, "text", "")).strip()
        if text:
            return f"Recite API error ({response.status_code}): {text}"
        return f"Recite API error: {response.status_code}"

    if isinstance(payload, dict):
        return _extract_error_message_from_payload(payload)
    return f"Recite API error: {response.status_code}"


def _extract_error_message_from_payload(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or "Unknown API error")
    if error:
        return str(error)
    return "Unknown API error"
