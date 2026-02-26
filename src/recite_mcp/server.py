from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

from recite_mcp.config import load_settings
from recite_mcp.resources import ResourceProvider
from recite_mcp.tools import ReciteTools

try:  # pragma: no cover - exercised only when mcp is installed in runtime.
    from mcp.server.fastmcp import FastMCP
except Exception:  # noqa: BLE001
    FastMCP = None  # type: ignore[assignment]


class _SimpleServer:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}
        self.resources: dict[str, Callable[[], Any]] = {}

    def tool(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def _wrap(func: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[name] = func
            return func

        return _wrap

    def resource(self, name: str) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
        def _wrap(func: Callable[[], Any]) -> Callable[[], Any]:
            self.resources[name] = func
            return func

        return _wrap


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def _build_handlers(server: Any, tools: ReciteTools, resources: ResourceProvider, settings: Any) -> Any:
    @server.tool("process_receipt")
    def process_receipt(file_path: str, rename: bool = False, category_hint: str | None = None, dry_run: bool = False) -> dict:
        return _serialize(tools.process_receipt(file_path=file_path, rename=rename, category_hint=category_hint, dry_run=dry_run))

    @server.tool("process_receipts_batch")
    def process_receipts_batch(input_dir: str, rename: bool = False, dry_run: bool = True, recursive: bool = True) -> dict:
        return _serialize(tools.process_receipts_batch(input_dir=input_dir, rename=rename, dry_run=dry_run, recursive=recursive))

    @server.tool("update_memory")
    def update_memory(instruction: str, tags: list[str] | None = None) -> dict:
        return tools.update_memory(instruction=instruction, tags=tags)

    @server.tool("list_memory")
    def list_memory() -> list[dict]:
        return tools.list_memory()

    @server.tool("add_ledger_correction")
    def add_ledger_correction(original_entry_id: str, corrected_fields: dict, reason: str) -> dict:
        return tools.add_ledger_correction(original_entry_id=original_entry_id, corrected_fields=corrected_fields, reason=reason)

    @server.tool("summarize_ledger")
    def summarize_ledger(group_by: str = "vendor") -> dict:
        return tools.summarize_ledger(group_by=group_by)

    @server.tool("export_ledger")
    def export_ledger(format: str, output_path: str) -> dict:
        return tools.export_ledger(format=format, output_path=output_path)

    @server.tool("get_config")
    def get_config() -> dict:
        return {
            "recite_home": str(settings.recite_home),
            "api_base_url": settings.api_base_url,
            "request_timeout_sec": settings.request_timeout_sec,
            "has_api_key": bool(settings.api_key),
        }

    @server.tool("validate_setup")
    def validate_setup() -> dict:
        return resources.get_health()

    @server.resource("recite://ledger")
    def recite_ledger() -> list[dict]:
        return resources.get_ledger_rows()

    @server.resource("recite://memory")
    def recite_memory() -> str:
        return resources.get_memory_text()

    @server.resource("recite://health")
    def recite_health() -> dict:
        return resources.get_health()

    return server


def create_server() -> Any:
    # Don't fail hard at process start if RECITE_API_KEY is missing.
    # MCP clients should still be able to connect and call validate_setup/get_config.
    settings = load_settings(require_api_key=False)
    tools = ReciteTools.from_settings(settings)
    resources = ResourceProvider(settings)
    server = FastMCP("recite-mcp") if FastMCP is not None else _SimpleServer()
    return _build_handlers(server, tools, resources, settings)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recite-mcp", add_help=True)
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Print local health/config JSON and exit (does not call the Recite API).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Transport to use when running as an MCP server (default: stdio).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    if args.version:
        try:
            version = importlib.metadata.version("recite-mcp")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
        print(version)
        return

    if args.validate:
        settings = load_settings(require_api_key=False)
        health = ResourceProvider(settings).get_health()
        payload = {
            "config": {
                "recite_home": str(settings.recite_home),
                "api_base_url": settings.api_base_url,
                "request_timeout_sec": settings.request_timeout_sec,
                "has_api_key": bool(settings.api_key),
            },
            "health": health,
        }
        print(json.dumps(payload, indent=2))
        sys.exit(0 if settings.api_key else 1)

    server = create_server()
    if FastMCP is not None and hasattr(server, "run"):
        server.run(transport=args.transport)
        return
    # Fallback mode is primarily for local dev when mcp isn't installed.
    print("recite-mcp initialized (fallback mode)")
    print(f"tools={','.join(sorted(server.tools.keys()))}")
    print(f"resources={','.join(sorted(server.resources.keys()))}")


if __name__ == "__main__":
    main()
