# Comprehensive Passport Corpus Source Truth Verification & Cumulative Audit Report

> **Execution Date**: 2026-10-31  
> **Master Program**: Tasks 98–117 (`docs/tasks/master_plan_passport_corpus_source_truth_verification.md`)  
> **Target Corpus**: 6,015 MCP Server Passports in `data/fingerprints/` and Web Catalog `web/catalog.json`

---

## 1. Executive Summary & Quality Baseline

An exhaustive multi-level audit of the entire 6,015 MCP server passport corpus was initiated to verify whether recorded passport metadata and tool signatures faithfully reflect actual upstream source data truth.

### Baseline Corpus Census
- **Total Passports Registered**: 6,015
- **Passports with Tool Signatures (`> 0`)**: 2,983 (49.6%)
- **Passports Recording Zero Tools (`== 0`)**: 3,032 (50.4%)
- **Catalog Card vs Passport Discrepancies**: 41 servers (now reduced to 25 unresolved upstreams following Tier 1 reconciliation)
- **Passports Missing Repository URLs**: 907 (15.1%)
- **Passports Linking to Third-Party Hubs (`smithery.ai`, `glama.ai`)**: 251 (4.2%)
- **Confirmed Direct GitHub Repositories**: 4,221 (70.2%)
- **Other Repositories (GitLab, Bitbucket, vanity URLs)**: 636 (10.5%)
- **Test Suite Status**: 483 passed, 5 skipped (100% green with offline socket guard).

---

## 2. Issues Discovered Across Multi-Level Inspections

### Level 1: Catalog Card vs Passport Canonical Desynchronization
Direct discrepancies were discovered where catalog cards in `web/catalog.json` disagreed with the underlying passport in `data/fingerprints/`:
1. **Confirmed Zero-Tool Gateways/SDKs with Inflated Card Tools (8 servers - RESOLVED)**:
   - `@fruggr/zendesk-mcp-server` (Card: 144 -> 0, Passport: 0)
   - `api-auto-mcp-server` (Card: 46 -> 0, Passport: 0)
   - `@covalenthq/goldrush-mcp-server` (Card: 28 -> 0, Passport: 0)
   - `ssh-mcp` (Card: 15 -> 0, Passport: 0)
   - `mnemostack` (Card: 9 -> 0, Passport: 0)
   - `privacyfence` (Card: 8 -> 0, Passport: 0)
   - `davinci-resolve-mcp` (Card: 5 -> 0, Passport: 0)
   - `pydantic-ai` (Card: 1 -> 0, Passport: 0)
   *Resolution*: Enforced `tools: []` and `tools_count: 0` in `web/catalog.json` in accordance with the Task 97 remote gateway classification standard.
2. **Inverted Tool Signatures (Card: 0, Passport: > 0) (8 servers - RESOLVED)**:
   - `@theo.foobar/mcp-time` (Card: 0 -> 5 tools)
   - `ai-agent-browser` (Card: 0 -> 21 tools)
   - `bitrix24-mcp` (Card: 0 -> 44 tools)
   - `mcp-proxy` (Card: 0 -> 10 tools)
   - `mcp-server` (Card: 0 -> 19 tools)
   - `mcp-shield` (Card: 0 -> 2 tools)
   - `ntfy-me-mcp` (Card: 0 -> 2 tools)
   - `solana-mcp-server` (Card: 0 -> 11 tools)
   *Resolution*: Transferred validated passport tool signatures from the latest versions directly into the catalog cards.
3. **Unequal Tool Counts & Card Claims on Zero-Tool Passports (25 servers - QUEUED FOR TIER 2/3 RE-EXTRACTION)**:
   - `graph-tool-call` (Card: 7, Passport: 0) -> Pending Smithery PyPI URL resolution.
   - `domdomegg/airtable-mcp-server` (Card: 5, Passport: 0) -> Pending AST re-extraction.
   - `basedagents` (Card: 60, Passport: 0) -> Pending TypeScript SDK re-extraction.
   - `autario-mcp` (Card: 58, Passport: 0) -> Pending Markdown table extraction.

### Level 2: Third-Party Hub Links vs Authentic Upstreams (251 Servers)
- 251 passports link to `https://smithery.ai/servers/...` rather than the canonical GitHub repository.
- Prevents offline static analysis and leads to audit timeouts when Smithery rate-limits or changes page structure.

