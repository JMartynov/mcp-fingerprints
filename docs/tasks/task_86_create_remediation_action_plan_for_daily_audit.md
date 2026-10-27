# Task Contract: Task 86 — Action Plan: Remediation of Daily Web Cards Audit Discrepancies & False Positives

## 1. Context & Motivation
Following the daily audit in PR #58 (`docs/reports/daily_web_audits/runs/2026-10-27_062732.md`) and our verification report (`docs/reports/daily_web_audits/reviews/pr_58_verification_report.md`), two primary classes of issues were identified:
1. **Auditor Engine False Positives (63 Servers)**: Packages without direct top-level GitHub URLs in `catalog.json` (such as `lnbits-mcp-server`, `opnsense-mcp`, `goldbean`) were misclassified as `CONFIRMED_ZERO_TOOLS: UNKNOWN_SOURCE` with 0 source tools, generating artificial mismatches against valid catalog tool counts.
2. **Missing Tool Extraction Gaps (4 Servers)**: Packages where tool signatures reside in Markdown documentation tables (`@zvid/mcp`, `giorgio44/gateonai-mcp-server`, `@fruggr/zendesk-mcp-server`) or complex OpenAPI wrappers (`@jrpool/kilotest`) were missed or undercounted.

This task formulates the comprehensive, prioritized architectural action plan to resolve both the auditor false positives and the tool extraction gaps.

---

## 2. Deliverables & Output Invariant
Jules must author the detailed remediation plan at:
`docs/reports/daily_web_audits/plans/remediation_plan_pr58_audit.md`

The plan must define:
1. **Remediation Item 1: Auditor Source Resolution & False Positive Elimination**:
   - Fix `DeepZeroToolAuditor.audit()` in `src/mcp_fingerprints/deep_zero_tool_auditor.py`:
     - When `repository_url` is absent or not a GitHub URL, query PyPI (`https://pypi.org/pypi/<pkg>/json`) and npm (`https://registry.npmjs.org/<pkg>`) APIs to extract repository URLs (`project_urls.Source`, `project_urls.Repository`, `repository.url`).
     - If upstream source is genuinely unresolvable, return `status: "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"` with `source_tools: "?"` and `match_status: "UNRESOLVED_SOURCE"`, instead of claiming 0 source tools.
2. **Remediation Item 2: Documentation Table Fallback Extraction**:
   - Enhance the audit and synchronization pipeline to incorporate Markdown table tool signatures (`doc_parser.py`) when AST code parsing yields fewer tools than the documented reference.
3. **Remediation Item 3: OpenAPI Wrapper Complement**:
   - Ingest operation IDs from `openapi.yaml` / `openapi.json` alongside AST-registered tools.
4. **Implementation & Verification Roadmap**:
   - Breakdown of exact functions to update, unit test contracts, and acceptance criteria for Task 87.

---

## 3. Strict Safety & Publication Gates
- **Domain Constraint**: Pure metadata cataloging, AST parsing, and audit reporting. Zero security or offensive features.
- **Report-Only Publishing**: Commit only the plan under `docs/reports/daily_web_audits/plans/`. Clean up any temporary scratch files.
