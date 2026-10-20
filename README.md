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
- **5,446+ Indexed Passports**: Cross-indexed across npm, PyPI, Crates.io, Maven Central, Docker Hub, and GitHub polyglot registries.
- **Empirical Ecosystem Research Audit**: Comprehensive empirical audit of 1,000 real MCP servers across 5 representative groups (Rust, Go, JVM/.NET, Regional/International, Monorepos/Containers) cataloging systemic blind spots and remedies ([`docs/research/master_mcp_ecosystem_audit_report.md`](docs/research/master_mcp_ecosystem_audit_report.md)).
- **Full Polyglot & Macro Ingestion Engines**: First-class support for Rust `rmcp` macros (`#[tool(...)] async fn`), Go `mark3labs/mcp-go` builder patterns, Spring AI `@Tool`, C# .NET `[McpServerTool]`, standalone PEP 723 `uvx` scripts, and CJK multilingual Unicode preservation.
- **Interactive Command Hub (`mcp-fingerprints interactive`)**: Emoji-decorated ergonomic TUI for workstation scanning, ready database search, unknown MCP auto-addition, and 1-click baseline diffing.
- **Cross-Platform Multi-Agent Discovery**: Out-of-the-box discovery and inventory across 14+ AI coding agents (Claude Code, Desktop, Cursor, Windsurf, Zed, Cline, Roo, Goose, Continue, Junie, Copilot, Antigravity, OpenHands) across macOS, Linux, and Windows.
- **Generic MCP Protocol Detection (`mcp-fingerprints detect`)**: Active JSON-RPC 2.0 handshake (`stdio` and `http`/`sse`) testing whether any arbitrary process or URL implements the MCP protocol.
- **High-Performance Multi-Core Parallel Batching & Two-Tier SHA Cache**: `ProcessPoolExecutor` with two-tier `(mtime, size) -> SHA-256` caching cutting warm validation and snapshot compilation from ~30s to <1s.
- **Resilient Time-Budgeted Stage Checkpoint Engine**: Graceful checkpointing and resumption in `data/.sync_checkpoint.json` with clean exit code 0 when execution time budgets or CI timeouts are approached.
- **Zero-Pull Container & Polyglot Discovery**: Headless Docker Hub / OCI Registry V2 and GitHub Rust/Go inspection without pulling gigabytes of images or cloning git trees.
- **Deep Parameter & Annotation Extraction**: Captures parameter types, descriptions, defaults, enums, required flags, and protocol annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).
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

## 🧭 Interactive Command Hub (`mcp-fingerprints interactive`)

For developer convenience, `mcp-fingerprints` includes an interactive TUI command hub decorated with visual anchor emojis, dynamic workstation status, and instant search:

```bash
# Launch the interactive hub (or simply run without args in an interactive TTY)
mcp-fingerprints interactive
```

```text
============================================================
      Interactive MCP Command Hub
============================================================
 OS: macOS
 Paths Scanned: 4 (Claude Code, Cursor, Claude Desktop, Gemini)
 Total MCP Servers Configured: 11
 Baseline Status: Saved (workstation_baseline.json)
============================================================

1. 🖥️ Workstation Discovery & Inventory
   • 🔍 Scan All Local AI Agents
   • 🎯 Scan Specific Agent...
   • 💾 Save Current State as Baseline JSON
   • ⚖️ Diff Against Previous Baseline
2. 🌐 Ready Database & Unknown Local MCPs
   • 🔤 Search Ready Database by Keyword
   • 📥 Add Unknown MCP from Local Machine
   • 📚 Browse Catalog Passports
3. 🧪 Live Prober & Generic MCP Detector
   • 🔬 Detect if Command/URL is an MCP Server
   • 🩺 Deep Live Server Probe
   • 🏷️ Auto-Generate & Save Passport
4. ⚙️ Performance, Cache & System
   • ⚡ View Cache & Benchmark Stats
   • 🧹 Clear Validation / Passport Cache
   • ⏱️ Inspect Active Checkpoints & Time Budgets
5. 🚪 Exit
```

