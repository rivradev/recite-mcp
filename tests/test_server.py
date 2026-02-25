from __future__ import annotations

from recite_mcp.server import create_server


def test_create_server_registers_tools_and_resources(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "re_test")

    server = create_server()

    assert "process_receipt" in server.tools
    assert "process_receipts_batch" in server.tools
    assert "recite://ledger" in server.resources
    assert "recite://health" in server.resources
