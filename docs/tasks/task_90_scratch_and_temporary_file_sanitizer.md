# Task Contract: Task 90 — Scratch & Temporary File Sanitizer in Worktree Gate & Git Configuration

## 1. Problem Statement & Motivation
In multiple recent Jules remote sessions (such as Task 82/PR #58 and Task 87):
- Workers created temporary scratch experiment files in the root worktree (e.g. `deep_zero_tool_auditor_extension*.py`, `mcp_audit_main.py`, `mcp_audit_test.py`, `tmp/github_test_test.json`, `tmp/sync_state.json`).
- These uncleaned files were inadvertently staged and committed to PRs and branches, requiring secondary manual or automated cleanup commits (such as commit `0998fd5c`).

This task implements automated repository-level sanitization and git exclusion rules to prevent untracked scratch files from ever being staged or committed.

---

## 2. Technical Scope & Implementation Plan

### A. Repository Git Exclusions (`.gitignore`)
1. Update `.gitignore` to explicitly ignore scratch and temporary file patterns:
   - Root scratch experiment scripts:
     `/*_scratch.py`, `/*_test.py` (root level only, preserving `tests/`), `/*_tmp.py`, `/*_debug.py`, `/scratch/`
   - Temporary JSON data files:
     `/tmp/`, `tmp/`, `*.tmp`, `*.scratch`
   - Test run cache artifacts:
     `.pytest_cache/`, `.coverage`, `coverage.xml`

### B. Pre-Commit / Pre-Verification Sanitizer Script (`bin/sanitize-scratch-files.sh`)
1. Create executable script `bin/sanitize-scratch-files.sh`:
   - Scans the repository worktree for untracked or staged scratch files outside `tests/` and `src/`.
   - Automatically removes any temporary root `.py` files matching `test_*.py`, `tmp_*.py`, `scratch_*.py`, and files in `tmp/`.
   - Returns exit code 0 on clean state.
2. In `pyproject.toml` or pre-commit hooks:
   - Wire the sanitizer script or pattern check so that local test runs and gates execute it automatically.

### C. Unit Test Validation (`tests/test_scratch_sanitizer.py`)
1. Verify that `bin/sanitize-scratch-files.sh` detects and cleans up temporary scratch files in a simulated directory.
2. Verify that valid repository files in `src/`, `tests/`, `docs/`, `data/` are never touched or deleted.

### D. Full Test Suite Verification
Run the full test suite:
```bash
PYTHONPATH=src .venv/bin/pytest -q tests/
```
Ensure 100% pass rate.

---

## 3. Strict Safety & Publication Gates
- **Domain Constraint**: Pure developer workflow hygiene and test tooling. Zero security features.
- Clean up any temporary scratch files before finishing.
- Verified test pass required prior to merge.
