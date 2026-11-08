# Task 102: Live Verification of All CLI Commands, Options & Exit Codes

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `tests/test_demo_script.py`, `tests/test_cli_live_sandbox.py`, `tests/test_live_cli_sandbox_invariants.py`
- **Category:** Quality Assurance & Invariant Verification

## 1. Architectural Context & Technical Objective
While the codebase maintains extensive unit tests, CLI commands undergo frequent option evolution and flag refactoring. Discrepancies between documented options and actual CLI argument parsers can cause silent breakage or user confusion. 

The objective of Task 102 is to author and execute a comprehensive live test suite that verifies every one of the 16 CLI subcommands, their argument combinations, formatting flags (`--format text`, `--format json`, `--format short`, `--format long`), and expected exit codes against real sandboxed processes and mock servers.

## 2. Technical Implementation Specifications

### A. Subprocess Sandboxing & Test Matrix
- Author automated tests in `tests/test_demo_script.py` and `tests/test_cli_live_sandbox.py`.
- Each test runs inside an isolated `tmp_path` fixture populated with fixture passports and mock configurations.
- Validate the following test matrix across all 16 commands:
  1. `interactive` / `hub`: verify invocation with mocked stdin or `--help`, exit code 0.
  2. `init`: verify non-interactive bootstrap creates valid config file, exit code 0.
  3. `sync`: verify dry-run or targeted sync into temporary directory, exit code 0.
  4. `match`: verify `--input-file` containing mock tools matches passport, exit code 0; invalid JSON exits with code 1 or 2.
  5. `probe`: verify stdio probing against mock server with `--format text`, `--format json`, `--format short`, and `--format long`, exit code 0; verify `--url` against mock HTTP/SSE server, exit code 0.
  6. `validate`: verify validation passes on valid passport directory, exits 0; fails with exit code 1 on malformed schema.
  7. `snapshot`: verify compiling passports to `.json.gz` produces valid gzip archive, exit code 0.
  8. `build-index`: verify building embeddings index produces searchable vector cache, exit code 0.
  9. `search`: verify search returns expected match for known passport keyword, exit code 0; `--json` produces valid JSON array.
  10. `browse`: verify headless/non-interactive invocation handling or help screen, exit code 0.
  11. `export-config`: verify client config export for `claude`, `cursor`, `cline`, `zed`, `windsurf`, exit code 0.
  12. `export-sbom`: verify SBOM generation with `--format cyclonedx` and `--format spdx`, exit code 0.
  13. `validate-protocol`: verify protocol validation against mock stdio server passes with exit code 0; fails with non-zero exit code on non-MCP process.
  14. `detect`: verify generic command detection on mock server returns positive detection, exit code 0; non-MCP command returns negative result with exit code 0.
  15. `detect-drift`: verify comparison of baseline vs identical state produces zero drift, exit code 0; comparison against tampered state exits code 1 with `--fail-on-tamper`.
  16. `scan-configs`: verify scanning mock config files discovers servers, `--save-baseline` writes inventory, `--diff` detects changes, exit code 0.

### B. Exit Code & Error Handling Invariants
- Exit code 0: Command succeeded cleanly.
- Exit code 1: Operational failure, schema invariant breach, or detected tamper under `--fail-on-tamper`.
- Exit code 2: Command-line argument syntax error (`argparse` default).
- Ensure stderr contains actionable human-readable messages rather than raw Python tracebacks for expected failures.

### C. Environment Variable Overrides Verification
- Test `MCP_FINGERPRINTS_DIR`: redirects default passport discovery path.
- Test `MCP_FINGERPRINTS_INDEX`: redirects vector index path.
- Test `MCP_FINGERPRINTS_CONFIG`: redirects configuration file path.
- Test `MCP_FINGERPRINTS_TIMEOUT`: enforces connection and probing timeouts.
- Test `NO_COLOR`: suppresses ANSI color codes in formatted outputs.

## 3. Clear Acceptance Criteria
- [ ] `tests/test_demo_script.py` and `tests/test_cli_live_sandbox.py` pass cleanly under `pytest`.
- [ ] Every one of the 16 CLI commands is tested with real subprocess execution.
- [ ] Formatting flags (`--format text`, `--format json`, `--format short`, `--format long`) are validated for output schema conformance.
- [ ] Exit codes 0, 1, and 2 are systematically asserted for normal and error conditions.
- [ ] Environment variable overrides (`MCP_FINGERPRINTS_*`) are proven to redirect paths and change behaviors.
- [ ] Zero background processes or temporary files leaked during test runs.

## 4. Unit Test Plan
- Run `pytest tests/test_demo_script.py -v`.
- Run `pytest tests/test_cli_live_sandbox.py -v`.
- Assert 100% of CLI test cases pass.

## 5. Live Acceptance Test Plan
1. Execute `pytest tests/test_demo_script.py tests/test_cli_live_sandbox.py`.
2. Inspect test output logs for zero deprecation warnings or unhandled exceptions.
3. Verify that `/tmp` contains no leftover artifacts post-run.
