# Task 43: Local Machine MCP Config Discovery & Interactive Inventory (`scan-configs`)

### 1. Architectural Context & Technical Objective
Developers, security analysts, and IT administrators run multiple AI-assisted developer environments (Claude Desktop, Cursor, Windsurf, Zed, Cline, VS Code) that connect to local and remote MCP servers via configuration files. 

Currently, `mcp_fingerprints` only probes individual commands supplied on the CLI. The objective of Task 43 is to implement an automated local configuration discovery engine (`src/mcp_fingerprints/config_scanner.py`) and CLI command (`scan-configs`) that traverses the host filesystem, discovers all declared MCP client configurations, probes the active servers, identifies them against the passport knowledge base, and outputs both a clean human-readable report and a structured JSON schema inventory.

---

### 2. Concrete Real-World Problem & Workflow (Practitioner Scenario)

* **The Practitioner**: Full-stack developer, AppSec engineer, or DevOps lead on macOS/Linux/Windows.
* **The Problem**: Over months of building AI-assisted workflows, the user configured dozens of MCP servers across Claude Desktop (`claude_desktop_config.json`), personal Cursor (`~/.cursor/mcp.json`), and various project repositories (`.cursor/mcp.json`). They have completely lost track of what MCP servers are installed, what tools they expose to AI agents, where they originated from, or if some are deprecated or broken.
* **What the Utility Finds**:
  - Locates all configuration files across standard OS paths and git repositories.
  - Detects each declared server name, transport (`stdio` or `http`), command/arguments, and environment variables.
  - Probes live servers to extract runtime tool contracts and matches them against the 5,058+ passport catalog (identifying packages like `@modelcontextprotocol/server-postgres` or `mcp-server-git`).
* **How It Solves the Problem**:
  - Provides a single one-line command to catalog and audit all local MCP assets.
  - Emits an instant human-readable terminal table and a consolidated JSON file of the local MCP schema inventory.

---

### 3. Technical Implementation Specifications

1. **Create `src/mcp_fingerprints/config_scanner.py`**:
   - `ClientConfigLocator`: Discovers configuration files across platforms:
     - **Claude Desktop**:
       - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
       - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
       - Linux: `~/.config/Claude/claude_desktop_config.json`
     - **Cursor IDE**:
       - Global: `~/.cursor/mcp.json`
       - Project-level: `.cursor/mcp.json` (scanned in current working directory and parent git roots)
     - **Windsurf / Zed / Cline / VS Code**:
       - Standard paths in `~/.codeium/windsurf/mcp_config.json`, `~/.config/zed/settings.json`, etc.
   - `ConfigScanner`:
     - Parses JSON configurations and extracts `mcpServers` dictionary.
     - Supports optional live probing (`probe_live=True`) to perform the JSON-RPC handshake for each discovered server using `McpStdioProber` and `McpHttpProber`.
     - Compiles `LocalInventoryReport` containing server specifications, detected capabilities, and fingerprint matches.
2. **Update CLI (`src/mcp_fingerprints/cli.py`)**:
   - Add subcommand `scan-configs`:
     - `--path <FILE_OR_DIR>`: Scan a specific configuration file or directory.
     - `--auto`: Automatically search all standard system paths for known clients (default if no path specified).
     - `--probe-live`: Actively launch/connect to each declared server to verify live schemas (default: True).
     - `--format [table|json|markdown]`: Output formatting option.
     - `--output <FILE>`: Save full inventory report to a JSON file.
3. **Public Python API**:
   - Expose `scan_local_configs()` and `scan_config_file(path)` from `mcp_fingerprints`.

---

### 4. Concrete Usage Examples

#### CLI Usage
```bash
# Automatically scan all local clients and print an audit table
mcp-fingerprints scan-configs --auto

# Scan a specific Cursor project configuration and export JSON inventory
mcp-fingerprints scan-configs --path .cursor/mcp.json --output local-inventory.json
```

#### Python Library SDK Usage
```python
from mcp_fingerprints import scan_local_configs

# Scan all local configurations and probe servers
inventory = scan_local_configs(probe_live=True)

for server in inventory.servers:
    print(f"[{server.client_name}] {server.server_name}: {server.package_name or 'Custom'} ({server.version or 'unknown'})")
    print(f"  Tools: {', '.join(t.name for t in server.tools)}")
```

---

### 5. README Documentation Plan

Add the following section to `README.md`:

```markdown
## Workstation MCP Inventory & Discovery

Audit and catalog all MCP servers configured on your local machine across Claude Desktop, Cursor, Windsurf, and Zed:

\`\`\`bash
# Audit all local configurations and display terminal summary table
mcp-fingerprints scan-configs --auto

# Export structured JSON schema inventory of all local MCPs
mcp-fingerprints scan-configs --output mcp-inventory.json
\`\`\`

**Python SDK:**
\`\`\`python
from mcp_fingerprints import scan_local_configs

inventory = scan_local_configs(probe_live=True)
print(f"Discovered {len(inventory.servers)} active MCP servers.")
\`\`\`
```

---

### 6. Clear Acceptance Criteria & Test Plan

- [ ] `ClientConfigLocator` correctly resolves default paths for Claude Desktop and Cursor across OS environments.
- [ ] `scan-configs` parses standard `mcpServers` JSON structures with command/args and url/headers.
- [ ] Probing matches identified packages against `passports.json.gz`.
- [ ] CLI supports `--format table`, `--format json`, and `--output <path>`.
- [ ] Unit tests in `tests/test_config_scanner.py` with mock configuration files pass with 100% coverage.
