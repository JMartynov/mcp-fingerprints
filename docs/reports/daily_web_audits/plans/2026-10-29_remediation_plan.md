# Phase 3 Remediation Action Plan - 2026-10-29

## Problem Statement
The daily audit from `2026-10-29` identified severe tool count inflation in 18 repositories (categorized as `MISSED_TOOLS`) due to the indiscriminate parsing of markdown tables across secondary documentation files (e.g., `CHANGELOG.md`, `ROADMAP.md`, `MIGRATION.md`, `.cursor/skills/`). Additionally, 4 `MISMATCH` entries occurred partially because the auditor failed to resolve correct GitHub repositories from PyPI metadata when the primary `repository_url` pointed to a registry hub (e.g., `smithery.ai` or `glama.ai`) instead of a direct GitHub link.

## Technical Specifications (Phase 4)

1. **Refine Markdown Table Extraction (`src/mcp_fingerprints/deep_zero_tool_auditor.py` & `src/mcp_fingerprints/doc_parser.py`)**:
   - Update `inspect_file` and relevant path traversal logic to explicitly skip non-primary markdown files.
   - Ignore patterns must include: `CHANGELOG.md`, `MIGRATION.md`, `ROADMAP.md`, `HISTORY.md`, `OPTIMIZATIONS.md`, `.cursor/`, `releases/`, and `changes/` when scanning for tool documentation.
   - Prioritize tool extraction from primary documentation files: `README.md`, `docs/tools.md`, and `docs/api.md`.

2. **Refine URL Resolution (`src/mcp_fingerprints/deep_zero_tool_auditor.py` or URL resolution modules)**:
   - Enhance the URL parsing/resolution logic to actively inspect PyPI and npm package metadata when the provided `repository_url` points to hubs like Smithery (`smithery.ai`) or Glama (`glama.ai`) rather than a direct GitHub repository.
   - Ensure the resolved URL accurately points to the upstream source code repository for structural AST/doc analysis.

3. **Passport Re-Indexing Mandate (Task 95)**:
   - Upon deploying the extraction and resolution refinements, all affected SDK passports under `data/fingerprints/` must be re-indexed using `src/mcp_fingerprints/reindex_sdk_passports.py` or a targeted re-indexing script.
   - Update `data/.passport_cache.json` accordingly.

4. **Test Acceptance Criteria**:
   - **Regression Tests (`tests/test_deep_zero_tool_auditor.py`)**:
     - Test that markdown tables in `CHANGELOG.md` or `.cursor/` are ignored.
     - Test that markdown tables in `README.md` and `docs/tools.md` are correctly parsed.
     - Test URL resolution correctly fallback to PyPI/npm project URLs when the main repo URL is a smithery.ai link.
   - All tests must pass: `PYTHONPATH=src .venv/bin/pytest -q tests/`.
   - The daily run script (`./bin/run-daily-card-audit.sh`) must produce 0 false positive `MISMATCH` errors and no inflated `MISSED_TOOLS` from changelogs upon re-execution.
