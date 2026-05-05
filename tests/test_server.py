from __future__ import annotations

import asyncio

from recite_mcp.server import create_server


def test_create_server_registers_tools_and_resources(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "re_test")

    server = create_server()

    if hasattr(server, "list_tools") and hasattr(server, "list_resources"):
        tool_names = {tool.name for tool in asyncio.run(server.list_tools())}
        resource_uris = {
            str(resource.uri) for resource in asyncio.run(server.list_resources())
        }
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
    assert "upload_bank_statement" in tool_names
    assert "list_bank_statements" in tool_names
    assert "get_bank_statement" in tool_names
    assert "delete_bank_statement" in tool_names
    assert "export_bank_statement" in tool_names
    assert "list_bank_transactions" in tool_names
    assert "get_bank_transaction" in tool_names
    assert "update_bank_transaction" in tool_names
    assert "delete_bank_transaction" in tool_names
    assert "create_reconciliation_link" in tool_names
    assert "list_reconciliation_links" in tool_names
    assert "update_reconciliation_link" in tool_names
    assert "delete_reconciliation_link" in tool_names
    assert "run_auto_match" in tool_names
    assert "get_reconciliation_summary" in tool_names
    assert "get_reconciliation_recommendations" in tool_names
    assert "export_reconciliation" in tool_names
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


import sys


def test_server_tools_registered(tmp_path, monkeypatch):
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "test_key")

    server = create_server()
    assert server is not None


def test_main_version(capsys, monkeypatch):
    import importlib.metadata

    def mock_version(*args, **kwargs):
        return "1.2.3"

    monkeypatch.setattr(importlib.metadata, "version", mock_version)

    from recite_mcp.server import main

    main(["--version"])
    out, err = capsys.readouterr()
    assert "1.2.3" in out


def test_main_version_unknown(capsys, monkeypatch):
    import importlib.metadata

    def mock_version(*args, **kwargs):
        raise importlib.metadata.PackageNotFoundError()

    monkeypatch.setattr(importlib.metadata, "version", mock_version)

    from recite_mcp.server import main

    main(["--version"])
    out, err = capsys.readouterr()
    assert "unknown" in out


def test_main_validate(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "test_key")

    from recite_mcp.server import main
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--validate"])

    assert exc.value.code == 0
    out, err = capsys.readouterr()
    assert "test_key" not in out
    assert '"has_api_key": true' in out


