from __future__ import annotations

import asyncio

from recite_mcp.server import create_server


def test_create_server_registers_tools_and_resources(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "re_test")

    server = create_server()

    if hasattr(server, "list_tools") and hasattr(server, "list_resources"):
        tool_names = {tool.name for tool in asyncio.run(server.list_tools())}
        resource_uris = {str(resource.uri) for resource in asyncio.run(server.list_resources())}
    else:
        tool_names = set(server.tools.keys())
        resource_uris = set(server.resources.keys())

    assert "process_receipt" in tool_names
    assert "process_receipts_batch" in tool_names
    assert "scan_receipt" in tool_names
    assert "get_scan" in tool_names
    assert "create_transaction" in tool_names
    assert "list_transactions" in tool_names
    assert "update_transaction" in tool_names
    assert "delete_transaction" in tool_names
    assert "import_transactions" in tool_names
    assert "submit_batch_scans" in tool_names
    assert "get_batch_scan_status" in tool_names
    assert "get_batch_scan_results" in tool_names
    assert "list_projects" in tool_names
    assert "create_project" in tool_names
    assert "update_project" in tool_names
    assert "delete_project" in tool_names
    assert "get_summary" in tool_names
    assert "create_webhook" in tool_names
    assert "list_webhooks" in tool_names
    assert "delete_webhook" in tool_names
    assert "create_rule" in tool_names
    assert "list_rules" in tool_names
    assert "delete_rule" in tool_names
    assert "get_usage" in tool_names
    assert "export_transactions" in tool_names
    assert "recite://ledger" in resource_uris
    assert "recite://health" in resource_uris


def test_create_server_does_not_require_api_key(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.delenv("RECITE_API_KEY", raising=False)

    server = create_server()

    if hasattr(server, "list_tools"):
        tool_names = {tool.name for tool in asyncio.run(server.list_tools())}
    else:
        tool_names = set(server.tools.keys())

    assert "validate_setup" in tool_names
