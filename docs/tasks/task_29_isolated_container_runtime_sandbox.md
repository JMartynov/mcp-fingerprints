# Task 29: True Isolated Container Sandbox (`--probe-runtime --sandbox=docker`)

### 1. Architectural Context & Technical Objective
While `mcp_fingerprints` extracts static AST data efficiently, the current runtime probe (`probe` command) executes servers directly via `stdio` using standard library `subprocess`. Even with environment sanitization, running untrusted or closed-source MCP server binaries directly on the host poses significant security risks.
The objective is to implement a true isolated container sandbox using Docker for runtime probing. When `--sandbox=docker` is specified, the engine will dynamically construct an ephemeral container, map only the necessary stdio pipes, execute the server, and immediately destroy the container.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/sandbox_docker.py`.
2. Implement a class `DockerSandboxRunner` that implements the same interface as the current stdio runner.
3. The runner will invoke the `docker` CLI directly (via `subprocess`) rather than using the heavy `docker-py` library to minimize dependencies.
   - Example command: `docker run -i --rm --network none untrusted-mcp-image <cmd>`
4. Update the `probe` CLI command to accept `--sandbox=[host|docker]`.
5. Ensure strict timeout controls and zero network access (`--network none`) during extraction.

### 3. Clear Acceptance Criteria
- [ ] `DockerSandboxRunner` is implemented via standard `subprocess` calling the `docker` executable.
- [ ] Container runs without network access (`--network none`).
- [ ] CLI supports `--sandbox=docker`.
- [ ] Fallback to `host` runner if docker is missing or requested.

### 4. Unit Test Plan
1. **Command Generation:** Unit test that `DockerSandboxRunner` generates the exact expected `docker run` command string, specifically asserting the presence of `-i`, `--rm`, and `--network none`.
2. **Missing Docker CLI:** Mock `shutil.which('docker')` to return `None` and assert the runner raises an appropriate environment error.
3. **Timeout Handling:** Mock `subprocess.Popen` to simulate a timeout and verify the runner forcibly kills the docker process.

### 5. Live Acceptance Test Plan
Ensure Docker is running locally. Run `uv run mcp-fingerprints probe --sandbox=docker <test-server-image>`. Verify the probe successfully extracts tools and cleanly exits. Verify via `docker ps` that no lingering containers remain.
