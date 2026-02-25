from __future__ import annotations

import asyncio

from recite_mcp.server import create_server


def test_create_server_registers_tools_and_resources(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "re_test")

    server = create_server()

    if hasattr(server, "tools") and hasattr(server, "resources"):
        assert "process_receipt" in server.tools
        assert "process_receipts_batch" in server.tools
        assert "recite://ledger" in server.resources
        assert "recite://health" in server.resources
        return

    tool_names = {tool.name for tool in asyncio.run(server.list_tools())}
    resource_uris = {str(resource.uri) for resource in asyncio.run(server.list_resources())}

    assert "process_receipt" in tool_names
    assert "process_receipts_batch" in tool_names
    assert "recite://ledger" in resource_uris
    assert "recite://health" in resource_uris
