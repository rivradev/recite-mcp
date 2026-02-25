# recite-mcp Publishing and Adoption Guide

This guide covers what to do after the first PyPI upload so people can find, install, and use `recite-mcp` quickly.

## 1. Post-Publish Tasks on PyPI

Complete these in your PyPI project page after release.

1. Verify project page content:
- Summary/description is clear and user-focused.
- `README.md` renders correctly on PyPI.

2. Add better package metadata in `pyproject.toml` (for future releases):
- `keywords` (already added): `mcp`, `mcp-server`, `receipts`, `bookkeeping`, `recite`
- `classifiers` (already added): Python versions, audience, topic.
- Add `[project.urls]` with real links (Homepage, Repository, Issues).

3. Release hygiene:
- Keep a changelog per version.
- Use semantic versions (`0.1.1`, `0.2.0`, `1.0.0`).
- Never delete published versions; publish fixes as new versions.

4. Token hygiene (already started):
- Keep only project-scoped API token for `recite-mcp`.
- Remove old account-scoped tokens.

## 2. Make the MCP Easy to Discover

Discovery comes from metadata + docs + ecosystem listings.

1. GitHub repository setup:
- Repo name and README title match: `recite-mcp`.
- Add repository topics: `mcp`, `mcp-server`, `python`, `receipts`, `bookkeeping`.
- Add short repository description aligned with PyPI summary.

2. README optimization:
- Put install command in first screen.
- Include one minimal MCP config example.
- Add "What this MCP does" with concrete tool names.

3. PyPI optimization:
- Keep package name stable and recognizable.
- Ensure metadata keywords/classifiers are present in each release.

4. Directory/listing submissions:
- Submit to MCP community directories/catalogs you use.
- Post an announcement with install snippet and supported clients.

## 3. End-User Installation Paths

### Recommended (no global Python pollution)

```bash
uvx recite-mcp
```

### Alternative

```bash
pipx install recite-mcp
```

### Standard pip

```bash
python -m pip install recite-mcp
```

## 4. End-User MCP Client Configuration

Use this base config and adapt to the client's config file location.

```json
{
  "mcpServers": {
    "recite": {
      "command": "uvx",
      "args": ["recite-mcp"],
      "env": {
        "RECITE_API_KEY": "re_live_xxx"
      }
    }
  }
}
```

If users do not have `uvx`, they can use installed entrypoint:

```json
{
  "mcpServers": {
    "recite": {
      "command": "recite-mcp",
      "args": [],
      "env": {
        "RECITE_API_KEY": "re_live_xxx"
      }
    }
  }
}
```

## 5. First-Run Validation for Users

Ask users to validate quickly:

1. Confirm command launches:
- `uvx recite-mcp`

2. Confirm API key is present:
- `RECITE_API_KEY` set in MCP client env.

3. Confirm server responds:
- Run the MCP client and call `validate_setup`.

## 6. Release Checklist Template

Copy this into each release PR/issue.

- [ ] Version bumped in `pyproject.toml`
- [ ] `python -m build` completed
- [ ] `python -m twine check dist/*` passed
- [ ] Uploaded to PyPI
- [ ] Fresh install test passed (`uvx recite-mcp`)
- [ ] README examples validated
- [ ] Changelog/release notes published
- [ ] Project-scoped token confirmed

## 7. Suggested README Section for End Users

You can copy this section directly into your public docs.

````md
## Install recite-mcp

```bash
uvx recite-mcp
```

Set your API key in MCP client config:

```json
{
  "mcpServers": {
    "recite": {
      "command": "uvx",
      "args": ["recite-mcp"],
      "env": {
        "RECITE_API_KEY": "re_live_xxx"
      }
    }
  }
}
```
````

## 8. What to Improve in the Next Release

1. Add `[project.urls]` with your real GitHub links.
2. Add a `CHANGELOG.md` and link it from README.
3. Add a GitHub Action for release builds and optional Trusted Publishing.
4. Add a short troubleshooting section:
- Missing API key
- `uvx` not found
- Permission issues on local output paths
