# Task 103: Update `README.md` with Complete CLI Options, Environment Variables & Real Outputs

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `README.md`, `docs/SPECIFICATION.md`, `docs/tasks/task_103_readme_cli_reference_and_live_outputs.md`
- **Category:** Documentation & Developer Experience

## 1. Architectural Context & Technical Objective
Accurate, authoritative documentation is critical for adoption and developer trust. Currently, `README.md` contains several syntax discrepancies with the real CLI implementation (notably in `match`, `detect-drift`, and `validate`), omits complete descriptions of several format flags (such as `--format text`), lacks documentation for environment variable overrides, and uses mock outputs that do not perfectly match the live outputs produced by `src/mcp_fingerprints/reporter.py` and `src/mcp_fingerprints/cli.py`.

The objective of Task 103 is to update `README.md` and `docs/SPECIFICATION.md` with an exhaustive, 100% verified CLI reference covering all 16 subcommands, their real arguments and exit codes, all supported environment variables, and real terminal output snippets captured directly from live sandbox runs.

## 2. Technical Implementation Specifications

### A. Correction of CLI Discrepancies
- **`match` Command**:
  - Replace legacy `python -m mcp_fingerprints.cli match <hash>` with actual syntax:
    ```bash
    # Match observed runtime tools from JSON manifest against knowledge base
    python -m mcp_fingerprints.cli match --input-file tools.json --threshold 0.8
    # Match tools passed via stdin
    cat tools.json | python -m mcp_fingerprints.cli match --input-file - --json
    ```
- **`detect-drift` Command**:
  - Replace inaccurate `python -m mcp_fingerprints.cli detect-drift <config_file>` with correct passport drift syntax:
    ```bash
    # Compare baseline snapshot or directory against latest passports
    python -m mcp_fingerprints.cli detect-drift --old baseline.json.gz --new data/fingerprints --fail-on-tamper
    ```
- **`scan-configs` Command**:
  - Clearly document workstation configuration drift tracking (`--save-baseline` and `--diff`), distinguishing it from catalog passport drift (`detect-drift`).
- **`validate` Command**:
  - Accurately document `--dir DIR`, `--no-cache`, and `--workers N`.
- **`probe` Command**:
  - Exhaustively document dual transports: stdio command line (`probe <cmd>`) and remote endpoint (`probe --url http://localhost:8000/sse`), plus all format styles (`--format text`, `--format json`, `--format short`, `--format long`).

### B. Complete 16-Command Reference Matrix
Add a structured summary table and dedicated subsection for each command:
1. `interactive` / `hub`: Interactive MCP Command Hub.
2. `init`: Interactive setup wizard.
3. `sync`: Multi-registry passport synchronization.
4. `match`: Toolset AST and parameter matching.
5. `probe`: Stdio and HTTP/SSE live capability probing.
6. `validate`: Passport schema and invariant validation.
7. `snapshot`: Consolidated gzip database compilation.
8. `build-index`: Semantic embeddings vector index build.
9. `search`: Fuzzy keyword and capability search.
10. `browse`: Interactive terminal TUI browser.
11. `export-config`: Client config generation (Claude, Cursor, Cline, Zed, Windsurf).
12. `export-sbom`: Software Bill of Materials (CycloneDX 1.6 / SPDX 2.3).
13. `validate-protocol`: JSON-RPC 2.0 & MCP protocol conformance validator.
14. `detect`: Generic MCP server and URL detector.
15. `detect-drift`: Supply-chain tamper and hash drift detector.
16. `scan-configs`: Workstation MCP client discovery and inventory.

### C. Environment Variables Reference
Document all supported environment variables with descriptions, default values, and example usage:
- `MCP_FINGERPRINTS_DIR`: Custom path to passport directory (defaults to package data or `data/fingerprints`).
- `MCP_FINGERPRINTS_INDEX`: Custom path to embeddings cache.
- `MCP_FINGERPRINTS_CONFIG`: Custom path to CLI configuration file.
- `MCP_FINGERPRINTS_TIMEOUT`: Probing and network timeout in seconds (default: 30).
- `NO_COLOR`: Disables ANSI color codes across all formatted reports.

### D. Live Verified Terminal Outputs
- Execute each command inside the sandbox from Task 101 and capture actual live stdout.
- Embed the real terminal outputs into `README.md` code blocks (e.g. `probe --format text`, `probe --format short`, `probe --format long`, `detect`, `scan-configs`).
- Ensure all command flags, keys, and values in code blocks match actual tool outputs with 100% fidelity.

### E. Quickstart with Sandboxed `demo.sh`
- Add a Quickstart subsection introducing `demo.sh`:
  ```bash
  # Run the interactive sandboxed CLI tour
  ./demo.sh

  # Or execute all 16 command demonstrations non-interactively
  ./demo.sh --all
  ```

## 3. Clear Acceptance Criteria
- [ ] `README.md` contains accurate syntax for all 16 CLI commands with zero obsolete argument patterns.
- [ ] Discrepancies in `match`, `detect-drift`, `validate`, and `probe` are completely resolved.
- [ ] All environment variables (`MCP_FINGERPRINTS_*`, `NO_COLOR`) are clearly documented.
- [ ] Code block output snippets in `README.md` reflect real, verified outputs generated from live execution.
- [ ] Links in table of contents and documentation hub remain fully valid.

## 4. Unit Test Plan
- Run markdown link checker and doctest or automated script validation on code blocks if available.
- Verify CLI examples in `README.md` can be run through `bash` without syntax errors.

## 5. Live Acceptance Test Plan
1. Review `README.md` rendered preview.
2. Manually test every code snippet in `README.md` inside a clean terminal session to ensure zero argument errors.
3. Validate that git diff against `README.md` cleanly addresses all discrepancies.
