# Remediation Fix Report: Daily Web Cards Audit Discrepancies (PR #58 / Tasks 86–87)

- **Date of Fix**: 2026-10-27
- **Scope**: Resolution of the 63 false positive mismatches from PR #58 and documentation table tool extraction.
- **Related Task Specifications**:
  - [Task 86: Action Plan Contract](../../../docs/tasks/task_86_create_remediation_action_plan_for_daily_audit.md)
  - [Task 87: Implementation Contract](../../../docs/tasks/task_87_implement_and_verify_audit_remediation_plan.md)
- **Commits**:
  - Action Plan: [`0dd1af96`](https://github.com/JMartynov/mcp-fingerprints/commit/0dd1af96)
  - Implementation & Tests: [`a5f18792`](https://github.com/JMartynov/mcp-fingerprints/commit/a5f18792)
  - Clean Audit Run: [`9cc8695d`](https://github.com/JMartynov/mcp-fingerprints/commit/9cc8695d)

---

## 1. Problem Statement & Root Cause

In PR #58 (`docs/reports/daily_web_audits/runs/2026-10-27_062732.md`), the automated daily audit reported **86 discrepancies out of 87 cards**.
Our review ([`pr_58_verification_report.md`](../reviews/pr_58_verification_report.md)) determined that:
1. **63 of the discrepancies were false positives**: Packages published on PyPI or npm without an explicit top-level `repository_url` in [`web/catalog.json`](../../../web/catalog.json) (e.g. `lnbits-mcp-server` with 612 tools, `opnsense-mcp` with 537 tools, `goldbean` with 278 tools) were flagged as `CONFIRMED_ZERO_TOOLS: UNKNOWN_SOURCE` with 0 source tools, generating an artificial mismatch against their valid tool count.
2. **Missing Tools in Documentation Tables**: For documentation-heavy servers (`@zvid/mcp`, `@fruggr/zendesk-mcp-server`), tool definitions documented in Markdown tables (`README.md`, `docs/*.md`) were not ingested by the AST parser.

---

## 2. Source Code Changes & File References

The following source files were modified to resolve the discrepancies:

### 1. [`src/mcp_fingerprints/deep_zero_tool_auditor.py`](../../../src/mcp_fingerprints/deep_zero_tool_auditor.py)
- **Lines 120–165**: Added automated fallback queries to PyPI (`https://pypi.org/pypi/<pkg>/json`) and npm (`https://registry.npmjs.org/<pkg>`) APIs to extract repository URLs (`info.project_urls.Source`, `info.project_urls.Repository`, `repository.url`) when missing from catalog cards.
- **Lines 170–190**: Proper classification for unresolvable repositories. If a repository cannot be identified or reached, it is assigned `status = "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"` rather than evaluating as 0 source tools.
- **Lines 410–445**: Updated `map_audit_to_status()`:
  - Unresolved sources now map to `match_status = "UNRESOLVED_SOURCE"`, `source_tools = "?"`, and `root_cause = "UNRESOLVED_OR_MISSING_SOURCE"`.
  - Eliminates the false `MISMATCH` penalty against cards with valid tool counts.
- **Lines 200–240**: Added Markdown table extraction (`| Tool | Description |`) and OpenAPI operation ID ingestion in `inspect_file()`.

### 2. [`tests/test_audit_remediation.py`](../../../tests/test_audit_remediation.py)
- Added dedicated unit test suite covering:
  - `test_unresolved_source_mapping`: Verifies `SOURCE_UNRESOLVED` maps to `UNRESOLVED_SOURCE` and `?` tools.
  - `test_pypi_registry_fallback`: Verifies PyPI API lookups discover upstream GitHub URLs.
  - `test_npm_registry_fallback`: Verifies npm API lookups discover upstream GitHub URLs.
  - `test_markdown_table_tool_extraction`: Verifies tool parsing from README markdown tables.

---

## 3. Post-Fix Verification & Published Audit Artifacts

| Artifact Type | Path | Purpose |
|:---|:---|:---|
| **Action Plan** | [`docs/reports/daily_web_audits/plans/remediation_plan_pr58_audit.md`](../plans/remediation_plan_pr58_audit.md) | Architectural roadmap formulated in Task 86 |
| **Verification Review** | [`docs/reports/daily_web_audits/reviews/pr_58_verification_report.md`](../reviews/pr_58_verification_report.md) | Itemized analysis of PR #58 findings |
| **Post-Fix Run Report** | [`docs/reports/daily_web_audits/runs/2026-10-27_095530.md`](../runs/2026-10-27_095530.md) | Full post-fix daily audit run |
| **Historical Ledger** | [`docs/reports/daily_web_audits/master_audit_summary.md`](../master_audit_summary.md) | Master audit ledger linking the verified run |

### Verification Outcome:
- **False positive `MISMATCH` entries dropped from 63 to 0**.
- All unresolvable source packages are now correctly tagged as `UNRESOLVED_SOURCE` with `'?'` tools.
- Full pytest test suite passed: **466 passed, 5 skipped** (100% green).
