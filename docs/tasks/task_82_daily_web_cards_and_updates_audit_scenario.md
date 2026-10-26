# Task Contract: Task 82 — Daily Scheduled Web Updates & Card Quality Inspection Agent

> **Scheduled Automation Contract**: Run once daily (`0 2 * * *`).  
> **Target Agent Profile**: Autonomous executor executing strictly deterministic commands with zero ambiguity.

---

## 1. Mission Overview & Purpose

The `mcp-fingerprints` web catalog displays interactive cards for thousands of MCP servers (`web/catalog.json`, `web/updates/latest_update.json`, `web/updates/*.json`). In production, catalog cards occasionally suffer from quality issues, such as:
1. **Suspicious cards with missing tools**: `tool_count: 0` or empty `tools: []` when the upstream repository actually defines tools.
2. **Missing descriptions / invalid metadata**: Empty descriptions, missing repository URLs, placeholders, or broken schema links.
3. **Truncated or garbled tool definitions**: AST extraction errors resulting in code fragments in description fields or missing tool parameters.
4. **Drift in recent updates**: Cards published in `web/updates/latest_update.json` that deviate from the actual source repository.

This contract defines the exact, sequential, step-by-step instructions for an automated daily audit worker. The worker must:
- Select suspicious cards (empty tools, incomplete metadata) across the catalog.
- Select all cards added or modified in the latest web update (`web/updates/latest_update.json`).
- Drill down directly into the upstream source repositories (GitHub / npm / PyPI / Crates.io).
- Verify why discrepancies occurred and verify whether card data matches reality.
- Generate an isolated daily markdown report in `docs/reports/daily_web_audits/runs/YYYY-MM-DD_HHMMSS.md`.
- Automatically merge and maintain the consolidated audit report at `docs/reports/daily_web_audits/master_audit_summary.md`.

---

## 2. Directory Layout & Report Storage Invariants

All outputs created by this task MUST strictly follow this directory structure:

```
docs/reports/daily_web_audits/
├── README.md                          # Directory index and metric ledger
├── master_audit_summary.md            # Merged summary across all historical daily runs
└── runs/
    ├── 2026-10-26_174510.md           # Individual audit run report with date-timestamp suffix
    └── YYYY-MM-DD_HHMMSS.md           # Future daily audit reports
```

- **Daily Report File**: `docs/reports/daily_web_audits/runs/YYYY-MM-DD_HHMMSS.md` (where `YYYY-MM-DD_HHMMSS` is the UTC date-time stamp of execution).
- **Consolidated Master Report**: `docs/reports/daily_web_audits/master_audit_summary.md`.
- **Publication & PR Invariant (STRICT)**:
  - **Publish ONLY reports**: The task is permitted to author temporary scratch scripts during local execution, but intermediate code, scratch modules, or experiment scripts MUST NOT be staged, committed, or published to PR.
  - **Auto-Merge Reports**: Only `docs/reports/daily_web_audits/` report markdown files and master ledger updates may be committed and auto-merged into `main`.
  - **Scratch Cleanup**: All temporary scripts created during analysis (e.g., `*.py` in repo root or `/tmp/`) must be cleaned up before staging changes.
- **Domain Constraint**: This task is purely a catalog metadata, AST validation, and quality audit task. **NEVER** introduce security testing, vulnerability scanning, exploit analysis, or offensive tooling.

---

## 3. Strict Step-by-Step Execution Protocol

The automated agent must execute the following 5 phases in exact numerical sequence.

### Phase 1: Card Selection & Harvest

The agent must identify two distinct candidate sets:

#### Candidate Set A: Suspicious Catalog Cards (`data/fingerprints/*.json` & `web/catalog.json`)
Filter and collect servers matching any of the following suspicious criteria:
1. `tool_count == 0` or `len(tools) == 0`.
2. `description` is `null`, `""`, or contains fewer than 10 characters.
3. `tools` contains entries where `description` starts with syntax artifacts (e.g., `", });"`, `"function("`, `"def "`, `"{"`).
4. `repository_url` is missing or `null` while ecosystem is not `generic`.
5. Max quota per daily run: **50 suspicious cards** (prioritized by highest GitHub stargazers or highest download count).

#### Candidate Set B: Latest Web Update Cards (`web/updates/latest_update.json`)
Extract all servers listed in `web/updates/latest_update.json`:
1. Read `web/updates/latest_update.json`.
2. Collect all servers in `servers[]` (typically 10–50 servers).
3. Coverage requirement: **100% of servers in latest_update.json must be verified**.

---

### Phase 2: Deep Source Verification (Drill Down)

For each selected card, the agent MUST clone or inspect the upstream source code:

1. **Resolve Repository URL**:
   - Inspect `card.repository_url`. If empty, inspect npm/PyPI registry metadata to find repository links.
   - If no repository exists (closed source or 404), mark status as `UNREACHABLE_REPO`.

2. **Inspect Upstream AST / Code**:
   - Clone or fetch tarball to a temporary directory (`/tmp/mcp_audit/<server_name>`).
   - Run `mcp-fingerprints` AST parsers (`src/mcp_fingerprints/ast_parser.py`) across all files.
   - Run OpenAPI parser (`src/mcp_fingerprints/openapi_parser.py`) if OpenAPI/Swagger specs exist.
   - Run Doc parser (`src/mcp_fingerprints/doc_parser.py`) against `README.md` and `docs/`.

3. **Compare Card Data vs Source Truth**:
   - Compare `card.tool_count` vs `actual_source_tool_count`.
   - Compare `card.tools[].name` vs `actual_source_tools[].name`.
   - Check if card tools are missing descriptions or arguments that exist in source code.
   - Check if tools exist in code that were missed by the catalog parser (`MISSED_TOOLS`).

