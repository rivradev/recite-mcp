
# Recite MCP Server: Design & Implementation Plan

## 1. Executive Summary
The **Recite MCP Server** is a Local Model Context Protocol (MCP) server that empowers AI assistants (like Claude for Desktop, Cursor, and Zed) to natively interface with the Recite Vision API. 

It aims to replace the legacy `rivradev/recite-agent-skill` approach (which requires AI agents to construct and execute arbitrary bash scripts) with a secure, standard-compliant Python package. This upgrade resolves the security friction of arbitrary bash execution and seamlessly integrations with modern AI editors.

MCP server for https://recite.rivra.dev/docs/api
The skill is available in https://github.com/rivradev/recite-agent-skill
Website: https://recite.rivra.dev


## 2. Architecture & Design

### 2.1 Core Decisions
- **Type:** Local MCP Server (communicates over `stdio` on the user's machine).
- **Language:** Python 3.10+
- **Repository Strategy:** Provide a dedicated new GitHub repository (`rivradev/recite-mcp`).
- **Distribution:** Hosted on PyPI (`pip install recite-mcp`) and executed globally via `uvx` (e.g., `uvx recite-mcp`).

### 2.2 Why Local Python MCP?
A Local Python MCP server is the optimal choice because:
1. **Local File Permissions:** The value of the Recite Agent Skill comes from an agent reading local receipts, renaming local files, and appending to a local CSV ledger. A remote cloud MCP server lacks the permissions to touch the user's local filesystem.
2. **Distribution Friction:** Distributing via PyPI allows users to configure Claude Desktop/Cursor with a single frictionless line (`uvx recite-mcp`), automatically managing isolated virtual environments and dependencies.
3. **Logic Reusability:** Python allows us to directly port existing logic (`requests`, CSV handling, path manipulation) from the legacy `recite-agent-skill` repository.

## 3. MCP Components

The server will expose a focused set of Tools and Resources to the AI client.

### 3.1 Tools (Actions)
Tools represent the actionable functions the AI can invoke directly. Instead of prompting the AI to run bash, the AI receives rigid JSON schemas for these operations.

- `process_receipt(file_path: str) -> str`: The primary orchestration handler. Sends a local image or PDF to the Recite API, extracts the structured JSON (Vendor, Date, Total, Tax, etc.), and automatically logs it to the local CSV.
- `update_memory(instruction: str) -> str`: Allows the AI to save custom categorization or processing rules for future receipts.

### 3.2 Resources (Context)
Resources provide file-system or state context that the AI can read or subscribe to.

- `recite://ledger`: Continuously exposes the contents of `bookkeeping_transactions.CSV` so the AI can analyze past spending, identify duplicates, or generate reports.
- `recite://memory`: Exposes the local `long_term_memory.md` file, providing the AI with user-specific processing rules before processing a receipt.

## 4. Implementation Steps

### Phase 1: Repository & Scaffolding
1. Create a new GitHub repository: `rivradev/recite-mcp`.
2. Initialize a standard Python package using a modern build tool (e.g., `hatch` or `poetry`).
3. Define the `pyproject.toml` configuration, including the `mcp[cli]` official SDK and `requests`.

### Phase 2: Core Logic Porting
1. Port the existing API request logic from `process_receipts.py` into a modular package (e.g., `src/recite_mcp/api.py`).
2. Port the local file manipulation logic (CSV parsing, file renaming, handling the `~/.config/recite/` fallback) into `src/recite_mcp/ledger.py`.
3. Implement API Key resolution (using the `RECITE_API_KEY` environment variable as the primary source).

### Phase 3: MCP Server Construction
1. Create the entry point: `src/recite_mcp/server.py`.
2. Instantiate the `mcp.server.Server(name="recite-mcp")`.
3. Wrap the core logic functions with the `@server.tool()` decorators.
4. Implement the `stdio` server runner.

### Phase 4: Packaging and Distribution
1. Expose a CLI entry point in `pyproject.toml` (e.g., `recite-mcp = recite_mcp.server:main`).
2. Draft a user-focused `README.md` aimed entirely at MCP Integration (skipping the "Agent Skills" philosophy).
3. Publish version `0.1.0` to PyPI.

## 5. Client Integration Plan

Once published, adding Recite to an AI tool will look exactly like this snippet. This will be the focal point of your README documentation:

### Example: Claude Desktop Configuration (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "recite": {
      "command": "uvx",
      "args": ["recite-mcp"],
      "env": {
        "RECITE_API_KEY": "re_live_your_api_key_here"
      }
    }
  }
}
```
*Note: `uvx` dynamically downloads and caches Python CLI tools without requiring global dependency pollution.*
