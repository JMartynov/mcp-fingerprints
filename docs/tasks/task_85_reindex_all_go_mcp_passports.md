# Task Contract: Task 85 — Re-index and Re-create Passports for All Go MCP Servers

## 1. Problem Statement & Mission Overview
With the integration of PR #38 and Task 83/84:
- The Go AST extraction engine (`src/mcp_fingerprints/ast_parser.py` and `src/mcp_fingerprints/go_sdk_parser.py`) now fully supports:
  1. Official Go SDK `Server.AddTool(&mcp.Tool{ ... }, handler)` and `mcp.Tool{ ... }` struct literals.
  2. Top-level single and block constant name and description resolution (`const toolName = "..."`, `const ( ... )`).
  3. Complex Go map/slice schemas (`map[string]any{...}`) and Go string escapes (`\x65`, `\u00e9`, octal).
  4. Custom import alias handling (`import mymcp "github.com/modelcontextprotocol/go-sdk/mcp"`).
  5. Fallback from description to title when description is empty or truncated.

Currently, across the repository catalog, there are **117 Go MCP servers** (cataloged in `data/samples/golang_mcp_servers_inventory.json`). Out of these, **59 servers** currently have `tool_count: 0` / `capabilities.tools: false` because their passports were created prior to these official SDK literal and constant resolution improvements.

**Mission**:
Iterate through all Go MCP servers in the catalog (`data/fingerprints/*.json`), re-fetch or re-parse their source code using the upgraded Go AST parser (`parse_golang_mcp_code`), re-extract their complete toolsets, re-calculate canonical tool hashes, update their passports in `data/fingerprints/`, and refresh the web catalog.

---

## 2. Technical Scope & Implementation Plan

### A. Re-Indexing Script / Module (`src/mcp_fingerprints/reindex_golang_passports.py`)
Build a dedicated, resilient CLI script to re-index all Go MCP passports:
1. **Load Inventory**:
   - Read all passports from `data/fingerprints/` matching ecosystem `golang`, `go`, or `pkg:golang`.
2. **Re-Fetch / Re-Parse Upstream Source**:
   - For each server with a valid GitHub repository URL:
     - Fetch relevant entrypoint files (`main.go`, `server.go`, `mcp.go`, `tools.go`, `app.go`, etc.) or examine candidate files under `tools/`, `cmd/`, `pkg/`.
     - Run `parse_golang_mcp_code(code)`.
3. **Passport Update Invariants**:
   - If tools are discovered:
     - Update `capabilities.tools = True`.
     - Recompute canonical tool signatures and toolset hash using `canonicalize_json` and `compute_sha256`.
     - Populate `tool_signatures` without erasing existing descriptions, licenses, or URLs.
   - If no tools are found but tool indicators exist:
     - Flag `extraction_status = "UNRESOLVED_EXTRACTION"`.
   - If verified toolless:
     - Retain `capabilities.tools = False`.
4. **Summary & Metrics Report**:
   - Output an audit report in `docs/reports/golang_passports_reindex_report.md` detailing:
     - Total Go servers processed.
     - Number of passports updated with newly recovered tools.
     - Newly discovered tool names per server.
     - Servers that remain zero-tool (with root causes).

---

### B. Catalog Refresh
1. Re-generate `web/catalog.json` (or synchronize changed passport records) to reflect updated tool counts and signatures.
2. Ensure `web/updates/latest_update.json` reflects any updated packages.

---

### C. Automated Unit & Integration Tests (`tests/test_reindex_golang_passports.py`)
1. Test batch re-indexing on a mock set of Go passports.
2. Verify that `capabilities.tools` correctly transitions from `False` to `True` when composite literals or constants are present.
3. Verify that existing non-Go passports and existing metadata (licenses, authors) remain completely untouched.

---

## 3. Strict Safety & Publication Gates
- **Domain Constraint**: Pure metadata, AST parsing, and passport cataloging. **NEVER** introduce security testing, vulnerability scanning, or attack tools.
- **Report-Only Publishing**: Commit updated passports under `data/fingerprints/`, the report under `docs/reports/`, and the re-indexer script under `src/mcp_fingerprints/`. Clean up any temporary scratch files before committing.
- **Verification**: Run `pytest tests/test_reindex_golang_passports.py` and full suite `pytest -q tests/`.
