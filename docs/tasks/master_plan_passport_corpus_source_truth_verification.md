# Master Plan: Comprehensive Passport Corpus Source Truth Verification & Remediation (Tasks 98–117)

> **Workflow Standard**: `docs/tasks/task_88_daily_audit_ai_workflow_and_resolution_protocol.md`  
> **Target Corpus**: 6,015 Passports across Python, TypeScript/Node, Go, Rust, Java/C#, and Generic MCP servers in `data/fingerprints/` and `web/catalog.json`.

---

## Executive Overview

A preliminary automated census of the 6,015 server passports revealed:
- **3,032 passports** (50.4%) record `0` tool signatures.
- **41 passports** exhibit direct discrepancies between web catalog cards (`web/catalog.json`) and source passport files (`data/fingerprints/`).
- **907 passports** lack an explicit upstream repository URL (`None`).
- **251 passports** link to third-party aggregation hubs (`smithery.ai`, `glama.ai`) rather than authentic GitHub upstreams.
- Recent enhancements in Tasks 91–97 introduced TypeScript `@modelcontextprotocol/sdk` pattern extraction, Python `Tool(...)` AST extraction, and primary doc Markdown table extraction, but **thousands of historical passports have never been re-scanned or re-indexed** against these modern extractors.

To ensure all passports **faithfully reflect upstream source data truth**, we establish a 4-Tier, 20-Task Verification and Remediation Program executed via Google Jules sub-agents.

---

## 4-Tier Verification Framework

### Tier 1: Catalog Card vs Passport Canonical Reconciliation (Tasks 98–101)
- Align tool counts, descriptions, and metadata between `web/catalog.json` and `data/fingerprints/*.json`.
- Enforce confirmed zero-tool gateway/SDK wrapper policies across all catalog cards.
- Detect discrepancies caused by out-of-order writes or partial updates.

### Tier 2: Upstream Source Repository & Hub Link Resolution (Tasks 102–106)
- Resolve missing repository URLs for PyPI, npm, and NuGet packages by querying registry metadata APIs offline or with fixtures.
- Convert third-party aggregator links (`smithery.ai`, `glama.ai`) to genuine GitHub repository URLs.
- Classify repositories as active open-source, remote cloud gateway, or dead/archived.

### Tier 3: Polyglot AST & SDK Re-Extraction & Re-Indexing (Tasks 107–113)
- Re-scan candidate zero-tool passports against updated AST extractors:
  - TypeScript SDK: `server.registerTool(...)`, `server.tool(...)`, nested `src/tools/` subdirectories.
  - Python SDK: `Tool(name=...)`, `@mcp.tool()`, `@action`, `@command`.
  - Go SDK: Official composite literals and `mcp.NewServer(...)`.
  - Markdown documentation tables (`README.md`, `docs/tools.md`) excluding secondary release logs.
- Recompute `toolset_canonical_hash` and refresh `data/.passport_cache.json`.

### Tier 4: Zero-Tool Remote Gateway Validation & Corpus Audit Synthesis (Tasks 114–117)
- Systematically validate confirmed 0-tool servers (SDK clients, proxies, documentation mirrors).
- Run full regression testing with the network isolation guard (`tests/conftest.py`).
- Compile and publish the Cumulative Passport Quality Audit Report (`docs/reports/passport_corpus_source_truth_audit_report.md`).
- Re-bundle `passports.json.gz` and synchronize web catalog.

---

## 20-Task Work Breakdown Structure (Tasks 98–117)

