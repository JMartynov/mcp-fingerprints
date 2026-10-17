# Task 42: Semver Sorting, Default Version Resolution, Updates Modal Fix & Edge-Case Test Synthesis

## Objective
Verify, harden, and synthesize comprehensive edge-case tests for the semver sorting and version resolution logic in `scripts/generate_web_catalog.py` and `scripts/generate_sync_updates.py`, ensure the Combined Configuration modal in `web/updates.html` remains properly styled with `class="modal"`, and update documentation and tests.

## Detailed Requirements

1. **Verify & Harden Version Parsing (`scripts/generate_web_catalog.py` & `scripts/generate_sync_updates.py`)**:
   - Inspect `_safe_version_key` in both scripts. Ensure it gracefully handles:
     - Standard semver strings (`1.0.0`, `1.0.11`, `1.2.0`).
     - Pre-release / build metadata tags (`1.0.0-beta.1`, `2.0.0-rc.2`).
     - Non-standard or malformed version strings (e.g. `"latest"`, `None`, empty string, non-numeric strings), falling back safely without crashing.
   - Verify that `versions_data` in `generate_web_catalog.py` is ordered with the highest semver release first.

2. **Verify Modal Styling (`web/updates.html`)**:
   - Confirm `<div id="configModal" class="modal">` has `class="modal"` so it stays hidden by default on page load.

3. **Synthesize Edge-Case Unit Tests**:
   - In `tests/test_web_catalog.py`:
     - Add edge-case tests for `_safe_version_key` and `build_catalog_entry`:
       - Pre-release versions comparison (e.g. `1.0.0` vs `1.0.0-alpha`).
       - Malformed version strings (e.g. `{"version": "dev-build"}` vs `{"version": "1.0.0"}`).
       - Passports with empty `versions: []` list.
   - In `tests/test_sync_updates_and_release.py`:
     - Add edge-case test for version delta detection with multiple semver versions.

4. **Test Suite Verification**:
   - Run `PYTHONPATH=src python3 -m pytest tests/test_web_catalog.py tests/test_sync_updates_and_release.py -v`.
   - Ensure 100% of tests pass.

5. **Review Documentation**:
   - Update `docs/reviews/review_task42.md` summarizing the verified logic and synthesized tests.

## Non-Interactive Completion Directive
This task must execute entirely non-interactively. Complete all code edits, dataset verification, and tests directly. Do NOT ask open-ended questions or wait for human feedback. Once all changes are committed and tests pass, cleanly exit.
