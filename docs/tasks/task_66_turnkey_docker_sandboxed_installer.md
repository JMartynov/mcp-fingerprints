# Task Contract: Task 66 — Turnkey Docker-Sandboxed Server Installer (`mcp-fingerprints install`)

## 1. Problem Statement
In the Task 7 registry & CLI ergonomics benchmark ([`docs/reports/task7_registries_hosting_cli_report.md`](../reports/task7_registries_hosting_cli_report.md) and [`docs/reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md`](../reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md)), we compared `mcp-fingerprints` against commercial registries and container runtimes (Smithery.ai `npx @smithery/cli install`, Docker MCP Catalog & Toolkit, Glama.ai, PulseMCP).

While `mcp-fingerprints` features an industry-leading **multi-client workstation scanner** (supporting 8+ clients: Claude Desktop, Cursor, Windsurf, Zed, Cline, Roo Code, Antigravity, OpenHands) and a **lossless JSONC configuration patcher** (`src/mcp_fingerprints/config_exporter.py` that preserves comments and trailing commas where Smithery's installer overwrites them), `mcp-fingerprints` currently lacks:
1. **1-Click Turnkey Server Installation (`mcp-fingerprints install <package>`)** that resolves a server's launch command and required environment variables directly from its catalog passport and injects it losslessly into the user's client configuration.
2. **OS-Level Container Sandboxing (`--sandbox docker`)** that wraps untrusted MCP servers in ephemeral, least-privilege Docker containers (`--network none`, `--read-only`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`).

**Task 66** closes both gaps by building the **Turnkey Docker-Sandboxed Server Installer (`mcp-fingerprints install`)**.

---

## 2. Technical Requirements & Deliverables

### A. Turnkey Installer & Docker Sandbox Builder (`src/mcp_fingerprints/installer.py` & `src/mcp_fingerprints/config_exporter.py`)
Create `src/mcp_fingerprints/installer.py` (and extend `src/mcp_fingerprints/config_exporter.py` as needed) with the following components:

1. **`SandboxMode` (`str, Enum`) & `NetworkPolicy` (`str, Enum`)**:
   - `SandboxMode`: `"docker"`, `"none"`.
   - `NetworkPolicy`: `"none"`, `"bridge"`.

2. **`InstallPlan` (dataclass / Pydantic model)**:
   - `server_key: str` — Normalized MCP server identifier key for `mcpServers` / `context_servers` (e.g., `"filesystem"` or `"modelcontextprotocol-server-filesystem"`).
   - `package_name: str` — Resolved package name from passport.
   - `ecosystem: str` — Ecosystem (`npm`, `pypi`, `docker`, `cargo`, `go`, etc.).
   - `command: str` — Executable command (`"docker"`, `"npx"`, `"uvx"`, `"cargo"`, etc.).
   - `args: List[str]` — Command arguments list.
   - `env: Dict[str, str]` — Placeholder or resolved environment variables from passport's `required_env_vars` (e.g., `{"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"}`).
   - `target_clients: List[str]` — Target client names (`claude`, `cursor`, `windsurf`, `zed`, `cline`, etc.).
   - `patched_files: Dict[str, str]` — Mapping of config file paths to their resulting lossless JSONC content.

3. **`DockerSandboxBuilder`**:
   - Constructs a hardened ephemeral container command (`command="docker"`, `args=[...]`) from a `ServerPackageSpec`:
     - Base isolation flags: `["run", "-i", "--rm"]`.
     - Network isolation: `["--network", network_policy.value]` (defaults to `"none"` when `--network none` is specified).
     - Filesystem hardening: appends `"--read-only"` and `["--tmpfs", "/tmp:rw,noexec,nosuid,size=64m"]` when `read_only=True`.
     - Privilege dropping: always appends `["--cap-drop=ALL", "--security-opt=no-new-privileges"]`.
     - Environment variable passthrough: for each key in `spec.required_env_vars` (or version passport env vars), appends `["-e", key]`.
     - Runtime image / entrypoint selection based on `spec.ecosystem`:
       - If `ecosystem == "docker"` or `startup_command` already specifies a Docker image: uses that image.
       - If `ecosystem in ("npm", "typescript", "javascript")`: uses `"node:20-alpine"` with `["npx", "-y", spec.package_name]`.
       - If `ecosystem in ("pypi", "python")`: uses `"ghcr.io/astral-sh/uv:python3.12-alpine"` with `["uvx", spec.package_name]`.
       - Fallback native command when `--sandbox none`: uses `"npx" [" -y", spec.package_name]` for npm, `"uvx" [spec.package_name]` for pypi, or parsed `spec.startup_command`.

4. **`ClientInstaller`**:
   - Resolves `<package_or_passport>` by file path, exact `package_name`, or slug in `data/fingerprints/` (or catalog snapshot).
   - Determines target client configuration paths (`claude`, `cursor`, `windsurf`, `zed`, `cline`, or `all` discovered clients, plus optional `--config-path <path>` override for deterministic testing).
   - Uses `config_exporter.py`'s lossless JSONC patcher to insert/update the server entry under `"mcpServers"` (or `"context_servers"` for Zed) while **preserving all existing `//` and `/* */` comments, indentation, and unrelated servers**.
   - When `dry_run=True`, computes and returns the `InstallPlan` and patched JSONC preview without modifying files on disk.

### B. CLI Subcommand (`src/mcp_fingerprints/cli.py`)
Register the `install` subcommand in `src/mcp_fingerprints/cli.py`:
```bash
mcp-fingerprints install <package_or_passport> \
  [--client claude|cursor|windsurf|zed|cline|all] \
  [--sandbox docker|none] \
  [--network none|bridge] \
  [--read-only] \
  [--dry-run] \
  [--config-path <file>]
```

### C. Comprehensive Unit Tests (`tests/test_installer.py`)
Create `tests/test_installer.py` covering:
1. **Hardened Docker Command Construction (`DockerSandboxBuilder`)**:
   - Verify `--sandbox docker --network none --read-only` generates `docker run -i --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cap-drop=ALL --security-opt=no-new-privileges` with `-e <VAR>` for required env vars and appropriate runtime image (`node:20-alpine` / `uv` / docker image).
   - Verify `--sandbox none` generates native `npx -y <pkg>` or `uvx <pkg>` commands.
2. **Lossless JSONC Patching Across Client Configs (`claude`, `cursor`, `zed`, etc.)**:
   - Create a temporary JSONC config file containing `// User comment` and `/* block comment */` plus an existing server, run `ClientInstaller.install(...)`, and verify both comments and the existing server are 100% preserved alongside the newly injected sandboxed server.
   - Verify Zed client config format (`context_servers` key) and standard MCP format (`mcpServers` key) are both handled cleanly.
3. **Dry-Run Mode & CLI Integration**:
   - Verify `mcp-fingerprints install <fixture> --client claude --sandbox docker --network none --read-only --dry-run --config-path <tmp_jsonc>` prints the planned JSONC output without mutating `<tmp_jsonc>` on disk.

---

## 3. Non-Interactive Completion Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement all specified modules, CLI wiring, and unit tests autonomously. Run `pytest tests/test_installer.py`, `pytest tests/test_live_config_scanner_tamper_drift.py`, and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
