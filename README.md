# MCP Fingerprints & Passport Knowledge Base

[![Daily MCP Fingerprint & Passport Sync](https://github.com/JMartynov/mcp-fingerprints/actions/workflows/daily_sync.yml/badge.svg)](https://github.com/JMartynov/mcp-fingerprints/actions/workflows/daily_sync.yml)
[![Passports Count](https://img.shields.io/badge/passports-5049-blue.svg)](data/fingerprints)
[![Tools Provided](https://img.shields.io/badge/with_tools-710-green.svg)](data/fingerprints)
[![Tombstoned Servers](https://img.shields.io/badge/tombstoned-150-inactive.svg)](data/fingerprints)
[![Test Suite](https://img.shields.io/badge/tests-144_passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Web Directory](https://img.shields.io/badge/Web_Directory-Live_Catalog-38bdf8?style=flat-square&logo=googlechrome)](https://jmartynov.github.io/mcp-fingerprints/)

An open-source, automated database and knowledge base of **Model Context Protocol (MCP)** server passports, version signatures, and tool contract fingerprints.

## Key Features
- **3,900+ Indexed Passports**: Cross-indexed across Smithery, npm, and PyPI registries.
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

## Security Auditing & Risk Scoring

MCP Fingerprints assigns risk scores based on tool definitions and parameter signatures to help identify potentially dangerous capabilities:
* **Critical**: Tools allowing arbitrary system command execution, unchecked filesystem writes, or broad remote code execution.
* **High**: Tools with broad database access (e.g., arbitrary SQL execution), potential server-side request forgery (SSRF) parameters, or sensitive environment variable manipulation.
* **Medium**: Tools with limited file reads/writes, scoped data extraction, or network requests to constrained domains.
* **Low**: Read-only operations, safe calculations, or well-constrained API integrations.

We employ robust parameter injection defenses and sandbox methodologies to ensure runtime safety during server auditing. For a full breakdown, read our [Security Audit Documentation](docs/SECURITY_AUDIT.md).

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

## CI Integration (GitHub Action)

You can use the MCP Fingerprints GitHub Action to automatically audit your client configurations (Claude Desktop, Cursor, Cline, Zed) in your CI pipeline to catch tool collisions and security shadowing before they reach production:

```yaml
name: Audit MCP Configuration

on:
  push:
    paths:
      - 'claude_desktop_config.json'

jobs:
  audit-mcp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Audit MCP Client Config
        uses: JMartynov/mcp-fingerprints@v1
        with:
          config-file: 'claude_desktop_config.json'
          fail-on-critical: 'true'
```

## Pre-Commit Integration

To prevent committing conflicting or shadowed MCP configurations locally, add `mcp-audit-config` to your repository's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/JMartynov/mcp-fingerprints
    rev: v1.0.0
    hooks:
      - id: mcp-audit-config
```

To run pre-commit locally across all files:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## CLI Usage
```bash
# Sync from registries
python -m mcp_fingerprints.cli sync --all

# Validate schema invariants
python -m mcp_fingerprints.cli validate --dir data/fingerprints

# Build compressed snapshot
python -m mcp_fingerprints.cli snapshot
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
