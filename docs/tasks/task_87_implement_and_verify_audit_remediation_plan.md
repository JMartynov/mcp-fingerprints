# Task Contract: Task 87 — Implement & Verify Daily Audit Remediation Action Plan

## 1. Objective & Scope
Implement the technical remediations defined in the Task 86 action plan (`docs/reports/daily_web_audits/plans/remediation_plan_pr58_audit.md`) across `src/mcp_fingerprints/deep_zero_tool_auditor.py`, `src/mcp_fingerprints/doc_parser.py`, and `src/mcp_fingerprints/ast_parser.py`.

---

## 2. Implementation Scope

### A. Auditor Source Resolution & False Positive Fix (`src/mcp_fingerprints/deep_zero_tool_auditor.py`)
1. **Upstream Registry URL Resolution**:
   - For npm packages (`ecosystem == "npm"`), query `https://registry.npmjs.org/<name>` to retrieve `repository.url`.
   - For PyPI packages (`ecosystem == "pypi"`), query `https://pypi.org/pypi/<name>/json` to inspect `project_urls` (`Source`, `Repository`, `Homepage`, `Code`).
2. **Proper Unresolved Status**:
   - If no repository can be identified, assign `status: "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"`.
   - In `map_audit_to_status()`, map this to `match_status: "UNRESOLVED_SOURCE"` with `source_tools: "?"` rather than `MISMATCH` (`source_tools: 0`).

### B. Documentation Table Tool Ingestion
1. Enhance tool discovery to evaluate markdown tables when source files are unavailable or yield fewer tools than documented tables.
2. Ensure recovered tools (`@zvid/mcp`, `@fruggr/zendesk-mcp-server`) are properly extracted with name and description.

### C. Live Audit Re-Run & Verification
1. Run `./bin/run-daily-card-audit.sh` and verify:
   - False positive mismatches drop from 63 to 0.
   - Genuine matches and valid tool counts are reported accurately.
2. Add unit tests in `tests/test_audit_remediation.py` testing:
   - Unresolved source maps to `UNRESOLVED_SOURCE` (`?` tools).
   - PyPI / npm repository URL auto-resolution.
   - Markdown table tool integration.

---

## 3. Strict Safety & Publication Gates
- **Domain Constraint**: Pure metadata cataloging, AST parsing, and audit reporting. Zero security or offensive features.
- **Verification**: Run `pytest tests/test_audit_remediation.py` and full suite `pytest -q tests/`.
- Clean up any temporary scratch files before committing.
