# EULIS Code Review & Gap Analysis: Task 67 (TUI & Hub CycloneDX SBOM Export)

## 1. Executive Summary & Verification Findings
Task 67 implemented CycloneDX SBOM export capabilities directly from interactive interfaces (`src/mcp_fingerprints/tui.py` and `src/mcp_fingerprints/hub.py`). This review evaluates the completeness of the implementation against EULIS standards, identifying edge cases, unhandled features, and potential bugs. 

Overall, the feature allows exporting CycloneDX 1.6 from the TUI (single package) and Hub (single package or entire catalog) via the `CycloneDXExporter`. The core exporting functionality is tested in `tests/test_tui_hub_sbom_export.py`.

## 2. Caught Capabilities vs Missing Features/Edge Cases

### Caught Capabilities
- **TUI Integration**: Added `e` / `b` keybinding to export CycloneDX SBOM for the selected package.
- **Hub Integration**: Added "Export CycloneDX 1.6 SBOM for Server / Catalog" action to the `ActionRegistry` under the Search/Database category.
- **Test Coverage**: Basic test coverage is present in `tests/test_tui_hub_sbom_export.py`, verifying the Hub action exists, Hub export for entire catalog succeeds, and TUI keybinding triggers export.

### Missing Features / Edge Cases / Bugs

**1. Missing Format Selection (CycloneDX vs SPDX):**
- In `tui.py`: The export format is hardcoded to `SBOMFormat.CYCLONEDX`. The user has no capability to choose SPDX 2.3.
- In `hub.py`: The export format is hardcoded to `SBOMFormat.CYCLONEDX`, and the menu action explicitly states "Export CycloneDX 1.6 SBOM...". The Hub user is not offered an SPDX alternative despite `CycloneDXExporter` supporting it.

**2. Output Path & Directory Collisions:**
- In `tui.py`: The output path is hardcoded as `export_{pkg_name}_cyclonedx.json` in the current working directory. It silently overwrites existing files.
- In `hub.py`: Allows prompting for output filepath, but defaults to `./mcp_catalog_sbom.cdx.json` or `./{pkg_name}_sbom.cdx.json`. Does not handle creating parent directories for the provided path, meaning `out_path.write_text()` will raise `FileNotFoundError` if a nested path is given (e.g. `out/sbom.cdx.json`).

**3. Passports with Empty Toolsets / Missing Versions:**
- The exporter `CycloneDXExporter._get_latest_version` will return `None` if `spec.versions` is empty. The Hub handles this without crashing, but might export a completely empty SBOM component list if no passports have valid versions. The Hub loader (`Entire Catalog Snapshot` mode) also ignores exceptions silently when parsing `json.loads`.

**4. Error Handling & State Recovery:**
- `tui.py`: Handles exceptions generically, printing `Export error: {e}` to status, which is mostly fine but `copy_to_clipboard` might fail if `xclip` or similar is missing, raising a sub-exception that obfuscates the original SBOM generation error.

## 3. Actionable List of Proposed Fixes

### High Priority
- **H1: Enable Format Selection (SPDX 2.3 vs CycloneDX 1.6) in Hub**: Update the `export_sbom_hub` menu in `hub.py` to prompt the user for the desired output format (`CycloneDX` or `SPDX`) before executing the export. Adjust file extensions accordingly (`.cdx.json` or `.spdx.json`).
- **H2: Enable Format Selection in TUI**: In `tui.py`, map a specific key to export SPDX (e.g., `x`), while `e` exports CycloneDX. Update the footer to indicate `[x]port spdx`.
- **H3: Directory Creation in Hub Export**: Ensure `out_path.parent.mkdir(parents=True, exist_ok=True)` is called in `hub.py` before `out_path.write_text()` to prevent errors when users specify nested output paths.

### Medium Priority
- **M1: Update Hub Menu Action Title**: Rename "Export CycloneDX 1.6 SBOM for Server / Catalog" to "Export SBOM for Server / Catalog (CycloneDX / SPDX)" in `setup_default_registry`.
- **M2: Robust Clipboard Copy Handling**: In `tui.py`, wrap `copy_to_clipboard(sbom_str)` in a specific `try/except` block so that if the clipboard utility is missing, it still successfully informs the user that the file was saved.

### Low Priority
- **L1: Warn on Overwrite**: Both TUI and Hub should ideally warn if the target file already exists, though safely creating the parent dir is more critical.

## 4. Suggested Unit Tests to Enforce Invariants
- Add a test in `tests/test_tui_hub_sbom_export.py` to verify that selecting SPDX in the Hub exports `spdxVersion: SPDX-2.3` (or equivalent structure).
- Add a test for `hub.py` where a nested output path (`some/deep/dir/out.json`) is provided, ensuring `mkdir` successfully runs and the file is created.
- Add a test in `tests/test_tui_hub_sbom_export.py` simulating the `x` key for SPDX export in TUI.
