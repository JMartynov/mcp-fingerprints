# Task 45: Dual-Transport Live Prober & Public Python Library SDK

### 1. Architectural Context & Technical Objective
Currently, `McpStdioProber` in `src/mcp_fingerprints/prober.py` exclusively communicates with MCP servers via local subprocesses over standard I/O (`stdio`). 

As the MCP ecosystem shifts toward networked microservices, SSE (Server-Sent Events), and modern Streamable HTTP endpoints (supported by Claude Code, Cursor, and enterprise gateways), `mcp_fingerprints` must natively support both transports.

The objective of Task 45 is to:
1. Implement a zero-dependency HTTP/SSE live prober (`McpHttpProber`) using Python's standard library (`urllib.request` / `http.client`).
2. Provide a unified `McpProber` interface supporting both `stdio` commands and `http` URLs.
3. Expose a clean, top-level Python SDK in `mcp_fingerprints/__init__.py` (`identify_stdio`, `identify_http`, `McpIdentifier`) for embedding into gateways, proxies, and automation harnesses.

---

### 2. Concrete Real-World Problem & Workflow (Practitioner Scenario)

* **The Practitioner**: AI Gateway engineer, security middleware author, or Python agent developer.
* **The Problem**: 
  - An engineer is building an enterprise AI proxy (or agent framework). Agents connect to remote MCP microservices hosted at URLs like `https://mcp.internal.company.com/sse`.
  - The engineer wants to verify the identity of the server, check its exposed tools, and ensure it matches an approved passport before routing LLM requests to it.
  - Spawning a CLI tool or pulling in heavy networking dependencies (like full Node.js runtimes) is unacceptable; they need a lightweight, pure-Python library they can simply `import` and run in < 20ms.
* **What the Utility Finds**:
  - Connects to the HTTP/SSE or Streamable HTTP endpoint.
  - Sends standard JSON-RPC 2.0 requests (`initialize`, `tools/list`, `prompts/list`, `resources/list`).
  - Matches the observed response against the 5,058+ passport index and returns structured attribution.
* **How It Solves the Problem**:
  - Provides a 3-line Python integration that acts as an in-memory identification filter.
  - Zero heavy external dependencies, maintaining instant startup time (< 50ms).

---

### 3. Technical Implementation Specifications

1. **Enhance `src/mcp_fingerprints/prober.py`**:
   - `McpHttpProber`:
     - Connects to remote MCP endpoints over HTTP/HTTPS.
     - Supports both standard SSE transport (reading endpoint handshake) and Streamable HTTP JSON-RPC POST.
     - Supports custom authentication headers (e.g. `Authorization: Bearer <token>`).
     - Enforces configurable timeout and graceful connection cleanup.
   - `McpProber` (Unified):
     - Automatically routes requests based on target: lists of strings (`command`) -> `McpStdioProber`, strings starting with `http://` or `https://` -> `McpHttpProber`.
2. **Public Python Library SDK (`src/mcp_fingerprints/__init__.py`)**:
   - Expose:
     - `identify_stdio(command: list[str], timeout: float = 10.0, ...) -> ProbeReport`
     - `identify_http(url: str, headers: dict[str, str] | None = None, timeout: float = 10.0, ...) -> ProbeReport`
     - `McpIdentifier(passports_dir: str | Path | None = None)` class wrapper for persistent in-memory indexing.
3. **Update CLI (`src/mcp_fingerprints/cli.py`)**:
   - Enhance `probe` / `identify` command:
     - Allow positional `cmd` OR `--url <ENDPOINT_URL>`.
     - Add `--header "Key: Value"` support for authenticated remote probing.

---

### 4. Concrete Usage Examples

#### CLI Usage
```bash
# Probe local server via stdio
mcp-fingerprints probe -- npx -y @modelcontextprotocol/server-postgres postgresql://localhost/db

# Probe remote server over HTTP/SSE
mcp-fingerprints probe --url http://localhost:8000/sse

# Probe authenticated remote endpoint
mcp-fingerprints probe --url https://api.example.com/mcp --header "Authorization: Bearer secret-token"
```

#### Python Library SDK Usage
```python
from mcp_fingerprints import identify_stdio, identify_http

# Example 1: Identify local server
local_report = identify_stdio(["npx", "-y", "@modelcontextprotocol/server-sqlite", "--db", "test.db"])
if local_report.is_identified:
    print(f"Identified: {local_report.package_name} v{local_report.version}")
    print(f"Confidence: {local_report.confidence_score:.1%}")

# Example 2: Identify remote HTTP/SSE server in a gateway
remote_report = identify_http("http://localhost:8000/sse", timeout=5.0)
if remote_report.is_identified:
    print(f"Remote Server: {remote_report.package_name} ({remote_report.repository_url})")
```

---

### 5. README Documentation Plan

Add the following section to `README.md`:

```markdown
## Python Library SDK (`mcp_fingerprints`)

Use `mcp-fingerprints` directly inside your Python applications, gateways, or agent frameworks to identify running MCP servers:

\`\`\`python
from mcp_fingerprints import identify_stdio, identify_http

# Identify a local subprocess over stdio
report = identify_stdio(["uvx", "mcp-server-git"])
print(f"Package: {report.package_name} (Confidence: {report.confidence_score:.1%})")

# Identify a remote HTTP / SSE endpoint
remote = identify_http("https://mcp.example.com/sse", headers={"Authorization": "Bearer token"})
print(f"Server: {remote.package_name} - {remote.repository_url}")
\`\`\`
```

---

### 6. Clear Acceptance Criteria & Test Plan

- [ ] `McpHttpProber` handles both Streamable HTTP JSON-RPC and SSE streams without third-party dependencies.
- [ ] Custom headers (such as Authorization tokens) are correctly injected into HTTP requests.
- [ ] Top-level `mcp_fingerprints` exports `identify_stdio`, `identify_http`, and `McpIdentifier`.
- [ ] CLI `probe` command seamlessly handles both `--url` and stdio commands.
- [ ] Mock HTTP/SSE server test fixtures in `tests/test_http_prober.py` pass with 100% reliability.
