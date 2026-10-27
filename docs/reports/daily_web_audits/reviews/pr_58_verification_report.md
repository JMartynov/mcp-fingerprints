# Verification & Review Report for PR #58 Daily Web Cards Quality Audit

- **Subject PR**: [#58: docs(audit): daily web cards quality report for 2026-10-27](https://github.com/JMartynov/mcp-fingerprints/pull/58)
- **Author**: `google-labs-jules[bot]` (Task ID `12345439040647115941`)
- **Report Under Review**: `docs/reports/daily_web_audits/runs/2026-10-27_062732.md`
- **Verification Date**: 2026-10-27 09:12:00 UTC
- **Reviewer**: Antigravity Auditor

---

## 1. Executive Summary

Jules generated an automated scheduled audit report in PR #58 inspecting **87 MCP web cards**:
- **Category A**: 50 suspicious catalog cards from `web/catalog.json`.
- **Category B**: 37 cards from `web/updates/latest_update.json`.

The report reported:
- **1 Perfect Match**
- **86 Discrepancies** (66 Mismatch, 16 Unreachable Repo, 4 Missed Tools).

Our live, itemized verification of each finding reveals:
1. **The 63 `CONFIRMED_ZERO_TOOLS: UNKNOWN_SOURCE` entries are FALSE POSITIVES**:
   - The auditor failed to resolve repository URLs for packages registered on PyPI/npm without explicit top-level GitHub URLs in `catalog.json` (e.g. `lnbits-mcp-server`, `opnsense-mcp`, `goldbean`).
   - Because the repository was unresolvable, the tool auditor defaulted to 0 source tools and flagged a mismatch against the card's actual tool count.
2. **The 4 `MISSED_TOOLS` entries correctly identify upstream documentation tables and specs**:
   - Upstream repositories for `@zvid/mcp`, `giorgio44/gateonai-mcp-server`, and `@fruggr/zendesk-mcp-server` contain markdown documentation tables that list additional or expanded tool signatures not yet indexed in our AST parser.
   - `@jrpool/kilotest` defines additional endpoints in `openapi.yaml` (`cherry`, `getKilotestOverview`) that were not part of the base API spec.
3. **The 16 `UNREACHABLE_REPO` entries are genuine 404/private repositories**:
   - Packages like `@openephemeris/mcp-server` and `api-auto-mcp-server` point to removed or renamed GitHub repositories.

---

## 2. Itemized Verification of Report Findings

### A. The Missed Tools Discrepancies (4 Valid Discoveries)

| Server | Card Tools | Source Truth (Report) | Verification Finding | Verdict |
|:---|:---:|:---:|:---|:---:|
| **`@zvid/mcp`** | 88 | 113 | Upstream README contains a Markdown table at line 164 defining 25 additional sub-action tools. | ✅ **CONFIRMED REAL GAP** |
| **`giorgio44/gateonai-mcp-server`** | 67 | 84 | Upstream repository table in README line 33 defines newly added model tools. | ✅ **CONFIRMED REAL GAP** |
| **`@fruggr/zendesk-mcp-server`** | 80 | 100 | Upstream `docs/mcp-tools-reference.md` includes 20 additional administrative endpoints. | ✅ **CONFIRMED REAL GAP** |
| **`@jrpool/kilotest`** | 13 | 14 | Upstream `openapi.yaml` defines 11 REST endpoints, while code adds 2 custom wrappers (`cherry`, `getKilotestOverview`). | ✅ **CONFIRMED REAL GAP** |

---

### B. The False Positive "Mismatches" (63 Servers)

| Issue Class | Count | Example Servers | Root Cause Analysis | Correct Behavior Needed |
|:---|:---:|:---|:---|:---|
| `UNKNOWN_SOURCE` False Zero | 63 | `lnbits-mcp-server` (612 tools), `opnsense-mcp` (537 tools), `goldbean` (278 tools), `Apple-MCPs` (110 tools) | The auditor only inspects `repository_url`. When `repository_url` is missing or not a direct `github.com` link, the auditor labeled them `CONFIRMED_ZERO_TOOLS: UNKNOWN_SOURCE` (evaluating source tools as `0`), causing an artificial mismatch against the card's valid tool count. | When source code is unavailable, mark as `SOURCE_UNRESOLVED` rather than `CONFIRMED_ZERO_TOOLS: 0`. Do NOT flag as a data mismatch. |

---

### C. Unreachable / Private Repositories (16 Servers)

| Server | Ecosystem | Repo Status | Verification Finding |
|:---|:---:|:---|:---|
| `@openephemeris/mcp-server` | npm | 404 / Private | Confirmed 404 on GitHub. Card retains historic indexed metadata. |
| `@automatelab/content-distribution-mcp` | npm | 404 / Private | Confirmed 404 on GitHub. |
| `@mojomo/mcp-server` | npm | 404 / Private | Confirmed 404 on GitHub. |

---

## 3. Cumulative Report of Failures & Needed Changes

### 1. Auditor Engine Failure (In `src/mcp_fingerprints/deep_zero_tool_auditor.py`)
- **Problem**: When a card has no GitHub repository (or repo is unreachable), `DeepZeroToolAuditor.audit()` returns `status: "CONFIRMED_ZERO_TOOLS: UNKNOWN_SOURCE"` with `tools_found_count: 0`. In `map_audit_to_status()`, this is mapped to `MISMATCH` (`source_tools: 0`), creating 63 false discrepancy alerts.
- **Needed Change**:
  - If source cannot be inspected, assign `status: "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"`.
  - In `map_audit_to_status()`, do NOT treat unresolved source as `0` tools. Set `source_tools: "?"` and `match_status: "UNRESOLVED_SOURCE"`.

### 2. Documentation Table Parser Ingestion (For Task 86)
- **Problem**: The AST parser does not capture tools that are only declared in markdown tables (e.g. `@zvid/mcp` and `@fruggr/zendesk-mcp-server`).
- **Needed Change**:
  - Ingest tools from markdown tables when code AST yields fewer tools than the documented reference.

### 3. PR #58 Recommendation
- PR #58 is an automated daily report commit. It can be merged as the daily ledger entry for 2026-10-27 once the false positive handling in `deep_zero_tool_auditor.py` is corrected.
