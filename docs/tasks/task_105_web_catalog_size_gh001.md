# Task 105: Slim Historical Version Tools in `web/catalog.json` to Prevent GH001 100 MB Push Limit Failure

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `scripts/generate_web_catalog.py`, `tests/test_web_catalog.py`, `web/catalog.json`, `docs/tasks/task_105_web_catalog_size_gh001.md`, `docs/tasks/roadmap_board_specifications.md`
- **Category:** CI/CD & Web Catalog Optimization
- **Status:** Done

## 1. Architectural Context & Technical Objective
`.github/workflows/daily_sync.yml` run [`45983774823`](https://github.com/JMartynov/mcp-fingerprints/actions/runs/45983774823) failed during `Commit and push updated passports & snapshot` with GitHub remote rejection `GH001: Large files detected`: `web/catalog.json` reached `101.30 MB`, exceeding GitHub's `100.00 MB` per-file push limit.

The root cause is in `scripts/generate_web_catalog.py` (`build_catalog_entry()`):
1. `versions[0]` (the latest version) duplicates the entire top-level `tools` array (full descriptions, annotations, and parameter schemas), even though `web/app.js` (`getVersionData()`) and `scripts/normalize_catalog_tools.py` (`normalize_server_item()`) fall back to top-level `item.tools` when `found.tools` is omitted.
2. Every historical entry in `versions[1:]` also embeds complete `tools` payloads (`description`, `annotations`, `parameters`), inflating `web/catalog.json` linearly with version history.

The objective of Task 105 is to deduplicate the latest version's `tools` payload from `versions[0]` and slim historical `versions[1:]` tool entries to `name` and `canonical_hash` only, keeping the frontend (`web/app.js`) working seamlessly while reducing `web/catalog.json` well below 100 MB.

## 2. Technical Implementation Specifications

### A. Catalog Deduplication & Historical Version Slimming (`scripts/generate_web_catalog.py`)
- In `build_catalog_entry()`:
  - Keep the full `tools` array (with `name`, `description`, `canonical_hash`, `annotations`, `parameters`) on the top-level catalog entry for the latest version.
  - For `versions[0]` (the latest version entry in `versions`), omit the redundant `tools` key while preserving `tool_count`, `version`, `release_date`, `transports`, `required_env_vars`, `connection_type`, and `command`. Both `web/app.js` (`getVersionData`) and `scripts/normalize_catalog_tools.py` automatically resolve latest-version tools from top-level `entry["tools"]`.
  - For historical versions (`versions[1:]`), retain `tools` as a slim list of `{"name": ..., "canonical_hash": ...}` dictionaries (preserving `tool_count` and empty `[]` when a historical version had zero tools so `getVersionData` does not fall back to latest tools).

### B. Unit Test Contract (`tests/test_web_catalog.py`)
- Add unit tests verifying:
  - Latest-version entry in `versions[0]` omits `"tools"` while retaining `tool_count` and top-level `entry["tools"]` retains full tool metadata (`description`, `parameters`, `annotations`, `canonical_hash`).
  - Historical entries in `versions[1:]` retain slim `tools` containing only `name` and `canonical_hash` (without `description`, `parameters`, `annotations`), and zero-tool historical versions retain `"tools": []`.
  - Regenerated `web/catalog.json` remains strictly below 80 MB (well under GitHub's 100 MB limit).

## 3. Clear Acceptance Criteria
- [x] `scripts/generate_web_catalog.py` omits duplicate `tools` from `versions[0]` and slims historical `versions[1:]` `tools` to `name` and `canonical_hash`.
- [x] `tests/test_web_catalog.py` enforces the slimmed `versions` contract and size safety threshold.
- [x] Regenerated `web/catalog.json` is well below 100 MB and `uv run pytest -m "not integration"` + `uv run ruff check src tests` pass.
- [x] `.github/workflows/daily_sync.yml`, `.github/workflows/e2e.yml`, and `.github/workflows/deploy_pages.yml` all pass on CI.

## 4. Unit Test Plan
- Run `uv run pytest tests/test_web_catalog.py tests/test_web_catalog_normalizer.py -v`.
- Run `uv run pytest -m "not integration" -q`.
- Run `uv run ruff check src tests`.

## 5. Live Acceptance Test Plan
1. Push updated `scripts/generate_web_catalog.py`, tests, and regenerated `web/catalog.json` to `main`, and verify `e2e.yml` (including Playwright E2E) and `deploy_pages.yml` pass.
2. Manually dispatch `.github/workflows/daily_sync.yml` and verify `sync-mcp-passports` (including `Commit and push updated passports & snapshot`), `pypi-release`, and `deploy-pages` all succeed without `GH001`.

## 6. Verification & CI Run Evidence
- **Commits:**
  - `817ba5eb`: `docs(tasks): add Task 105 spec for web/catalog.json GH001 size fix`
  - `b8f61d3a`: `test(web): add failing unit test contract for Task 105 slimmed versions`
  - `712e8139`: `chore(aider): apply task task_105_fix changes` (DeepSeek via `aider_bridge.py`, `$0.0042` USD)
  - `4793cf06`: `chore(web): regenerate slimmed web/catalog.json for Task 105`
  - `6e569c63`: `chore(release): bump version to v1.4.20 and sync MCP fingerprints` (automated `daily_sync.yml` commit & push)
- **Catalog Size Reduction:**
  - Before: `98.44 MB` locally (`101.30 MB` during failed `daily_sync.yml` run `45983774823`)
  - After regeneration (`4793cf06`): `45.50 MB` (`47,710,960` bytes)
  - After `v1.4.20` catch-up sync (`6e569c63`): `46.59 MB` (`48,852,367` bytes)
- **Local Verification:**
  - `uv run pytest tests/test_web_catalog.py -v`: `26 passed in 0.09s`
  - `uv run pytest -m "not integration" -q`: `564 passed, 1 skipped, 12 deselected in 93.07s`
- **GitHub Actions Verification:**
  - **`Deploy GitHub Pages` (`.github/workflows/deploy_pages.yml`, Run [`45997579848`](https://github.com/JMartynov/mcp-fingerprints/actions/runs/45997579848)):** `success` (`34s`).
  - **`Playwright E2E Tests` (`.github/workflows/e2e.yml`, Run [`45997579968`](https://github.com/JMartynov/mcp-fingerprints/actions/runs/45997579968)):** `success` (`3m1s`).
  - **`Daily MCP Fingerprint & Passport Sync` (`.github/workflows/daily_sync.yml`, Run [`45997591293`](https://github.com/JMartynov/mcp-fingerprints/actions/runs/45997591293)):** `success` across `sync-mcp-passports` (including `Commit and push updated passports & snapshot`), `pypi-release`, and `deploy-pages` (`25s`).
