# Task 106: Untrack `web/catalog.json` from Git and Build Dynamically in CI

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `.gitignore`, `.github/workflows/daily_sync.yml`, `.github/workflows/e2e.yml`, `tests/test_catalog_size_guard.py`, `bin/run-daily-card-audit.sh`, `scripts/resolve_hub_urls.py`, `docs/tasks/task_106_untrack_web_catalog.md`, `docs/tasks/roadmap_board_specifications.md`
- **Category:** CI/CD & Repository Hygiene
- **Status:** In Progress

## 1. Architectural Context & Technical Objective
Even after Task 105 slimmed historical `versions` entries in `web/catalog.json`, the compiled file remains `~46.64 MiB` (`48,902,783` bytes) — dangerously close to GitHub's `50 MB` (`52,428,800` bytes) warning threshold and `100 MB` (`GH001`) hard push limit. Moreover, committing a 46.64 MiB JSON artifact on every daily passport sync bloats Git object history, slows clones/pushes, and creates recurring maintenance risk as the passport corpus grows beyond 3,900+ servers.

`web/catalog.json` is a purely derived build artifact generated deterministically from `data/fingerprints/*.json` via `scripts/generate_web_catalog.py`. Note that `.github/workflows/deploy_pages.yml` already runs `PYTHONPATH=src:. python scripts/generate_web_catalog.py` before uploading the Pages artifact, whereas `.github/workflows/daily_sync.yml`, `.github/workflows/e2e.yml`, local scripts, and tests still assume `web/catalog.json` is tracked in Git.

The objective of Task 106 is to untrack `web/catalog.json` from Git (`git rm --cached web/catalog.json` + `.gitignore`) and generate it dynamically on-demand in CI workflows (`e2e.yml`, `daily_sync.yml`, alongside existing `deploy_pages.yml`) and local tooling, while:
- Keeping `$0` GitHub Free tier budget (standard GitHub Actions runners and GitHub Pages artifacts, no paid LFS/storage add-ons).
- Making **zero changes** to `web/app.js`, `web/index.html`, `web/sw.js`, or `passports.json.gz`.

## 2. Technical Implementation Specifications

### A. Untrack & Ignore Derived Web Catalog (`.gitignore`, Git Index)
- Remove `web/catalog.json` from Git tracking without deleting the local working file (or keeping local generation optional): `git rm --cached web/catalog.json`.
- Add `web/catalog.json` to `.gitignore` so regenerated local or CI build artifacts are never accidentally staged or committed.

### B. Dynamic Catalog Generation in CI Workflows (`.github/workflows/daily_sync.yml`, `.github/workflows/e2e.yml`)
- **`.github/workflows/daily_sync.yml`**:
  - Remove `web/catalog.json` from `git add` in `Commit and push updated passports & snapshot` (both the standard sync `git add` and the release bump `git add`). Keep `scripts/generate_web_catalog.py` running in `Compile Consolidated Snapshot & Web Catalog` (and on version bump if needed for downstream update scripts/verification), without committing `web/catalog.json`.
  - In the `deploy-pages` job (which checks out `main` fresh with `actions/checkout@v4`), install minimal Python dependencies and run `PYTHONPATH=src:. python scripts/generate_web_catalog.py` before `actions/upload-pages-artifact@v4` so the deployed GitHub Pages artifact always contains the freshly built `web/catalog.json`.
- **`.github/workflows/e2e.yml`**:
  - Run `PYTHONPATH=src:. uv run python scripts/generate_web_catalog.py` dynamically in the CI job before the catalog size guard, unit tests, and Playwright E2E tests (`tests/test_web_pwa_e2e.py`).
  - Preserve the catalog size budget check (`Guard web/catalog.json size` or equivalent check against generated output) so Pages bundle bloat is still caught early.
- **`.github/workflows/deploy_pages.yml`**:
  - Already generates `web/catalog.json` via `PYTHONPATH=src:. python scripts/generate_web_catalog.py` prior to `actions/upload-pages-artifact@v4`; keep unchanged (or verify trigger compatibility).

### C. Local Scripts & Size Guard Test Compatibility
- **`tests/test_catalog_size_guard.py`**:
  - Update `test_web_catalog_under_50mb()` so it does not fail when `web/catalog.json` is absent on a clean untracked checkout (e.g., guard/skip or validate when present, or test generated catalog size safely without requiring a committed `web/catalog.json`), while keeping `daily_sync.yml` and `e2e.yml` workflow contract assertions aligned with the updated dynamic-build steps.
- **`bin/run-daily-card-audit.sh`**:
  - Ensure `web/catalog.json` is generated on-demand (e.g., via `PYTHONPATH=src:. uv run python scripts/generate_web_catalog.py` if missing or before audit execution) prior to invoking `python3 -m mcp_fingerprints.deep_zero_tool_auditor --catalog web/catalog.json`.
- **`scripts/resolve_hub_urls.py`**:
  - Guard `update_catalog(resolved_map)` when `web/catalog.json` does not exist on disk (skip gracefully or only update if `web/catalog.json` is present) so hub URL resolution on `data/fingerprints/*.json` never crashes with `FileNotFoundError` in a clean checkout.

### D. Strict Non-Modification Invariants
- Zero edits to `web/app.js`, `web/index.html`, `web/sw.js`, or `passports.json.gz`.
- Zero paid GitHub services or Git LFS usage (`$0` GitHub Free budget).

## 3. Clear Acceptance Criteria
- [ ] `web/catalog.json` is untracked from Git (`git ls-files web/catalog.json` returns empty) and listed in `.gitignore`.
- [ ] Zero modifications made to `web/app.js`, `web/index.html`, `web/sw.js`, and `passports.json.gz`.
- [ ] `.github/workflows/daily_sync.yml`, `.github/workflows/e2e.yml`, `tests/test_catalog_size_guard.py`, `bin/run-daily-card-audit.sh`, and `scripts/resolve_hub_urls.py` work cleanly without a committed `web/catalog.json`.
- [ ] `uv run pytest -v -m "not integration"` and `uv run ruff check src tests` pass locally.
- [ ] CI workflows (`.github/workflows/e2e.yml` and `.github/workflows/deploy_pages.yml`) pass on GitHub Actions with `$0` GitHub Free budget.

## 4. Unit Test Plan
- Verify `git ls-files web/catalog.json` is empty and `git check-ignore web/catalog.json` matches `.gitignore`.
- Run `uv run pytest -v -m "not integration"`.
- Run `uv run ruff check src tests`.
- Run `tests/test_catalog_size_guard.py` and `tests/test_web_catalog.py` both with and without a pre-existing `web/catalog.json` file on disk.

## 5. Live Acceptance Test Plan
1. Push changes to `main` (or open a PR) and verify `.github/workflows/e2e.yml` builds `web/catalog.json` dynamically and passes all unit + Playwright E2E checks.
2. Verify `.github/workflows/deploy_pages.yml` builds `web/catalog.json` dynamically and deploys a working catalog to GitHub Pages.
3. Verify `.github/workflows/daily_sync.yml` commits passport/snapshot updates without staging `web/catalog.json`, and its `deploy-pages` job generates and publishes `web/catalog.json`.
