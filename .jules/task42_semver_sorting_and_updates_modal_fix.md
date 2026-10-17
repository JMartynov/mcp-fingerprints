# Task 42: Semver Sorting, Default Version Resolution, Updates Modal Fix & Delta Sync Alignment

## Objective
Fix the version resolution defect where `generate_web_catalog.py` selects the oldest release (`versions[0]`, typically `1.0.0`) instead of the true newest semver release for multi-version packages; fix `web/updates.html` where `<div id="configModal">` lacks `class="modal"` and displays open on screen; and align `generate_sync_updates.py` to compare true latest versions and update `updates_history.json` with accurate counts.

## Detailed Requirements

1. **`scripts/generate_web_catalog.py`**:
   - In `build_catalog_entry(passport: dict[str, Any])`:
     - Do NOT simply take `latest_v = versions[0]`!
     - Instead, parse and sort `passport.get("versions", [])` using `packaging.version.parse` (with safe fallback for non-semver strings: e.g. `try: parse_version(v.get("version", "0.0.0")) except Exception: parse_version("0.0.0")`) in descending order.
     - Set `latest_v` to the highest semver version.
     - Ensure `versions_data` is also ordered with the highest semver version first, so card dropdowns and inspector modal version lists present the newest release first and default to the true latest release.
   - Run `python scripts/generate_web_catalog.py` to rebuild `web/catalog.json`.

2. **`scripts/generate_sync_updates.py`**:
   - In `compute_updates`:
     - Sort `new_versions` and `old_versions` in descending semver order before picking `new_latest` and `old_latest`, ensuring version deltas accurately compare the true newest releases.
   - In `main()`:
     - When updating `history_file`:
       - If an entry for `args.version` already exists in `history`, update its `count` to `len(updates)`.
       - If it does not exist, insert `{"version": args.version, "count": len(updates)}` at index 0.
       - Write `history_file` atomically.
   - Re-run `python scripts/generate_sync_updates.py --version "1.0.1"` (or compile) and ensure `web/updates/updates_history.json` reflects actual counts.

3. **`web/updates.html`**:
   - Fix line 45: Change `<div id="configModal">` to `<div id="configModal" class="modal">` so the Combined Configuration dialog is hidden by default and only displays when opened via user action.

4. **Tests & Validation**:
   - In `tests/test_web_catalog.py`:
     - Add/update tests verifying that multi-version packages have their highest semver release selected as `version` and `latest_version`, and `versions` array is ordered from newest to oldest.
   - In `tests/test_sync_updates_and_release.py`:
     - Verify `generate_sync_updates.py` semver sorting and updates history updating.
   - Run `PYTHONPATH=src python3 -m pytest tests/ -q --tb=short` and ensure 100% pass rate.

5. **EULIS Branch Review Report**:
   - Author and commit `docs/reviews/review_task42.md` summarizing the changes, verification results, and token metrics.

## Non-Interactive Completion Directive
This task must execute entirely non-interactively. Complete all code edits, dataset regeneration, and tests directly. Do NOT ask open-ended questions or wait for human feedback. Once all changes are committed and tests pass, cleanly exit.