---

## 💼 Real-World Scenarios & Use Cases

### Scenario 1: Interactive Terminal Audit & Workstation Management
* **Use Case Description**: Developers using multiple AI coding assistants want an effortless, terminal-native way to inspect what tools are available, search tool definitions, and detect newly installed MCP servers without remembering flags.
* **How It Works**: Running `mcp-fingerprints interactive` presents an intuitive, categorized menu. Selecting `🔍 Scan All Local AI Agents` audits Claude Code, Claude Desktop, Cursor, and Windsurf, displays active tools, and offers 1-click baseline diffing.

### Scenario 2: Multi-Agent Shadow MCP Discovery
* **Use Case Description**: AI developers frequently test MCP servers in one client (like Claude Code `~/.claude.json`) and forget they are active, or need an inventory across diverse team configurations.
* **How It Works**: `mcp-fingerprints scan-configs` automatically resolves configuration paths across 14+ clients across macOS, Linux, and Windows:
```bash
# Scan all installed clients without live probing
mcp-fingerprints scan-configs --no-probe-live

# Target a specific client
mcp-fingerprints scan-configs --client claude

# Export full machine inventory as a structured JSON file
mcp-fingerprints scan-configs --output workstation_inventory.json
```
**Supported Clients Out-of-the-Box:**
- **Claude Desktop** (`claude_desktop_config.json`)
- **Claude Code CLI** (`~/.claude.json` root & per-project entries, `.mcp.json`)
- **Cursor** (`~/.cursor/mcp.json`, `<project>/.cursor/mcp.json`)
- **Windsurf** (`~/.codeium/windsurf/mcp_config.json`)
- **Zed** (`~/.config/zed/settings.json`, `context_servers` format)
- **Cline & Roo Code** (`cline_mcp_settings.json`, `.roo/mcp.json`)
- **Goose** (`~/.config/goose/config.yaml`, YAML `extensions` format)
- **Continue.dev** (`~/.continue/config.yaml`, YAML list format)
- **JetBrains Junie & AI Assistant** (`~/.junie/mcp/mcp.json`)
- **VS Code / GitHub Copilot** (`.vscode/mcp.json`, `servers` format)
- **Antigravity / Gemini CLI** (`~/.gemini/config/mcp_config.json`)
- **OpenHands & Trae** (`mcp.json`)

### Scenario 3: Auto-Passport Generation for Unknown Local Servers (e.g. CodeScene)
* **Use Case Description**: An organization uses a proprietary, closed-source, or containerized MCP server (such as `codescene/codescene-mcp` or an internal Docker tool) that is not indexed in public registries.
* **How It Works**: Use `--auto-passport` during a workstation scan to probe the server's tools over stdio/HTTP, construct a valid `ServerPackageSpec` passport, and save it directly into `data/fingerprints/<server_name>.json`:
```bash
# Automatically extract and generate passports for any unknown local servers
mcp-fingerprints scan-configs --auto-passport
```
The newly created passport immediately participates in validation, canonical hashing, and snapshot compilations.

### Scenario 4: Generic MCP Protocol Detection (`mcp-fingerprints detect`)
* **Use Case Description**: A developer wants to verify whether a third-party binary, Docker container command, or local HTTP server actually speaks the Model Context Protocol before hooking it up to an AI agent.
* **How It Works**: The `detect` command runs an active JSON-RPC 2.0 `initialize` handshake with a fast 3-second timeout:
```bash
# Test an arbitrary command line (stdio)
mcp-fingerprints detect "docker run -i --rm -e CS_ACCESS_TOKEN=$TOKEN codescene/codescene-mcp"

# Test a local or remote HTTP/SSE streaming endpoint
mcp-fingerprints detect http://127.0.0.1:64342/stream
```
**Sample Output:**
```text
Target:    docker run -i --rm codescene/codescene-mcp
Is MCP:    Yes (verified)
Transport: stdio
Server:    codescene-mcp v1.2.0
Protocol:  2024-11-05
Tools:     5 capabilities advertised
```

