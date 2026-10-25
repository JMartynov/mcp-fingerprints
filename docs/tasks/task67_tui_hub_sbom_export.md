# Task Contract: Task 67 — Integrate CycloneDX SBOM Export into Interactive TUI and Hub Interfaces

## 1. Problem Statement
`mcp-fingerprints` provides a high-fidelity CycloneDX 1.6 / SPDX 2.3 SBOM generator via `src/mcp_fingerprints/sbom_exporter.py` and CLI command `mcp-fingerprints export-sbom`. However, terminal operators utilizing the interactive interfaces—specifically the curses catalog browser (`src/mcp_fingerprints/tui.py`) and the terminal command hub (`src/mcp_fingerprints/hub.py`)—currently have no direct way to generate or export standard Software Bills of Materials (SBOM) for inspected MCP packages without exiting the interactive sessions.

## 2. Technical Requirements & Deliverables

### A. TUI Shortcut & Export Integration (`src/mcp_fingerprints/tui.py`)
1. **Interactive Key Binding**:
   - Bind `e` / `E` (or `b` / `B` for Bill of Materials) in `MCPCatalogBrowser.run()` when not in active search mode.
   - When triggered on the currently selected passport:
     - Prompt or default export to `export_<package_name>_cyclonedx.json` (or write to disk and report filename in status bar).
     - Instantiate `CycloneDXExporter(format=SBOMFormat.CYCLONEDX)`.
     - Convert the selected passport dict to a `ServerPackageSpec` (via `ServerPackageSpec.model_validate(p)`) and call `exporter.export_package_sbom(spec)`.
     - Write the formatted JSON to disk and set status message: `f"Exported CycloneDX SBOM to {out_path.name}"`.
     - Also support clipboard copy of the SBOM JSON or provide clean status error handling if write fails.
2. **Help Bar / Footer Display**:
   - Update footer/help text in `tui.py` to display: `[s]earch [Tab]filter [c]opy claude cfg [e]xport sbom [q]uit`.

### B. Command Hub Menu Integration (`src/mcp_fingerprints/hub.py`)
1. **Register Action**:
   - Register a new action item under category `"🌐 2. Search Ready Database & Ingest Unknown Local MCPs"`:
     - Emoji: `"📦"`
     - Title: `"Export CycloneDX 1.6 SBOM for Server / Catalog"`
     - Handler: `export_sbom_hub`
     - Order: `75` (positioned right between `browse_passports` and prober tools).
2. **Handler Implementation (`export_sbom_hub`)**:
   - Prompt user whether to export a single passport from the local database or the entire catalog snapshot.
   - Prompt for output filepath (defaulting to `./mcp_catalog_sbom.cdx.json` or `./<pkg>_sbom.cdx.json`).
   - Use `CycloneDXExporter` to generate compliant CycloneDX 1.6 JSON.
   - Print success confirmation with file path, component count, and file size.

### C. Comprehensive Automated Tests (`tests/test_tui_hub_sbom_export.py`)
1. Create `tests/test_tui_hub_sbom_export.py` verifying:
   - TUI keyboard event handling for SBOM export key without crashes in mock curses / test mode.
   - Hub action registration: category `"🌐 2. Search Ready Database & Ingest Unknown Local MCPs"` contains the registered `"📦"` SBOM export action item.
   - `export_sbom_hub` correctly writes CycloneDX 1.6 SBOM file matching `bomFormat == "CycloneDX"`.
   - Maintain 100% pass rate with zero regression across all existing suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement all specified interactive TUI bindings, hub action items, and automated tests autonomously. Run `pytest tests/test_tui_hub_sbom_export.py`, `pytest tests/test_sbom_exporter.py`, and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
