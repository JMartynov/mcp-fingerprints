# Task Contract: Task 77 — TUI & Hub SBOM Exporter Hardening (SPDX 2.3 & UX Resilience)

## 1. Problem Statement
Based on the code review findings in `docs/reviews/review_task67.md`, the TUI and Hub SBOM export integrations in `src/mcp_fingerprints/tui.py` and `src/mcp_fingerprints/hub.py` require hardening:
1. **SPDX 2.3 Format Selection**: Users are currently restricted to CycloneDX 1.6. Operators need the ability to export SPDX 2.3 JSON as well:
   - In Hub: prompt the operator to choose between CycloneDX 1.6 (`.cdx.json`) and SPDX 2.3 (`.spdx.json`).
   - In TUI: bind `x` / `X` to export SPDX 2.3 format (in addition to `e` for CycloneDX 1.6).
2. **Directory Creation Safety**: Ensure `out_path.parent.mkdir(parents=True, exist_ok=True)` is called in `hub.py` prior to writing files to prevent `FileNotFoundError` when nested directories are specified.
3. **Clipboard Failure Resilience**: In `tui.py`, wrap clipboard operations so that a missing system clipboard (e.g., headless Linux / SSH) does not mask a successful file write.
4. **Clean Test Isolation**: Ensure `tests/test_tui_hub_sbom_export.py` cleans up all temporary output files and does not leave stray JSON in `tmp/`.

## 2. Technical Deliverables
- Update `src/mcp_fingerprints/hub.py`:
  - `export_sbom_hub`: Add format selection (`CycloneDX 1.6` vs `SPDX 2.3`) and parent directory creation safety.
  - Update menu action title: `"📦 Export CycloneDX / SPDX SBOM for Server or Catalog"`.
- Update `src/mcp_fingerprints/tui.py`:
  - Bind `x` / `X` for SPDX 2.3 export.
  - Update footer help text: `[s]earch [Tab]filter [c]opy [e]xport cdx [x]port spdx [q]uit`.
  - Isolate clipboard exception handling.
- Update `tests/test_tui_hub_sbom_export.py` covering all enhancements with 100% pass rate.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement the fixes in `src/mcp_fingerprints/hub.py` and `src/mcp_fingerprints/tui.py`, update `tests/test_tui_hub_sbom_export.py`, run `pytest tests/test_tui_hub_sbom_export.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