### Scenario 5: Stateful Workstation Drift Tracking & Baseline Diffs
* **Use Case Description**: Prevent supply-chain poisoning and unauthorized configuration tampering in development environments or CI pre-commit checks.
* **How It Works**: Establish a signed baseline of workstation MCP tools and compare on subsequent runs:
```bash
# 1. Capture baseline snapshot
mcp-fingerprints scan-configs --save-baseline workstation_baseline.json

# 2. Check for drift (exits with code 2 if changes or tool schema mutations exist)
mcp-fingerprints scan-configs --diff workstation_baseline.json --fail-on-drift
```

### Scenario 6: High-Performance Multi-Core Batching & Two-Tier SHA Cache
* **Use Case Description**: Large monorepos and CI/CD pipelines need to validate 5,000+ passport files and compile snapshots in milliseconds without CPU bottlenecks.
* **How It Works**: `mcp-fingerprints validate` and `snapshot` employ `concurrent.futures.ProcessPoolExecutor` (bypassing the Python GIL) and a two-tier `(mtime, size) -> SHA-256` cache in `data/.passport_cache.json`:
```bash
# Multicore validation across all available CPU cores
mcp-fingerprints validate --workers 8

# Force re-validation bypassing cache
mcp-fingerprints validate --no-cache --force
```
*Warm validation runs drop from ~30 seconds to < 0.5 seconds (98.3% speedup).*

### Scenario 7: Time-Budgeted Resilient Sync & Stage Checkpointing
* **Use Case Description**: CI runners (like GitHub Actions) and cloud sandboxes (like Google Jules) enforce hard timeout ceilings (e.g. 40 minutes). Ingestion jobs must not crash upon reaching time limits.
* **How It Works**: `mcp-fingerprints sync` measures monotonic time and monitors `SIGTERM`/`SIGINT`. If the time budget is approached, it flushes state, saves a checkpoint in `data/.sync_checkpoint.json`, and exits with code 0 (`SUCCESS`):
```bash
# Run multi-source synchronization bounded to a 30-minute budget
mcp-fingerprints sync --all --time-budget 1800
```
On the next run, `mcp-fingerprints` automatically skips finished stages and resumes from the exact page and cursor where it stopped. Completed stage marks are removed stage-by-stage until the file is deleted upon full completion.

### Scenario 8: Zero-Pull Docker Hub & Polyglot GitHub Discovery
* **Use Case Description**: Discovering containerized MCP servers on Docker Hub and compiled Rust/Go servers on GitHub without downloading gigabytes of container layers or cloning full git repositories.
* **How It Works**: Headless inspection queries Docker Hub / OCI Registry V2 metadata and GitHub topic search APIs (`topic:mcp-server` with `rust`/`go`), fetching only `Cargo.toml`, `go.mod`, and `README.md` to extract tool signatures via `doc_parser`:
```bash
# Run targeted Docker Hub and GitHub polyglot discovery
mcp-fingerprints sync --docker --polyglot
```

### Scenario 9: Rust Systems Polyglot & `rmcp` Macro Parsing (CodeScene & Crates.io)
* **Use Case Description**: Ingesting high-performance Rust MCP servers (such as CodeScene `@codescene/codehealth-mcp`) distributed via Crates.io or native binaries whose tools are defined via declarative Rust macros.
* **How It Works**: The dedicated Crates.io crawler queries `crates.io/api/v1/crates` for `mcp` keywords, while the enhanced Rust AST parser extracts tool definitions, docstrings, and parameter types from official `rmcp` (v2.x) macros (`#[tool(description = "...")] async fn`) and `pmcp-macros`.

### Scenario 10: Cloud-Native Go Ingestion & `mark3labs/mcp-go` Builder Parsing
* **Use Case Description**: Indexing Go modules and cloud-native Kubernetes/Docker MCP servers implementing the protocol via dynamic builder patterns.
* **How It Works**: `mcp-fingerprints` crawls `pkg.go.dev` and GitHub Go modules, recursively scanning nested `/cmd/*` and `/pkg/*` directories. The Go AST parser extracts tool signatures, parameters, descriptions, and required keys directly from `mcp.NewTool(...)` and `s.AddTool(...)` builder patterns.

