# Task 104: Align Pages Workflow Unit Test with upload-pages-artifact@v4 and Gate Push CI on Fast Unit Tests

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `tests/test_pages_workflow.py`, `.github/workflows/e2e.yml`, `docs/tasks/task_104_ci_pages_workflow_test_and_fast_unit_gate.md`, `docs/tasks/roadmap_board_specifications.md`
- **Category:** CI/CD & Quality Assurance
- **Status:** Done

## 1. Architectural Context & Technical Objective
Commit `6fb94b61` upgraded `actions/upload-pages-artifact` from `@v3` to `@v4` in both `.github/workflows/deploy_pages.yml` and `.github/workflows/daily_sync.yml`. However, `tests/test_pages_workflow.py` (line 32) was left asserting `"actions/upload-pages-artifact@v3" in uses`.

As a result, `.github/workflows/daily_sync.yml` failed during its `Run Test Suite` step (`PYTHONPATH=src python -m pytest -v -m "not integration"`) on Nov 24–26 (GitHub Actions runs `45413389496`, `45626071243`, and `45828058680`). Furthermore, this regression went undetected on push and pull request CI because `.github/workflows/e2e.yml` only executed `uv run pytest tests/test_web_pwa_e2e.py -v -m "integration"`, skipping fast unit tests.

The objective of Task 104 is to align `tests/test_pages_workflow.py` with the upgraded `@v4` GitHub Pages actions across both `.github/workflows/deploy_pages.yml` and `.github/workflows/daily_sync.yml`, and to gate push/PR CI in `.github/workflows/e2e.yml` on the fast unit test suite (`-m "not integration"`).

## 2. Technical Implementation Specifications

### A. Pages Workflow Test Alignment (`tests/test_pages_workflow.py`)
- Update `test_deploy_pages_workflow()` in `tests/test_pages_workflow.py` to assert `"actions/upload-pages-artifact@v4" in uses` (replacing the stale `@v3` assertion) alongside `"actions/deploy-pages@v4" in uses`.
- Add validation covering `.github/workflows/daily_sync.yml`'s `deploy-pages` job to verify:
  - `actions/upload-pages-artifact@v4` is present in the job's step `uses`.
  - `actions/deploy-pages@v4` is present in the job's step `uses`.
  - `concurrency.group == "pages"` is configured on the `deploy-pages` job.

### B. Push/PR Fast Unit Test Gate (`.github/workflows/e2e.yml`)
- Add a fast unit test step named `Run Fast Unit Test Suite` running `uv run pytest -v -m "not integration"` to `.github/workflows/e2e.yml` immediately before the Playwright E2E test step (`Run E2E Tests`).
- Ensure push and pull request CI fails fast whenever non-integration unit tests regress, preventing silent breakage between scheduled `daily_sync.yml` runs.

## 3. Clear Acceptance Criteria
- [x] `tests/test_pages_workflow.py` asserts `actions/upload-pages-artifact@v4` and `actions/deploy-pages@v4` in `.github/workflows/deploy_pages.yml`.
- [x] `tests/test_pages_workflow.py` verifies `.github/workflows/daily_sync.yml`'s `deploy-pages` job uses `actions/upload-pages-artifact@v4`, `actions/deploy-pages@v4`, and `concurrency.group == "pages"`.
- [x] `.github/workflows/e2e.yml` includes the `Run Fast Unit Test Suite` step (`uv run pytest -v -m "not integration"`) before the Playwright E2E step.
- [x] `uv run pytest tests/test_pages_workflow.py -v` and `uv run pytest -v -m "not integration"` pass cleanly without regressions.

## 4. Unit Test Plan
- Run `uv run pytest tests/test_pages_workflow.py -v`.
- Run `uv run pytest -v -m "not integration"` to validate the full fast unit test suite locally.
- Validate `.github/workflows/e2e.yml` YAML syntax and structure.

## 5. Live Acceptance Test Plan
1. Push the fix commit to `main` (or open a PR) and observe `.github/workflows/e2e.yml` executing `Run Fast Unit Test Suite` with green status.
2. Verify `.github/workflows/daily_sync.yml` passes its `Run Test Suite` step on the next scheduled or manually dispatched run.

## 6. Verification & CI Run Evidence
- **Implementation Commit:** `22285e9b` (`fix(ci): align pages workflow unit test with upload-pages-artifact@v4 and gate push CI on unit tests (Task 104)`)
- **Local Verification:**
  - `uv run pytest tests/test_pages_workflow.py -v`: `2 passed in 0.03s`
  - `uv run pytest -m "not integration" -q`: `562 passed, 1 skipped, 12 deselected in 92.51s`
- **GitHub Actions Verification:**
  - **`Playwright E2E Tests` (`.github/workflows/e2e.yml`, Run [`45983768561`](https://github.com/JMartynov/mcp-fingerprints/actions/runs/45983768561)):** `success` (`2m42s`). Both `Run Fast Unit Test Suite` (`1m53s`) and `Run E2E Tests` (`11s`) passed.
  - **`Deploy GitHub Pages` (`.github/workflows/deploy_pages.yml`, Run [`45983769899`](https://github.com/JMartynov/mcp-fingerprints/actions/runs/45983769899)):** `success` (`39s`).
  - **`Daily MCP Fingerprint & Passport Sync` (`.github/workflows/daily_sync.yml`, Run [`45983774823`](https://github.com/JMartynov/mcp-fingerprints/actions/runs/45983774823)):** `Run Test Suite` **passed** (`2m04s`), confirming Task 104 resolved the Nov 24–26 unit test regression. *(Note: the 4-day catch-up sync later failed in `Commit and push updated passports & snapshot` due to a newly uncovered separate blocker: `web/catalog.json` reached `101.30 MB`, exceeding GitHub's `100.00 MB` file size limit [`GH001`].)*
