# Task Contract: Task 72 — EULIS Code Review & Gap Analysis: Task 67 (TUI & Hub CycloneDX SBOM Export)

## 1. Problem Statement
In Task 67, `CycloneDXExporter` was wired into `src/mcp_fingerprints/tui.py` and `src/mcp_fingerprints/hub.py` to allow exporting Software Bills of Materials (SBOM) directly from interactive interfaces.
This review conducts a thorough audit of the implementation, evaluating:
1. What capabilities were successfully caught and verified in `tests/test_tui_hub_sbom_export.py`.
2. Edge cases, potential bugs, or missed UX requirements:
   - Behavior when a passport contains empty toolsets or legacy malformed schemas.
   - Support for format selection (CycloneDX 1.6 vs SPDX 2.3) in both TUI and Hub.
   - Configurable output directory and path collision handling.
   - Prevention of stray test files in working directory during test runs.
3. Proposing a concrete list of fixes and improvements.

## 2. Technical Deliverables
- Author comprehensive review report in `docs/reviews/review_task67.md` adhering to the standard EULIS review template:
  1. Executive Summary & Verification Findings
  2. Caught Capabilities vs Missing Features/Edge Cases
  3. Actionable List of Proposed Fixes (categorized by High/Medium/Low priority)
  4. Suggested Unit Tests to enforce invariants.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Inspect `src/mcp_fingerprints/tui.py`, `src/mcp_fingerprints/hub.py`, `src/mcp_fingerprints/sbom_exporter.py`, and `tests/test_tui_hub_sbom_export.py`. Author `docs/reviews/review_task67.md`, commit cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
