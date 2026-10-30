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
- **Catalog Card vs Passport Discrepancies**: 41 servers
- **Passports Missing Repository URLs**: 907 (15.1%)
- **Passports Linking to Third-Party Hubs (`smithery.ai`, `glama.ai`)**: 251 (4.2%)
- **Confirmed Direct GitHub Repositories**: 4,221 (70.2%)
- **Other Repositories (GitLab, Bitbucket, vanity URLs)**: 636 (10.5%)

---

## 2. Issues Discovered Across Multi-Level Inspections

### Level 1: Catalog Card vs Passport Canonical Desynchronization (41 Servers)
Direct discrepancies were discovered where catalog cards in `web/catalog.json` disagreed with the underlying passport in `data/fingerprints/`:
1. **Confirmed Zero-Tool Gateways/SDKs with Inflated Card Tools (8 servers)**:
   - `@fruggr/zendesk-mcp-server` (Card: 144, Passport: 0)
   - `api-auto-mcp-server` (Card: 46, Passport: 0)
   - `@covalenthq/goldrush-mcp-server` (Card: 28, Passport: 0)
   - `ssh-mcp` (Card: 15, Passport: 0)
   - `mnemostack` (Card: 9, Passport: 0)
   - `privacyfence` (Card: 8, Passport: 0)
   - `davinci-resolve-mcp` (Card: 5, Passport: 0)
   - `pydantic-ai` (Card: 1, Passport: 0)
   *Root Cause*: Recent audit fixes zeroed passport tool counts to reflect pure SDK client/remote gateway status, but the web catalog card JSON was not re-synchronized.
2. **Inverted Tool Signatures (Card: 0, Passport: > 0) (9 servers)**:
   - `@theo.foobar/mcp-time` (Card: 0, Passport: 5)
   - `mcp-proxy` (Card: 0, Passport: 10)
   - `solana-mcp-server` (Card: 0, Passport: 11)
   - `ai-agent-browser` (Card: 0, Passport: 21)
   - `bitrix24-mcp` (Card: 0, Passport: 44)
   - `ntfy-me-mcp` (Card: 0, Passport: 2)
   - `mcp-shield` (Card: 0, Passport: 2)
   - `mcp-server` (Card: 0, Passport: 4 / 19)
   *Root Cause*: Passports were enriched during AST passes, but catalog card synchronizer did not push new tool arrays into `web/catalog.json`.
3. **Unequal Tool Counts (Both > 0) (5 servers)**:
   - `mcp-searxng` (Card: 1 vs Passport: 5)
   - `docker-mcp` (Card: 1 vs Passport: 4)
   - `duckduckgo-mcp-server` (Card: 1 vs Passport: 3)
   - `bear-mcp-server` (Card: 3 vs Passport: 4)
   - `jira_communication_server` (Card: 3 vs Passport: 11)
4. **Card Claims Tools but Passport Has Zero (19 servers)**:
   - `graph-tool-call` (Card: 7), `basedagents` (Card: 60), `orieg/gws-connector` (Card: 49), `autario-mcp` (Card: 58), `mobile-next/mobile-mcp` (Card: 34), `serkan-ozal/driflyte-mcp-server` (Card: 38), etc.

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
        ├── Task 98: Reconcile 41 Discrepant Servers (Jules Active)
        ├── Task 99: Enforce Zero Tools for Confirmed Remote Gateways in Catalog
        ├── Task 100: Recover Inverted Tool Signatures (Card > 0, Passport == 0)
        └── Task 101: Push Passport Tool Signatures to Catalog (Passport > 0, Card == 0)

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
| **Task 98** | Reconcile Catalog Cards vs Passport Source Truth | 🔄 In Progress | Pending Jules | Dispatch session active |
| **Task 99** | Zero-Tool Gateway Catalog Normalization | ⏳ Queued | - | Follows Task 98 |
| **Task 100** | Inverted Tool Signature Recovery | ⏳ Queued | - | - |
| **Task 101** | Tool Signature Push to Catalog | ⏳ Queued | - | - |
| **Tasks 102–106** | Tier 2 Hub & Source URL Resolution | ⏳ Queued | - | - |
| **Tasks 107–113** | Tier 3 Polyglot AST Re-Extraction | ⏳ Queued | - | - |
| **Tasks 114–117** | Tier 4 Verification & Master Re-bundling | ⏳ Queued | - | - |

*(Report is updated cumulatively as Jules tasks land and verify on `main`)*