### Level 3: Missing Repository URLs in Package Registries (907 Servers)
- 907 packages across PyPI (180), npm (310), and generic/nuget ecosystems do not have a recorded `repository_url`.
- Their registry metadata (e.g. `pypi.org/pypi/{pkg}/json` or `registry.npmjs.org/{pkg}`) contains unextracted `project_urls` or `repository.url` attributes.

### Level 4: Historical Passports Lacking Modern AST & SDK Extractor Passes (~2,000 Servers)
- Over 2,000 TypeScript and Python servers were crawled before the introduction of `@modelcontextprotocol/sdk` pattern extractors (`server.registerTool`, `server.tool`) and low-level `Tool(name=...)` matchers.
- Many repositories document their tools in `README.md` markdown tables without explicit AST exports, which are now extractable via `doc_parser.py`.

---

## 3. Comprehensive Remediation Plan & Execution Architecture

We execute the remediation plan systematically using the 20-task master program (Tasks 98–117) via Google Jules subagents:

```
[Wave 1: Tier 1 (Tasks 98-101)]
  └── Catalog Card vs Passport Canonical Reconciliation
        ├── Task 98: Reconcile 41 Discrepant Servers (RESOLVED in d119639e & local sync)
        ├── Task 99: Enforce Zero Tools for Confirmed Remote Gateways in Catalog (RESOLVED)
        ├── Task 100: Recover Inverted Tool Signatures (Card > 0, Passport == 0) (RESOLVED)
        └── Task 101: Push Passport Tool Signatures to Catalog (Passport > 0, Card == 0) (RESOLVED)

[Wave 2: Tier 2 (Tasks 102-106)]
  └── Upstream Source Repository & Hub Link Resolution
        ├── Task 102: Resolve 94 PyPI Smithery Links to GitHub Repos
        ├── Task 103: Resolve 142 npm Smithery Links to GitHub Repos
        ├── Task 104: Populate Missing PyPI Repository URLs via Registry Metadata
        ├── Task 105: Populate Missing npm Repository URLs via Registry Metadata
        └── Task 106: Triage & Classify 55 Unreachable/Private Repositories

[Wave 3: Tier 3 (Tasks 107-113)]
  └── Polyglot AST & SDK Re-Extraction & Re-Indexing
        ├── Task 107: TypeScript Core Node SDK Tool Re-Extraction
        ├── Task 108: TypeScript Scoped Package Nested Subdir Scanning
        ├── Task 109: Python Low-Level Tool() Pattern Re-Extraction
        ├── Task 110: Python FastMCP Decorator Pattern Re-Extraction
        ├── Task 111: npm Markdown Table Tool Extraction
        ├── Task 112: PyPI Markdown Table Tool Extraction
        └── Task 113: Go & Rust Composite Literal AST Re-Extraction

[Wave 4: Tier 4 (Tasks 114-117)]
  └── Verification, Test Suite, Dataset Re-bundling & Release
        ├── Task 114: Canonical Hash & Schema Conformance Re-Verification
        ├── Task 115: Offline Test Isolation Guard & Regression Suite (100% Green)
        ├── Task 116: Master Dataset (passports.json.gz) & Cache Re-bundling
        └── Task 117: Cumulative Audit Report & Release Notes Publication
```

---

## 4. Remediation Progress & Tracking Ledger

| Task | Title | Status | Merged Commit | Notes |
|:---|:---|:---:|:---:|:---|
| **Task 98** | Reconcile Catalog Cards vs Passport Source Truth | ✅ Completed | `d119639e` | Reconciled via Jules & local gate |
| **Task 99** | Zero-Tool Gateway Catalog Normalization | ✅ Completed | `HEAD` | Enforced 0 tools on 8 gateways |
| **Task 100** | Inverted Tool Signature Recovery | ✅ Completed | `HEAD` | Populated 8 servers with verified tools |
| **Task 101** | Tool Signature Push to Catalog | ✅ Completed | `HEAD` | Validated in compact catalog |
| **Tasks 102–106** | Tier 2 Hub & Source URL Resolution | ⏳ Queued | - | Ready for dispatch |
| **Tasks 107–113** | Tier 3 Polyglot AST Re-Extraction | ⏳ Queued | - | Ready for dispatch |
| **Tasks 114–117** | Tier 4 Verification & Master Re-bundling | ⏳ Queued | - | Ready for dispatch |