def test_main_validate_no_key(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.delenv("RECITE_API_KEY", raising=False)

    from recite_mcp.server import main
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--validate"])

    assert exc.value.code == 1
    out, err = capsys.readouterr()
    assert '"has_api_key": false' in out


def test_main_fallback_mode(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "test_key")

    import recite_mcp.server as mod

    monkeypatch.setattr(mod, "FastMCP", None)

    mod.main([])

    out, err = capsys.readouterr()
    assert "recite-mcp initialized (fallback mode)" in out


def _get_server_and_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("RECITE_HOME", str(tmp_path))
    monkeypatch.setenv("RECITE_API_KEY", "test_key")
    import recite_mcp.server as mod

    monkeypatch.setattr(mod, "FastMCP", None)
    server = mod.create_server()
    return server, server.tools


def test_server_process_receipt(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "process_receipt", mock)
    tools["process_receipt"]("file.jpg", rename=False, dry_run=False)
    assert called


def test_server_process_receipts_batch(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "process_receipts_batch", mock)
    tools["process_receipts_batch"]("dir", dry_run=True, recursive=False)
    assert called


def test_server_get_scan(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_scan", mock)
    tools["get_scan"]("123")
    assert called


def test_server_scan_receipt(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "scan_receipt", mock)
    tools["scan_receipt"](file_path="123")
    assert called


def test_server_create_transaction(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "create_transaction", mock)
    tools["create_transaction"]({})
    assert called


def test_server_list_transactions(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "list_transactions", mock)
    tools["list_transactions"]()
    assert called


def test_server_update_transaction(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "update_transaction", mock)
    tools["update_transaction"]("123", {})
    assert called


def test_server_delete_transaction(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_transaction", mock)
    tools["delete_transaction"]("123")
    assert called


def test_server_import_transactions(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "import_transactions", mock)
    tools["import_transactions"]()
    assert called


def test_server_submit_batch_scans(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "submit_batch_scans", mock)
    tools["submit_batch_scans"]([{}])
    assert called


def test_server_get_batch_scan_status(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_batch_scan_status", mock)
    tools["get_batch_scan_status"]("123")
    assert called


def test_server_get_batch_scan_results(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_batch_scan_results", mock)
    tools["get_batch_scan_results"]("123")
    assert called


def test_server_list_projects(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "list_projects", mock)
    tools["list_projects"]()
    assert called


def test_server_create_project(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "create_project", mock)
    tools["create_project"]("name")
    assert called


def test_server_update_project(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "update_project", mock)
    tools["update_project"]("123")
    assert called


def test_server_delete_project(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_project", mock)
    tools["delete_project"]("123")
    assert called


def test_server_get_summary(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_summary", mock)
    tools["get_summary"]()
    assert called


def test_server_create_webhook(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "create_webhook", mock)
    tools["create_webhook"]("url", ["event"])
    assert called


def test_server_list_webhooks(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "list_webhooks", mock)
    tools["list_webhooks"]()
    assert called


def test_server_delete_webhook(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_webhook", mock)
    tools["delete_webhook"]("123")
    assert called


def test_server_create_rule(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "create_rule", mock)
    tools["create_rule"]("type", {}, {})
    assert called


def test_server_list_rules(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "list_rules", mock)
    tools["list_rules"]()
    assert called


def test_server_delete_rule(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_rule", mock)
    tools["delete_rule"]("123")
    assert called


def test_server_update_rule(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "update_rule", mock)
    tools["update_rule"]("123", {})
    assert called


def test_server_get_categories(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_categories", mock)
    tools["get_categories"]()
    assert called


def test_server_create_category(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "create_category", mock)
    tools["create_category"]("name")
    assert called


def test_server_delete_category(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_category", mock)
    tools["delete_category"]("name")
    assert called


def test_server_get_vendors(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_vendors", mock)
    tools["get_vendors"]()
    assert called


def test_server_create_vendor(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "create_vendor", mock)
    tools["create_vendor"]("name")
    assert called


def test_server_delete_vendor(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_vendor", mock)
    tools["delete_vendor"]("name")
    assert called


def test_server_get_usage(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_usage", mock)
    tools["get_usage"]()
    assert called


def test_server_export_transactions(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "export_transactions", mock)
    tools["export_transactions"]("csv")
    assert called


def test_server_update_memory(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "update_memory", mock)
    tools["update_memory"]("instruction")
    assert called


def test_server_list_memory(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(mod.ReciteTools, "list_memory", mock)
    tools["list_memory"]()
    assert called


def test_server_add_ledger_correction(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "add_ledger_correction", mock)
    tools["add_ledger_correction"]("123", {}, "reason")
    assert called


def test_server_summarize_ledger(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "summarize_ledger", mock)
    tools["summarize_ledger"]()
    assert called


def test_server_export_ledger(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "export_ledger", mock)
    tools["export_ledger"]("csv", "path")
    assert called


def test_server_get_config(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    config = tools["get_config"]()
    assert "recite_home" in config


def test_server_validate_setup(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.resources as res

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(res.ResourceProvider, "get_health", mock)
    tools["validate_setup"]()
    assert called


def test_server_resources(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.resources as res

    called_ledger = False

    def mock_ledger(*args, **kwargs):
        nonlocal called_ledger
        called_ledger = True
        return []

    monkeypatch.setattr(res.ResourceProvider, "get_ledger_rows", mock_ledger)
    server.resources["recite://ledger"]()
    assert called_ledger

    called_memory = False

    def mock_memory(*args, **kwargs):
        nonlocal called_memory
        called_memory = True
        return ""

    monkeypatch.setattr(res.ResourceProvider, "get_memory_text", mock_memory)
    server.resources["recite://memory"]()
    assert called_memory

    called_health = False

    def mock_health(*args, **kwargs):
        nonlocal called_health
        called_health = True
        return {}

    monkeypatch.setattr(res.ResourceProvider, "get_health", mock_health)
    server.resources["recite://health"]()
    assert called_health


def test_server_upload_bank_statement(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "upload_bank_statement", mock)
    tools["upload_bank_statement"](csv_text="date,amount")
    assert called


def test_server_list_bank_statements(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "list_bank_statements", mock)
    tools["list_bank_statements"]()
    assert called


def test_server_get_bank_statement(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_bank_statement", mock)
    tools["get_bank_statement"]("stmt_1")
    assert called


def test_server_delete_bank_statement(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_bank_statement", mock)
    tools["delete_bank_statement"]("stmt_1")
    assert called


def test_server_export_bank_statement(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "export_bank_statement", mock)
    tools["export_bank_statement"]("stmt_1", format="csv")
    assert called


def test_server_list_bank_transactions(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "list_bank_transactions", mock)
    tools["list_bank_transactions"]()
    assert called


def test_server_get_bank_transaction(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_bank_transaction", mock)
    tools["get_bank_transaction"]("btxn_1")
    assert called


def test_server_update_bank_transaction(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "update_bank_transaction", mock)
    tools["update_bank_transaction"]("btxn_1", {})
    assert called


def test_server_delete_bank_transaction(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_bank_transaction", mock)
    tools["delete_bank_transaction"]("btxn_1")
    assert called


def test_server_create_reconciliation_link(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "create_reconciliation_link", mock)
    tools["create_reconciliation_link"](
        transaction_id="txn_1", bank_transaction_id="btxn_1"
    )
    assert called


def test_server_list_reconciliation_links(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "list_reconciliation_links", mock)
    tools["list_reconciliation_links"]()
    assert called


def test_server_update_reconciliation_link(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "update_reconciliation_link", mock)
    tools["update_reconciliation_link"]("link_1", {})
    assert called


def test_server_delete_reconciliation_link(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "delete_reconciliation_link", mock)
    tools["delete_reconciliation_link"]("link_1")
    assert called


def test_server_run_auto_match(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "run_auto_match", mock)
    tools["run_auto_match"]()
    assert called


def test_server_get_reconciliation_summary(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_reconciliation_summary", mock)
    tools["get_reconciliation_summary"]()
    assert called


def test_server_export_reconciliation(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "export_reconciliation", mock)
    tools["export_reconciliation"]()
    assert called

def test_server_get_reconciliation_recommendations(tmp_path, monkeypatch):
    server, tools = _get_server_and_tools(tmp_path, monkeypatch)
    import recite_mcp.tools as mod

    called = False

    def mock(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mod.ReciteTools, "get_reconciliation_recommendations", mock)
    tools["get_reconciliation_recommendations"](bank_transaction_id="btx_123")
    assert called
