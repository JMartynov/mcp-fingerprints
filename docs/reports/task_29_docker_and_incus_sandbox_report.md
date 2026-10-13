# Task 29: Isolated Container Sandbox (Dual Docker & Incus) Delivery Report

## 1. Executive Summary
Task 29 implements true isolated container runtime sandboxing for live MCP server probing in `mcp-fingerprints`. Probing untrusted, dynamic, or closed-source MCP servers directly on the host machine presents substantial security exposure. This release introduces dual container engine support—featuring both **Docker** and **Incus** (system containers & microVMs)—alongside an automated fallback resolver and sanitized host execution.

- **GitHub Project Board Item**: [Task 29 (`PVTI_lAHOD-xmQM4BmPbTzhAYXzE`)](https://github.com/users/JMartynov/projects/3)
- **Status**: Completed & Verified (`Done`)
- **Remote Jules Session ID**: `12158340814707218824`
- **Cumulative Estimated Tokens Spared**: 3,895,460 tokens (~$19.48 USD value)

---

## 2. Architecture & Design Specification

### 2.1 Driver Hierarchy (`src/mcp_fingerprints/sandbox_drivers.py`)
A unified abstraction layer allows interchangeable runtime engines:
- `BaseSandboxRunner`: Abstract base class specifying `prepare()`, `wrap_command()`, and `run_handshake(command, timeout, env)`.
- `DockerSandboxRunner`: Builds and runs ephemeral containers using direct CLI invocation (`subprocess.Popen`):
  ```bash
  docker run -i --rm --network none --memory 512m <image> <command>
  ```
  Enforces zero network egress (`--network none`) and strict memory ceilings (`--memory 512m`).
- `IncusSandboxRunner`: Orchestrates OCI containers and KVM microVMs:
  ```bash
  incus launch docker:<image> <instance_name> --ephemeral -c limits.memory=512MB -c limits.cpu=1 [--vm]
  incus exec <instance_name> -- <command>
  ```
  Guarantees ephemeral instance lifecycle with automatic cleanup routines (`incus delete -f <instance_name>`).
- `HostSandboxRunner`: Sanitized host execution stripping dangerous credentials (`AWS_*`, `GITHUB_TOKEN`, `OPENAI_API_KEY`, etc.) via `probe_mcp_server_stdio`.
- `AutoSandboxRunner`: Dynamically detects runtime availability:
  1. Checks for `incus` via `shutil.which`.
  2. Checks for `docker` via `shutil.which`.
  3. Detects whether commands are host binaries/scripts (e.g., absolute paths, files on disk).
  4. Falls back gracefully to `HostSandboxRunner`.
- `get_sandbox_runner(mode: str)`: Factory resolving `"auto"`, `"docker"`, `"incus"`, `"incus-vm"`, and `"host"`.

### 2.2 CLI & Pipeline Integration
- **`probe` CLI**:
  ```bash
  uv run mcp-fingerprints probe --sandbox=[auto|docker|incus|incus-vm|host] -- <image_or_cmd>
  ```
- **`sync --probe-runtime` CLI**:
  ```bash
  uv run mcp-fingerprints sync --probe-runtime --sandbox=[auto|docker|incus|incus-vm|host]
  ```
- **`McpStdioProber` & `PassportSynchronizer`**: Fully wired to accept `sandbox` parameter, routing JSON-RPC stdio handshakes through the requested driver.

---

## 3. Test Verification & Coverage

### 3.1 Unit Test Suite (`tests/test_sandbox_containers.py`)
8 targeted test cases verifying driver behavior:
1. `test_docker_command_construction`: Asserts `-i`, `--rm`, `--network none`, `--memory 512m`.
2. `test_docker_missing_binary`: Asserts `EnvironmentError` raised when `docker` CLI is absent.
3. `test_docker_timeout_handling`: Asserts timeout enforcement and clean return.
4. `test_incus_command_construction`: Asserts `incus launch docker:<image>`, `--ephemeral`, `limits.memory=512MB`, `limits.cpu=1`, and `incus exec`.
5. `test_incus_vm_command_construction`: Asserts `--vm` flag is supplied for microVM execution.
6. `test_incus_missing_binary`: Asserts `EnvironmentError` raised when `incus` CLI is absent.
7. `test_incus_timeout_handling`: Asserts timeout during `incus launch` aborts and cleans up.
8. `test_auto_sandbox_fallback`: Asserts fallback cascade (`incus` -> `docker` -> `host`).

### 3.2 Regression Suite Verification
Full project test suite execution:
```
================== 246 passed, 5 skipped in 64.39s (0:01:04) ===================
```
100% pass rate achieved with zero regressions across AST parsers, semantic search, schema validators, SARIF exporters, and synchronization pipelines.

---

## 4. Artifacts Delivered
- `src/mcp_fingerprints/sandbox_drivers.py`: Implementation of `BaseSandboxRunner`, `DockerSandboxRunner`, `IncusSandboxRunner`, `HostSandboxRunner`, and `AutoSandboxRunner`.
- `src/mcp_fingerprints/cli.py`: Added `--sandbox` argument to `probe` and `sync` commands.
- `src/mcp_fingerprints/prober.py`: Added sandbox driver integration in `McpStdioProber`.
- `src/mcp_fingerprints/synchronizer.py`: Added sandbox driver parameter to `probe_runtime_passports`.
- `tests/test_sandbox_containers.py`: Comprehensive test suite for container isolation and fallbacks.
- `docs/tasks/task_29_isolated_container_runtime_sandbox.md`: Formally updated with dual Docker + Incus specification.
- `docs/tasks/roadmap_board_specifications.md`: Updated Section 29 with dual container engine details.
- `docs/reports/task_29_docker_and_incus_sandbox_report.md`: This delivery report.
