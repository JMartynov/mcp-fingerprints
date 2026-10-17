# MCP Fingerprints & Passport Knowledge Base

[![Daily MCP Fingerprint & Passport Sync](https://github.com/JMartynov/mcp-fingerprints/actions/workflows/daily_sync.yml/badge.svg)](https://github.com/JMartynov/mcp-fingerprints/actions/workflows/daily_sync.yml)
[![Passports Count](https://img.shields.io/badge/passports-5058+-blue.svg)](data/fingerprints)
[![Tools Provided](https://img.shields.io/badge/with_tools-710-green.svg)](data/fingerprints)
[![Tombstoned Servers](https://img.shields.io/badge/tombstoned-150-inactive.svg)](data/fingerprints)
[![Test Suite](https://img.shields.io/badge/tests-252_passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Web Directory](https://img.shields.io/badge/Web_Directory-Live_Catalog-38bdf8?style=flat-square&logo=googlechrome)](https://jmartynov.github.io/mcp-fingerprints/)
[![What's New](https://img.shields.io/badge/What's_New-Latest_Sync_Updates-22c55e?style=flat-square&logo=git)](https://jmartynov.github.io/mcp-fingerprints/updates.html)

An open-source, automated database and knowledge base of **Model Context Protocol (MCP)** server passports, version signatures, and tool contract fingerprints.

## Ecosystem Architecture & Scope

`mcp-fingerprints` serves as the authoritative open standard for structural Model Context Protocol server passports. It focuses purely on:
* **Static AST Extraction**: Deep parameter schema, docstring, prompt, and resource extraction across Python, TypeScript/JavaScript, Go, and Rust.
* **Deterministic Cryptographic Hashing**: Order-invariant and whitespace-insensitive canonical hashing (`canonical_hash`, `toolset_canonical_hash`).
* **Supply-Chain Verification & Drift Tracking**: Detecting tool tampering, description changes, and schema mutations across package versions.
* **Open Catalog & Client Exporters**: Serving enriched structural web catalogs with interactive parameter schema inspectors and 1-click config generators.

## Key Features
- **5,058+ Indexed Passports**: Cross-indexed across Smithery, npm, PyPI, and GitHub registries.
- **Deep Parameter & Annotation Extraction**: Captures parameter types, descriptions, defaults, enums, required flags, and protocol annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).
- **Automated Daily Sync**: Continuously crawls, extracts tool signatures, canonicalizes hash fingerprints, and tracks historical schema drift.
- **Consolidated Snapshot**: Pre-compiled `passports.json.gz` for rapid HTTP consumption (< 50ms startup time).

## Quickstart: Search & Client Export

Search for available MCP servers:
```bash
python3 -m mcp_fingerprints.cli search "postgres"
```

Export an MCP server configuration for Claude Desktop:
```bash
python3 -m mcp_fingerprints.cli export-config @modelcontextprotocol/server-postgres --client claude
```

Export an MCP server configuration for Cursor:
```bash
python3 -m mcp_fingerprints.cli export-config @modelcontextprotocol/server-postgres --client cursor
```

## Enriched Tool Parameter Schemas & Protocol Annotations

MCP Fingerprints extracts rich parameter schemas and runtime protocol hints directly from server source ASTs:
* **Structured Parameter Metadata**: Includes parameter types (`string`, `number`, `boolean`, `array`, `object`), descriptions, required status, default values, and allowed enums.
* **Protocol Annotations**: Captures MCP tool behavior hints:
  - `readOnlyHint`: Tool performs read-only operations without side effects.
  - `destructiveHint`: Tool performs destructive operations (deletions, modifications).
  - `idempotentHint`: Repeated invocations yield identical state.
  - `openWorldHint`: Tool interacts with external/unconstrained network services.
* **Transport Specifications**: Captures supported transports (`stdio`, `sse`, `streamable-http`, `websocket`) and required environment variables.

## Fast Consumption

You can fetch the latest consolidated database in a single GET request:
```bash
curl -sL https://raw.githubusercontent.com/JMartynov/mcp-fingerprints/main/passports.json.gz | gzip -d > passports.json
```

### Python
```python
import gzip, json, urllib.request

url = "https://raw.githubusercontent.com/JMartynov/mcp-fingerprints/main/passports.json.gz"
with urllib.request.urlopen(url) as resp:
    with gzip.GzipFile(fileobj=resp) as gz:
        data = json.load(gz)

print(f"Loaded {data['total_passports']} MCP server passports.")
```

## CLI Usage

The CLI provides a focused set of pure structural commands:

```bash
# Sync from registries
python -m mcp_fingerprints.cli sync --all

# Match a toolset hash against the knowledge base
python -m mcp_fingerprints.cli match <hash>

# Probe a server and extract its fingerprint
python -m mcp_fingerprints.cli probe <server_command>

# Validate schema invariants
python -m mcp_fingerprints.cli validate --dir data/fingerprints

# Build compressed snapshot
python -m mcp_fingerprints.cli snapshot

# Search the catalog
python -m mcp_fingerprints.cli search "query"

# Browse interactively via TUI
python -m mcp_fingerprints.cli browse

# Export client configurations (Claude, Cursor, Cline, Zed, Windsurf)
python -m mcp_fingerprints.cli export-config <server_name> --client claude

# Detect configuration drift against the latest passports
python -m mcp_fingerprints.cli detect-drift <config_file>
```

## Releases

### TestPyPI Dry-Run

You can perform an automated dry-run release to TestPyPI to verify packaging, metadata, and functionality before a production PyPI release.
1. Navigate to the **Actions** tab in the GitHub repository.
2. Select the **Release to TestPyPI (Dry-Run)** workflow.
3. Click **Run workflow**.
4. You can optionally provide a `version_suffix` (e.g. `rc1`, `b2`) which will be appended to the current version in `pyproject.toml` to avoid conflicts on TestPyPI.
5. The workflow will build artifacts, publish them to TestPyPI using Trusted Publishing, and execute an automated smoke test (`pip install` into a clean container).

## License
MIT
