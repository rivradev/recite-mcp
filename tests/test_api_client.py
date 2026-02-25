from __future__ import annotations

from pathlib import Path

import pytest

from recite_mcp.api_client import ApiClient, ApiClientError
from recite_mcp.config import Settings


class _Response:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _Session:
    def __init__(self, response: _Response | Exception) -> None:
        self._response = response
        self.last_url: str | None = None
        self.last_kwargs: dict | None = None

    def post(self, *_args, **_kwargs):  # noqa: ANN002, ANN003
        self.last_url = _args[0] if _args else None
        self.last_kwargs = _kwargs
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


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