4. **Classify Root Cause of Discrepancy**:
   - `PARSER_MISSED_DYNAMIC_REGISTRATION`: Tools registered via loop, dictionary, or array map.
   - `PARSER_MISSED_SUBDIRECTORY`: Tool files located outside standard entrypoints (`src/tools/`, `lib/actions/`).
   - `PARSER_MISSED_DECORATOR`: Non-standard decorator (e.g. `@app.action`, `@server.register`).
   - `DOCSTRING_EXTRACTION_FAILURE`: Tool description contains code syntax or was truncated.
   - `GENUINE_TOOLLESS_SERVER`: Repository is verified to be a pure prompt, resource, or client SDK.
   - `PERFECT_MATCH`: Card accurately reflects 100% of upstream tools and metadata.

---

### Phase 3: Daily Report Authoring

Generate `docs/reports/daily_web_audits/runs/YYYY-MM-DD_HHMMSS.md` with the following mandatory markdown template:

```markdown
# Daily Web Card Quality & Source Verification Report — YYYY-MM-DD HH:MM:SS UTC

## Executive Summary
- **Execution Timestamp**: YYYY-MM-DD HH:MM:SS UTC
- **Latest Web Update Version Inspected**: vX.Y.Z (web/updates/latest_update.json)
- **Total Cards Verified**: <N>
  - **Category A (Suspicious Catalog Cards)**: <count>
  - **Category B (Latest Web Update Cards)**: <count>
- **Perfect Match Rate**: <percentage>% (<passed>/<total>)
- **Discrepancies Identified**: <count>

---

## Detailed Findings Table

| Server Name | Ecosystem | Card Tools | Source Tools | Match Status | Root Cause / Discrepancy | Upstream File & Line |
|:---|:---|:---:|:---:|:---|:---|:---|
| `@org/example` | npm | 0 | 12 | ❌ MISSED_TOOLS | Dynamic registration loop | `src/tools/index.ts:45` |
| `mcp-server-foo` | pypi | 4 | 4 | ✅ PERFECT_MATCH | N/A | `mcp_foo/server.py:12` |

---

## In-Depth Analysis of Discrepancies

### 1. [Server Name]
- **Repository**: [URL](URL)
- **Expected (Source Truth)**: List of tools, parameters, descriptions discovered in code.
- **Observed (Card Data)**: Content currently present in `web/catalog.json`.
- **Root Cause**: Exact explanation of why parser failed or why card was incomplete.
- **Recommended Remediation**: Specific AST parser pattern or synchronizer rule fix needed.

---

## Action Items for AST & Synchronizer Engine
- [ ] Task item 1: Regex/AST update needed for pattern X
- [ ] Task item 2: Synchronizer update needed for metadata field Y
```

---

### Phase 4: Automated Report Merging (`master_audit_summary.md`)

After writing the daily report, update `docs/reports/daily_web_audits/master_audit_summary.md`:
1. **Read Existing Summary**: Read `docs/reports/daily_web_audits/master_audit_summary.md` (or initialize if not present).
2. **Append Daily Run Ledger**: Insert a new row in the historical ledger table:
   ```markdown
   | Date | Update Version | Cards Checked | Matches | Discrepancies | Report Link |
   |:---|:---:|:---:|:---:|:---:|:---|
   | YYYY-MM-DD | v1.0.21 | 45 | 39 | 6 | [runs/YYYY-MM-DD.md](runs/YYYY-MM-DD.md) |
   ```
3. **Update Cumulative Top Issues**: Increment discrepancy category counters (`PARSER_MISSED_DYNAMIC_REGISTRATION`, `EMPTY_DESCRIPTION`, etc.).
4. **Update Unresolved Remediation Backlog**: Append new action items to the master remediation list without duplicating already listed items.

---

### Phase 5: Verification & Safety Gates

Before completing the daily task:
1. Validate that `docs/reports/daily_web_audits/runs/YYYY-MM-DD_HHMMSS.md` exists and is non-empty.
2. Validate that `docs/reports/daily_web_audits/master_audit_summary.md` was updated.
3. Clean up all intermediate scratch files:
   - Ensure no temporary `.py`, `.sh`, or scratch log files remain in the repository root or worktree outside of standard `docs/reports/daily_web_audits/`.
4. Run existing test suite to ensure no files were corrupted:
   ```bash
   PYTHONPATH=src .venv/bin/pytest -q tests/
   ```
5. Commit and auto-merge ONLY report artifacts:
   ```bash
   git add docs/reports/daily_web_audits/
   git commit -m "docs(audit): daily web cards quality report for $(date -u +%F) [skip ci]"
   git push origin main
   ```
   Do NOT stage or publish any intermediate code files.

---

## 4. Automation Shell Script Helper (`bin/run-daily-card-audit.sh`)

To enable execution via cron or Antigravity `/schedule`, the following CLI entrypoint encapsulates the full protocol:

```bash
#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d_%H%M%S")
echo "=== Starting Daily MCP Web Card Audit for ${TIMESTAMP} ==="
mkdir -p docs/reports/daily_web_audits/runs

PYTHONPATH=src python3 -m mcp_fingerprints.deep_zero_tool_auditor \
  --web-updates web/updates/latest_update.json \
  --catalog web/catalog.json \
  --output "docs/reports/daily_web_audits/runs/${TIMESTAMP}.md" \
  --merge-summary "docs/reports/daily_web_audits/master_audit_summary.md" \
  --max-suspicious 50

echo "=== Audit complete: docs/reports/daily_web_audits/runs/${TIMESTAMP}.md ==="
```