| Task ID | Tier | Title | Target Scope | Jules Mode / Role |
|:---|:---:|:---|:---|:---|
| **Task 98** | Tier 1 | Catalog-Passport Discrepancy Ingestion & Triage | 41 known mismatched cards in `web/catalog.json` vs `data/fingerprints/` | Mode 1 / Research Subagent |
| **Task 99** | Tier 1 | Catalog Tool Count Normalization for Confirmed Gateways | Fix card claims on 7 confirmed zero-tool gateways/SDKs in `web/catalog.json` | Mode 1 / Implementation Worker |
| **Task 100** | Tier 1 | Inverted Tool Signature Recovery (Card > 0, Passport == 0) | Recover missing tools for 22 servers where catalog had signatures lost in passports | Mode 1 / Implementation Worker |
| **Task 101** | Tier 1 | Inverted Tool Signature Sync (Passport > 0, Card == 0) | Update catalog cards for 12 servers where passports have tools but cards show 0 | Mode 1 / Implementation Worker |
| **Task 102** | Tier 2 | Hub Link Fallback Resolution: PyPI Servers (Smithery/Glama) | Resolve 94 PyPI passports with `smithery.ai` URLs to GitHub repositories | Mode 1 / Implementation Worker |
| **Task 103** | Tier 2 | Hub Link Fallback Resolution: npm Servers (Smithery/Glama) | Resolve 142 npm passports with `smithery.ai` URLs to GitHub repositories | Mode 1 / Implementation Worker |
| **Task 104** | Tier 2 | Missing Upstream URL Resolution: PyPI Ecosystem | Populate `repository_url` for 180 PyPI passports missing source URLs | Mode 1 / Implementation Worker |
| **Task 105** | Tier 2 | Missing Upstream URL Resolution: npm Ecosystem | Populate `repository_url` for 310 npm passports missing source URLs | Mode 1 / Implementation Worker |
| **Task 106** | Tier 2 | Dead Repo & Unreachable Source Triage | Formally tag 55 unreachable/archived repos as `UNREACHABLE_OR_PRIVATE_REPO` | Mode 1 / Research & Worker |
| **Task 107** | Tier 3 | TypeScript SDK AST Re-Extraction: Core Node Servers | Re-index 250 top npm zero-tool servers with `server.registerTool` extractor | Mode 1 / Implementation Worker |
| **Task 108** | Tier 3 | TypeScript SDK AST Re-Extraction: Scoped Packages (`@*/*`) | Re-index 200 scoped npm zero-tool servers with nested directory scanning | Mode 1 / Implementation Worker |
| **Task 109** | Tier 3 | Python SDK AST Re-Extraction: Low-level `Tool()` Patterns | Re-index 180 Python zero-tool servers with low-level `Tool(...)` pattern | Mode 1 / Implementation Worker |
| **Task 110** | Tier 3 | Python FastMCP & Decorator Tool Re-Extraction | Re-index 150 Python zero-tool servers with `@mcp.tool()` / FastMCP decorators | Mode 1 / Implementation Worker |
| **Task 111** | Tier 3 | Markdown Table Tool Extraction: npm Servers | Extract tools from `README.md` tables for 120 npm servers lacking source AST | Mode 1 / Implementation Worker |
| **Task 112** | Tier 3 | Markdown Table Tool Extraction: PyPI & Generic Servers | Extract tools from `README.md` tables for 90 PyPI/generic servers lacking AST | Mode 1 / Implementation Worker |
| **Task 113** | Tier 3 | Go & Rust MCP Server AST Re-Extraction | Re-index 118 Go/Rust zero-tool servers using composite literal extractors | Mode 1 / Implementation Worker |
| **Task 114** | Tier 4 | Canonical Hash & Schema Conformance Re-Verification | Verify `toolset_canonical_hash` and passport schema across all 6,015 files | Mode 1 / Verifier Subagent |
| **Task 115** | Tier 4 | Offline Test Guard Verification & Regression Suite | Ensure 100% pytest pass rate with `tests/conftest.py` socket block | Mode 1 / Verifier Subagent |
| **Task 116** | Tier 4 | Master Dataset & Snapshot Re-Bundling | Rebuild `passports.json.gz`, update `data/.passport_cache.json`, and web catalog | Mode 1 / Implementation Worker |
| **Task 117** | Tier 4 | Cumulative Audit Report & Release Notes Publication | Compile `docs/reports/passport_corpus_source_truth_audit_report.md` & tag | Mode 1 / Review & Release |

---

## Execution Protocol

1. **Wave-based Fan-Out**: Execute tasks in 4 sequential waves (Tier 1 -> Tier 2 -> Tier 3 -> Tier 4).
2. **Token Insulation**: Each task runs inside an isolated Google Jules sub-agent (`bin/jules-gate wait <id> --interactive`).
3. **No Unmocked Sockets**: All verification in unit tests strictly obeys the network guard in `tests/conftest.py`.
4. **Deliverables**:
   - Updated passports in `data/fingerprints/`.
   - Updated catalog in `web/catalog.json`.
   - Clean regression test pass.
   - Cumulative audit report at `docs/reports/passport_corpus_source_truth_audit_report.md`.
