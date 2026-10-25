# Review Proposal: Task 36 (Security Module Purge & Pure CLI/TUI Refactoring)

**Branch:** `jules/review-task36`  
**PR:** Task 36: Security Module Purge & Pure CLI/TUI Refactoring  
**Reviewer:** EULIS (Google Jules) Review Engine  
**Status:** Approved with Recommendations Applied  

---

## 1. Scope & Verification Criteria Audit

- **VC-36.1: Purge Legacy Security Analysis Modules**
  - Completely purged all 6 legacy security modules from `src/mcp_fingerprints/`:
    - `security_classifier.py`
    - `conflict_detector.py`
    - `conflict_resolver.py`
    - `sarif_exporter.py`
    - `sandbox_drivers.py`
    - `sbom.py`
  - Preserved essential helper `extract_package_from_server_config` by cleanly migrating it to `src/mcp_fingerprints/drift_detector.py`.
  - **Verdict:** PASSED.

- **VC-36.2: Purge Associated Documentation, Actions & Tests**
  - Purged 4 doc and GitHub Action/hook workflow files:
    - `docs/SECURITY_AUDIT.md`
    - `action.yml`
    - `.pre-commit-hooks.yaml`
    - `.github/workflows/test_action.yml`
  - Purged 7 obsolete test files:
    - `tests/test_security_classifier.py`
    - `tests/test_conflict_detector.py`
    - `tests/test_conflict_resolver.py`
    - `tests/test_sarif_exporter.py`
    - `tests/test_sandbox_containers.py`
    - `tests/test_sbom.py`
    - `tests/test_action_and_hooks.py`
  - Cleaned `.pre-commit-config.yaml` to eliminate local `mcp-audit-config` hook dependency.
  - **Verdict:** PASSED.

- **VC-36.3: Pure CLI & TUI Refactoring**
  - Refactored `src/mcp_fingerprints/cli.py` to remove deprecated subcommands (`audit-config`, `resolve-config`, `sbom`) and removed the dead `--sandbox` flag.
  - Refactored `src/mcp_fingerprints/tui.py` to remove security profile references, security badges, and risk displays, replacing them with clean package metadata and `author` information.
  - Decoupled `src/mcp_fingerprints/prober.py` and `src/mcp_fingerprints/synchronizer.py` from `sandbox_drivers`.
  - Decoupled `scripts/generate_web_catalog.py` from `security_classifier`.
  - Updated `tests/test_cli_runtime_probe.py` to mock `PassportSynchronizer` instead of `sandbox_drivers`.
  - **Verdict:** PASSED.

---

## 2. Review Findings & Applied Refinements

1. **AST Parser Robustness**:
   - Refined `_extract_balanced_braces` in `src/mcp_fingerprints/ast_parser.py` to correctly parse nested `z.object({...})` schemas and prevent premature truncation.
   - Enhanced `FastMcpAstVisitor` in `src/mcp_fingerprints/ast_parser.py` to accurately capture `BaseTool`/`Tool` class declarations, Pydantic `args_schema` resolution, and `@tool_manager.register(...)` decorators.
2. **Architecture Decoupling**:
   - Verified that `mcp-fingerprints` is now fully decoupled from issue scanning and security classification (offloaded to Verity MCP Auditor), focusing purely on structural AST fingerprinting, passport schemas, and drift detection.

---

## 3. Test Coverage & Verification

- Full test suite: **247 passed, 5 skipped, 0 failed** in 64.31s across all active test suites.
