# Task 93: Re-index Passports for Servers with Upgraded AST & SDK Tool Patterns

> **Issue**: [#67](https://github.com/JMartynov/mcp-fingerprints/issues/67)  
> **Workflow Mandate**: Phase 4 Step 3 & Phase 5 Step 2 of `docs/tasks/task_88_daily_audit_ai_workflow_and_resolution_protocol.md`

## 1. Context & Motivation
Following the enhancements to `DeepZeroToolAuditor` and AST pattern extraction (`server.registerTool(...)`, `server.tool(...)`, Python `Tool(name=...)`, and nested subdirectory scanning) in Task 91/92:
- 18 target servers were confirmed to have live tools in their upstream repositories (`capsulemcp`, `@zvid/mcp`, `giorgio44/gateonai-mcp-server`, `notion-mcp-server`, `audionaut-mcp`, etc.).
- However, their existing passports in `data/fingerprints/` still record `0 tools`.
- Per our workflow standard, when extraction algorithms improve, all affected passports must be re-indexed so the catalog and database reflect the updated tool signatures.

## 2. Requirements & Deliverables

### A. Re-Indexing Script
Create `src/mcp_fingerprints/reindex_sdk_passports.py` (analogous to `src/mcp_fingerprints/reindex_golang_passports.py`) that:
1. Iterates over candidate passports in `data/fingerprints/` that currently have 0 tools or match target SDK patterns (`server.registerTool`, `server.tool`, `Tool(name=...)`).
2. Targets at least the 18 flagged servers:
   - `soil-dev_capsulemcp.json`
   - `@zvid_mcp.json`
   - `giorgio44_gateonai-mcp-server.json`
   - `awkoy_notion-mcp-server.json`
   - `audionaut-mcp.json`
   - `tufantunc_ssh-mcp.json`
   - `ihor-sokoliuk_mcp-searxng.json`
   - `bvisible_mcp-ssh-manager.json`
   - `PhilipAD_health-export-mcp.json`
   - `eslint-plugin-mcp-sdk-security.json`
   - `api-auto-mcp-server.json`
   - `1mcp-app_agent.json`
   - `@fodx_codelens.json`
   - `@fruggr_zendesk-mcp-server.json`
   - `@jrpool_kilotest.json`
   - `@mojomo_mcp-server.json`
   - `@openephemeris_mcp-server.json`
   - `AutomateLab-tech_content-distribution-mcp.json`
3. Inspects the upstream repository (handling branches `main` / `master`, token authentication via `GITHUB_TOKEN`, and SSL fallbacks).
4. Extracts tool definitions using the improved regex and AST patterns.
5. Updates the corresponding passport JSON file in `data/fingerprints/` with the new tool signatures, computing canonical hashes and tool counts.
6. Re-syncs `data/.passport_cache.json` and updates `web/catalog.json` if applicable.

### B. Unit & Regression Tests
Add unit tests in `tests/test_reindex_sdk_passports.py` verifying:
- Upstream tool extraction and parsing against mocked repository tree / files.
- Passport JSON updating logic preserves existing metadata while populating `tools` and `tool_count`.

### C. Phase 5 Fix & Re-Index Report
Publish the fix and delta report at:
`docs/reports/daily_web_audits/fixes/2026-10-28_passports_reindex_fix_report.md`

**Required Contents**:
- Cross-references to Issue [#67](https://github.com/JMartynov/mcp-fingerprints/issues/67), Task 88 protocol, and previous audit reports.
- Direct links to modified files and line ranges:
  - `[src/mcp_fingerprints/reindex_sdk_passports.py](file:///...)`
  - `[tests/test_reindex_sdk_passports.py](file:///...)`
  - Links to updated passport files under `data/fingerprints/`.
- **Passport Delta Summary**: Table showing before-vs-after tool counts for each re-indexed passport.
