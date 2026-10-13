# Task 29: True Isolated Container Sandbox with Dual Support for BOTH Docker and Incus (`--probe-runtime --sandbox=[auto|docker|incus|incus-vm|host]`)

### 1. Architectural Context & Technical Objective
While `mcp_fingerprints` extracts static AST data efficiently, the current runtime probe (`probe` command) executes servers directly via `stdio` using standard library `subprocess`. Even with environment sanitization, running untrusted or closed-source MCP server binaries directly on the host poses significant security risks.
The objective is to implement a true isolated container sandbox using Docker and Incus for runtime probing. When `--sandbox=[auto|docker|incus|incus-vm|host]` is specified (default `auto`), the engine will dynamically construct an ephemeral container (or microVM), map only the necessary stdio pipes, execute the server, and immediately destroy the container.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/sandbox_drivers.py`.
2. Implement a `BaseSandboxRunner` abstract base class with `run_handshake(command: list[str], timeout: float = 5.0, env: dict[str, str] | None = None) -> list[dict[str, Any]]`.
3. Implement `DockerSandboxRunner` that invokes the `docker` CLI directly via `subprocess`. Example command: `docker run -i --rm --network none --memory 512m <image> <cmd>`. Validate with `shutil.which("docker")`.
4. Implement `IncusSandboxRunner` that invokes `incus`. Example command: `incus launch docker:<image> <instance_name> --ephemeral -c limits.memory=512MB -c limits.cpu=1` and `incus exec <instance_name> -- <command>`. Support microVM with `--vm`. Validate with `shutil.which("incus")`.
5. Implement `HostSandboxRunner` executing via sanitized host stdio.
6. Implement `AutoSandboxRunner` which falls back from incus -> docker -> host.
7. Update CLI `probe` and `sync` commands to accept `--sandbox=[auto|docker|incus|incus-vm|host]`.

### 3. Clear Acceptance Criteria
- [ ] `DockerSandboxRunner` is implemented via standard `subprocess` calling the `docker` executable.
- [ ] `IncusSandboxRunner` is implemented for container and microVM execution.
- [ ] Container runs without network access (`--network none`).
- [ ] CLI supports `--sandbox=[auto|docker|incus|incus-vm|host]`.
- [ ] Fallback to `host` runner if docker is missing or requested.
- [ ] Auto-detection logic (prefers Incus/Docker when present, falls back gracefully to host).

### 4. Unit Test Plan
1. **Command Generation:** Unit test that `DockerSandboxRunner` generates the exact expected `docker run` command string, specifically asserting the presence of `-i`, `--rm`, and `--network none`.
2. **Missing Docker CLI:** Mock `shutil.which('docker')` to return `None` and assert the runner raises an appropriate environment error.
3. **Timeout Handling:** Mock `subprocess.Popen` to simulate a timeout and verify the runner forcibly kills the docker process.
4. **Incus Command Generation:** Test Incus command line construction.
5. **Auto Fallback:** Test auto-detection logic logic.

### 5. Live Acceptance Test Plan
Ensure Docker is running locally. Run `uv run mcp-fingerprints probe --sandbox=docker <test-server-image>`. Verify the probe successfully extracts tools and cleanly exits. Verify via `docker ps` that no lingering containers remain.