### Scenario 11: Enterprise JVM (Spring AI `@Tool`) & .NET C# Ingestion
* **Use Case Description**: Cataloging enterprise Java/Kotlin (Spring AI, Quarkus) and C# (.NET Semantic Kernel) MCP servers published on Maven Central or NuGet.
* **How It Works**: The Enterprise Indexer queries Maven Central (`io.modelcontextprotocol`, `spring-ai-mcp`) and NuGet, while the polyglot AST visitors parse Spring AI `@Tool(name = "...", description = "...")` annotations, `@ToolParam`, and C# `[McpServerTool]` / `[KernelFunction]` attributes.

### Scenario 12: Standalone PEP 723 `uvx` Python Scripts & Docker Container Ingestion
* **Use Case Description**: Supporting lightweight, single-file Python MCP tools run directly via `uvx <script_url>` without a full PyPI package, as well as containerized Docker Hub servers.
* **How It Works**: The PEP 723 parser reads inline `# /// script` metadata blocks to extract script dependencies, metadata, and FastMCP/MCP tool signatures, while the Docker Hub crawler extracts container names, tags, and stdio execution parameters (`docker run -i --rm ...`).

### Scenario 13: Multilingual & Cross-Regional MCP Ingestion (CJK Unicode Sanitization)
* **Use Case Description**: Indexing international MCP tools from Chinese and Japanese developer ecosystems (Dify plugins, WeChat/WeCom, Bilibili, and `模型上下文协议`) without character degradation or false-positive heuristic rejections.
* **How It Works**: The sanitizer preserves Unicode, CJK, and international characters cleanly while stripping control characters. Multilingual search query expansion automatically captures regional community MCP tools.

---

## Dual-Transport Live Probing & Attribution (`stdio` + `http`)
Connect to any live MCP server via local subprocess (`stdio`) or remote URL (`http`/`sse`), identify what it is, and retrieve its official repository and download instructions:

```bash
# Probe local server with concise 3-line summary
mcp-fingerprints probe --format short -- npx -y @modelcontextprotocol/server-postgres postgresql://localhost/db

# Probe remote HTTP/SSE endpoint
mcp-fingerprints probe --url http://localhost:8000/sse --format long

# Authenticated remote endpoint
mcp-fingerprints probe --url https://api.example.com/mcp --header "Authorization: Bearer mytoken"
```

**Python SDK:**
```python
from mcp_fingerprints import identify_stdio, identify_http

# Identify local subprocess
report = identify_stdio(["uvx", "mcp-server-git"])
print(f"Verified: {report.package_name} ({report.repository_url})")

# Identify remote HTTP/SSE endpoint
remote = identify_http("https://mcp.internal.acme.com/sse")
print(f"Remote Server: {remote.package_name} v{remote.version}")
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

# Auto-discover local configs with generic agent detection and baseline drift tracking
python -m mcp_fingerprints.cli scan --auto --save-baseline baseline.json
python -m mcp_fingerprints.cli scan --auto --diff baseline.json

# Detect if a generic command or URL is an MCP server
python -m mcp_fingerprints.cli detect "uvx mcp-server-git"
python -m mcp_fingerprints.cli detect http://localhost:8000/sse

# Auto-generate passports for locally discovered tools
python -m mcp_fingerprints.cli scan --auto --auto-passport

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

## Reporting & Output Formats

Customize the output verbosity to fit your terminal or CI environment:

```bash
# Concise 3-line summary for quick checks and CI logs
mcp-fingerprints probe --format short -- npx -y @modelcontextprotocol/server-sqlite --db app.db

# Exhaustive schema and parameter audit report
mcp-fingerprints probe --format long -- npx -y @modelcontextprotocol/server-sqlite --db app.db

# Structured JSON output for scripting and automation
mcp-fingerprints probe --json -- npx -y @modelcontextprotocol/server-sqlite --db app.db
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
