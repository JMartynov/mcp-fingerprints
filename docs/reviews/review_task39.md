# Review Proposal: Task 39 (Sync Update Delta Tracker, What's New Web Page & PyPI Auto-Release Hardening)

**Branch:** `jules/review-4903307779422791349`  
**PR:** Task 39: Sync Update Delta Tracker, What's New Web Page (web/updates.html) & PyPI Auto-Release Hardening  
**Reviewer:** EULIS (Google Jules) Review Engine  
**Status:** Approved with Recommendations Applied  

---

## 1. Scope & Verification Criteria Audit

- **VC-39.1: Sync Update Delta Tracker Script**
  - Implemented `scripts/generate_sync_updates.py`:
    - Compares baseline/previous snapshots against new synchronizer outputs.
    - Computes discrete change badges (`NEW SERVER`, `NEW VERSION`, `+N TOOLS ADDED`, `PARAMETERS UPDATED`).
    - Emits per-version delta file `web/updates/v<version>.json`, `web/updates/latest_update.json`, and updates `web/updates/updates_history.json`.
  - Removed all residual references to `security_profile` and `risk_tier` from `generate_sync_updates.py` to maintain pure structural decoupling.
  - **Verdict:** PASSED.

- **VC-39.2: Dedicated What's New Web Page & Updates Feed**
  - Implemented `web/updates.html` and `web/updates.js`:
    - Renders only the updated MCP servers in the selected sync release.
    - Uses matching responsive card layout, interactive configuration export modal (`Claude`, `Cursor`, `Cline`, `Zed`, `Windsurf`, `Docker`), and delta badges.
    - Provides release version selector dropdown for historical releases (`v1.0.x`).
    - Provides bidirectional navigation links between `web/index.html` and `web/updates.html`.
  - Cleaned `web/style.css` and `web/updates.js` of all residual `--risk-*` CSS variables and risk badges.
  - **Verdict:** PASSED.

- **VC-39.3: Hardened Daily Sync & Automated PyPI Release Pipeline**
  - Updated `.github/workflows/daily_sync.yml`:
    - Hardened `FINGERPRINT_CHANGES` filter to ignore volatile state files (`sync_state.json`, `index.json`, `.passport_index.pickle`).
    - When structural changes occur: bumps package version (`scripts/bump_version.py --apply`), compiles web catalog, runs `generate_sync_updates.py`, commits, creates tag `v${NEW_VERSION}`, pushes, and triggers `release.yml` (`pypi-release` job) to publish to PyPI.
  - **Verdict:** PASSED.

- **VC-39.4: Unit Test Suite Coverage**
  - Created `tests/test_sync_updates_and_release.py` covering:
    - New server detection (`NEW SERVER` badge).
    - New version and added tools detection (`NEW VERSION`, `+N TOOLS ADDED` badges).
    - Tool schema mutation detection (`PARAMETERS UPDATED` badge).
    - Daily sync workflow step verification and volatile state file exclusions.
  - Test suite passes 100% locally.
  - **Verdict:** PASSED.

---

## 2. Review Findings & Applied Refinements

1. **Purged Residual Security References**:
   - Eliminated `risk_tier` calculations and badges from `generate_sync_updates.py`, `web/updates.js`, and `web/updates/v1.0.1.json`, aligning 100% with the Wave 1 & 2 structural purification mandate.
2. **Deterministic Output Formats**:
   - Formatted `web/updates/latest_update.json` to include both summary counts and server delta records for direct client consumption.

---

## 3. Test Coverage & Verification

- `PYTHONPATH=src:. python3 -m pytest tests/test_sync_updates_and_release.py -q --tb=short`: **4 passed** in 0.02s
- `PYTHONPATH=src python3 -m pytest tests/test_ci_pipeline.py -q --tb=short`: **4 passed** in 0.07s
