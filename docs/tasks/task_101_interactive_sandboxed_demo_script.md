# Task 101: Build Interactive Sandboxed `demo.sh` for All 16 CLI Commands & Env Vars

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `demo.sh`, `tests/test_demo_script.py`, `docs/tasks/task_101_interactive_sandboxed_demo_script.md`
- **Category:** Developer Experience & CLI Tooling

## 1. Architectural Context & Technical Objective
The `mcp-fingerprints` repository contains 16 distinct CLI subcommands (`interactive`, `init`, `sync`, `match`, `probe`, `validate`, `snapshot`, `build-index`, `search`, `browse`, `export-config`, `export-sbom`, `validate-protocol`, `detect`, `detect-drift`, `scan-configs`) and multiple environment variable overrides (`MCP_FINGERPRINTS_DIR`, `MCP_FINGERPRINTS_INDEX`, `MCP_FINGERPRINTS_CONFIG`, `MCP_FINGERPRINTS_TIMEOUT`). 

Developers, evaluators, and CI pipelines currently lack a turnkey, self-contained demonstration script that can execute and showcase every command safely without polluting the host environment, requiring network access, or mutating production passport databases.

The objective of Task 101 is to build an interactive, fully sandboxed Bash executable script (`demo.sh`) that sets up an ephemeral `mktemp -d` sandbox, launches mock stdio and HTTP/SSE MCP servers, provides an interactive menu as well as a non-interactive `--all` mode, and guarantees 100% clean teardown on exit.

## 2. Technical Implementation Specifications

### A. Ephemeral Sandbox Architecture
- Use `SANDBOX_DIR=$(mktemp -d "${TMPDIR:-/tmp}/mcp-demo.XXXXXX")`.
- Register robust POSIX traps:
  ```bash
  trap 'cleanup' EXIT INT TERM HUP
  ```
- The `cleanup` routine must kill any background mock server processes (stdio/HTTP), flush temporary files, and remove `${SANDBOX_DIR}` completely.
- Populate sandbox with dummy minimal passports (`data/fingerprints/demo-sqlite.json`, `data/fingerprints/demo-git.json`), dummy client configs (`claude_desktop_config.json`, `cursor_config.json`, `cline_mcp_settings.json`), and baseline snapshots.

### B. Lightweight Built-in Mock MCP Servers
- **Mock stdio Server**: An inline Python script executing inside the sandbox that reads JSON-RPC 2.0 lines from stdin and writes responses to stdout:
  - Responds to `initialize` with server info and protocol version `2024-11-05`.
  - Responds to `notifications/initialized` with no-op.
  - Responds to `tools/list` returning 2 mock tools (`read_query`, `write_query`).
  - Responds to `ping` with `{}`.
- **Mock HTTP/SSE Server**: A background Python daemon utilizing standard library `http.server` / `socketserver` (no external dependencies):
  - Listens on an ephemeral localhost port (`http://127.0.0.1:$PORT`).
  - Provides SSE endpoint (`/sse`) and Streamable HTTP POST endpoint.
  - Process PID tracked in `${SANDBOX_DIR}/mock_http.pid` for guaranteed termination.

### C. Execution Modes
- **Interactive Mode (Default)**:
  - ANSI-styled terminal menu displaying all 16 CLI commands grouped by domain (Discovery & Probing, Catalog & Inspection, Export & Interop, Management & Setup).
  - Prompts user to select a command number, run all (`a`), or exit (`q`).
- **Batch Automated Mode (`--all`)**:
  - Sequentially executes every command demonstration with verification, echoing clear headers and sanitized outputs.
  - Returns exit code 0 if all demonstrations complete successfully.
- **Single Command Mode (`--command <name>`)**:
  - Executes a single specified command demonstration (e.g. `./demo.sh --command probe`).
- **Non-Interactive Flag (`--non-interactive` / `-y`)**:
  - Suppresses interactive prompts for TUI and wizard commands (`init`, `browse`, `interactive`), running them in headless/dry-run or simulated input modes.

### D. All 16 CLI Commands Demonstrated
1. `interactive` / `hub`: Interactive hub launch (with mock/dry-run input).
2. `init`: Interactive configuration bootstrap (using simulated stdin or non-interactive flags).
3. `sync`: Registry synchronization into sandbox directory.
4. `match`: Toolset and schema matching against sandbox passports using `--input-file`.
5. `probe`: Live probing over both stdio mock server and HTTP/SSE mock server endpoint.
6. `validate`: Structural invariant validation over sandbox passport directory.
7. `snapshot`: Compiling passports into `.json.gz` archive.
8. `build-index`: Building embeddings index for semantic search.
9. `search`: Querying catalog passports by keyword and capabilities.
10. `browse`: Catalog browsing (non-interactive / simulated keypress).
11. `export-config`: Generating Claude, Cursor, Cline, Zed, and Windsurf configurations.
12. `export-sbom`: Exporting CycloneDX 1.6 and SPDX 2.3 software bills of materials.
13. `validate-protocol`: Testing JSON-RPC 2.0 and MCP protocol conformance on mock server.
14. `detect`: Detecting generic command and URL endpoints.
15. `detect-drift`: Comparing baseline vs mutated passport states with `--old` and `--new`.
16. `scan-configs` / `scan`: Scanning mock client configuration files, building workstation inventory, and detecting drift.

### E. Environment Variables Demonstration
- Demonstrate overriding core environment variables:
  - `MCP_FINGERPRINTS_DIR`
  - `MCP_FINGERPRINTS_INDEX`
  - `MCP_FINGERPRINTS_CONFIG`
  - `MCP_FINGERPRINTS_TIMEOUT`
  - `NO_COLOR`

## 3. Clear Acceptance Criteria
- [ ] `demo.sh` is executable (`chmod +x demo.sh`) and runs cleanly under macOS and Linux `bash`/`zsh`.
- [ ] Ephemeral sandbox is created via `mktemp -d` and completely cleaned up upon termination.
- [ ] All 16 CLI commands are implemented and demonstrated with real invocation examples.
- [ ] Mock stdio and mock HTTP/SSE servers start on demand with zero third-party dependencies.
- [ ] Running `./demo.sh --all` executes all demonstrations non-interactively and exits with code 0.
- [ ] Running `./demo.sh --help` prints usage instructions, flags, and command list.
- [ ] `tests/test_demo_script.py` asserts `--all` exit code, output headers, and sandbox directory cleanup.

## 4. Unit Test Plan
- `tests/test_demo_script.py`:
  - `test_demo_help()`: Assert `./demo.sh --help` returns 0 and outputs all command options.
  - `test_demo_all_batch()`: Assert `./demo.sh --all` executes to completion, outputs success banners, and exits 0.
  - `test_demo_cleanup_on_signal()`: Assert SIGINT/SIGTERM cleans up sandbox directory and background PIDs.
  - `test_demo_single_command()`: Assert `./demo.sh --command probe` executes only the probe step.

## 5. Live Acceptance Test Plan
1. Execute `./demo.sh --help` and verify terminal formatting and option listing.
2. Execute `./demo.sh --all` in a clean environment with `TMPDIR` monitoring:
   - Verify no background Python processes remain (`ps aux | grep mock`).
   - Verify no temporary directories linger in `/tmp`.
3. Verify exit code: `echo $?` returns 0.
