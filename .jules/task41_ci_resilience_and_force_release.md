# Task 41: CI Resilience, PyPI Graceful Fallback & Force-Release Support

## Objective & Scope
Harden `.github/workflows/daily_sync.yml` in `mcp-fingerprints` to ensure scheduled and manual CI runs always succeed:
1. Use `python -m pytest -v` instead of direct `pytest -v` to ensure the correct Python 3.12 environment is used.
2. Add `force_release` boolean input to `workflow_dispatch` to allow manual workflow triggers to bump version, build updates, tag, and publish releases on demand.
3. Add `continue-on-error: true` to the `pypi-release` job so PyPI Trusted Publishing OIDC validation warnings do not fail the overall workflow run.

## Target Files
1. `.github/workflows/daily_sync.yml`

## Implementation Details
1. **In `on.workflow_dispatch`**:
   ```yaml
   on:
     schedule:
       - cron: '0 4 * * *'
     workflow_dispatch:
       inputs:
         force_release:
           description: 'Force version bump and release'
           required: false
           default: false
           type: boolean
   ```
2. **In `Run Test Suite`**:
   Change:
   ```yaml
         - name: Run Test Suite
           run: |
             PYTHONPATH=src python -m pytest -v
   ```
3. **In `Commit and push updated passports & snapshot`**:
   Condition check:
   ```bash
   if [ -n "$FINGERPRINT_CHANGES" ] || [ "${{ inputs.force_release }}" = "true" ]; then
   ```
4. **In `pypi-release` job**:
   ```yaml
     pypi-release:
       needs: sync-mcp-passports
       if: needs.sync-mcp-passports.outputs.release_created == 'true'
       continue-on-error: true
       permissions:
         id-token: write
         contents: read
       uses: ./.github/workflows/release.yml
   ```
5. **Verification**:
   Run `PYTHONPATH=src python3 -m pytest tests/ -q --tb=short` and ensure all tests pass.

## Non-Interactive Completion Directive
Apply changes directly and verify. Do not prompt the user or ask open-ended questions. Cleanly transition the remote VM session to Completed.
