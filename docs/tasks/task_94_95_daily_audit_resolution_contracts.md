# Task 94: Verification Report & Action Plan for Daily Report 2026-10-29 (PR #68)

> **Issue**: [#69](https://github.com/JMartynov/mcp-fingerprints/issues/69)  
> **Target Run**: `docs/reports/daily_web_audits/runs/2026-10-29_063053.md` (PR #68)  
> **Workflow Standard**: `docs/tasks/task_88_daily_audit_ai_workflow_and_resolution_protocol.md`

## 1. Objectives & Context
In the daily run `2026-10-29_063053.md`:
- **Total Cards Verified**: 87
- **Findings Breakdown**:
  - `PERFECT_MATCH`: 2
  - `UNRESOLVED_SOURCE`: 53 (missing upstream GitHub URLs on package cards)
  - `MISMATCH`: 4 (`api-auto-mcp-server`, `data-olympus`, `privacyfence`, `ssh-mcp`)
  - `MISSED_TOOLS`: 18 (servers where tool definitions were flagged in Markdown tables across non-README or secondary doc files: `CHANGELOG.md`, `ROADMAP.md`, `MIGRATION.md`, `.cursor/skills/`)

## 2. Requirements & Deliverables

### Phase 2: Verification Report
Author `docs/reports/daily_web_audits/reviews/2026-10-29_verification_report.md`:
1. Item-by-item verification across the 87 audited cards.
2. Triage of the 4 `MISMATCH` entries:
   - `data-olympus` & `privacyfence`: The cards contain Smithery URLs (`https://smithery.ai/servers/...`). While the auditor has a PyPI fallback, `data-olympus` and `privacyfence` need their GitHub URLs resolved cleanly or classified as external gateway sources.
   - `ssh-mcp` & `api-auto-mcp-server`: Verify upstream tool definitions against the repository.
3. Triage of the 18 `MISSED_TOOLS` entries:
   - Identify why `doc_parser.py` / `inspect_file` flagged doc tables in secondary files (`CHANGELOG.md`, `ROADMAP.md`, `MIGRATION.md`) that may contain changelog versions, historical entries, or roadmaps rather than active MCP tools.
   - Establish that documentation parsing should prioritize primary tool definitions (e.g. `README.md`, `docs/tools.md`) and avoid falsely aggregating changelog tables or skill definitions into total tool counts.

### Phase 3: Action Plan Authoring
Author `docs/reports/daily_web_audits/plans/2026-10-29_remediation_plan.md`:
1. Technical specifications to refine markdown table extraction:
   - Ignore `CHANGELOG.md`, `MIGRATION.md`, `ROADMAP.md`, and hidden tool directories (e.g. `.cursor/`) when searching for active server tools in documentation.
   - Refine PyPI/npm URL resolution for Smithery-hosted packages.
2. Re-indexing mandate for any newly recovered tool definitions.
3. Test acceptance criteria.

---

# Task 95: Implement Auditor Enhancements, Re-Index Affected Passports & Publish Fix Report for 2026-10-29

> **Issue**: [#70](https://github.com/JMartynov/mcp-fingerprints/issues/70)  
> **Prerequisites**: Task 94 completed.

## Objectives & Deliverables
1. **Implementation**:
   - Refine `src/mcp_fingerprints/deep_zero_tool_auditor.py` and `src/mcp_fingerprints/doc_parser.py`.
   - Filter out changelog/migration/roadmap files from tool discovery.
2. **Passport Re-Indexing (Phase 4 Step 3 Mandate)**:
   - Run `src/mcp_fingerprints/reindex_sdk_passports.py` or re-index any affected passports under `data/fingerprints/`.
   - Update `data/.passport_cache.json`.
3. **Unit Tests**:
   - Add unit tests in `tests/` validating doc table filtering and URL resolution.
   - Ensure `PYTHONPATH=src .venv/bin/pytest -q tests/` passes 100%.
4. **Phase 5 Fix Summary Report**:
   - Author `docs/reports/daily_web_audits/fixes/2026-10-29_daily_audit_remediation_fix_report.md` with:
     - Direct file links and line ranges to modified files.
     - Passport Delta Summary table.
     - Before-vs-after metrics comparison.
