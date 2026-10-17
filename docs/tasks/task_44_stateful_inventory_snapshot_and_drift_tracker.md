# Task 44: Stateful Inventory Snapshot & Differential Drift Tracker

### 1. Architectural Context & Technical Objective
Once a user has determined their local MCP server inventory (from Task 43), they need to track how this landscape evolves over time. 

The objective of Task 44 is to implement a stateful snapshot persistence and differential comparison engine (`src/mcp_fingerprints/snapshot_diff.py`). It enables saving the determined local machine schema inventory to a versioned snapshot file (e.g. `mcp-inventory.json`) and comparing subsequent scans against this baseline to report newly added servers, uninstalled servers, and schema/version drift.

---

### 2. Concrete Real-World Problem & Workflow (Practitioner Scenario)

* **The Practitioner**: Security auditor, developer maintaining team repository standards, or DevOps engineer.
* **The Problem**: 
  - A developer pulled updates from their team's git repository, and a teammate modified `.cursor/mcp.json` to add a new third-party MCP server.
  - Or an existing server package was updated (`latest`), and a tool description or parameter was changed, breaking agent workflows or exposing unintended capabilities.
  - The developer has no automated way to detect: *"What changed in my local MCP environment since yesterday?"*
* **What the Utility Finds**:
  - Compares the baseline snapshot (`mcp-inventory.json`) with a live scan.
  - Identifies:
    - ➕ **Added Servers**: New MCP servers that were not previously present.
    - ➖ **Removed Servers**: Servers that were deleted or disabled.
    - 🔄 **Drifted Contracts**: Servers where tool contracts mutated (tools added, tools dropped, parameter schema changes, description shifts).
    - ⬆ **Version Upgrades**: Changes in detected package release versions.
* **How It Solves the Problem**:
  - Acts as a local drift gate and change tracker.
  - Prevents unexpected MCP modifications from creeping into workflows unnoticed.
  - Can be added to local pre-commit hooks or CI/CD pipelines to fail when unauthorized MCP drift occurs.

---

### 3. Technical Implementation Specifications

1. **Create `src/mcp_fingerprints/snapshot_diff.py`**:
   - `InventorySnapshot`:
     - Serializes and deserializes local inventory schemas to versioned JSON (`snapshot_version: "1.0.0"`).
     - Records timestamp, host identifier, client configurations scanned, and server signatures.
   - `InventoryDiffer`:
     - Compares two `InventorySnapshot` instances (baseline vs. target/current).
     - Computes:
       - `added_servers: list[DiscoveredServer]`
       - `removed_servers: list[DiscoveredServer]`
       - `modified_servers: list[ServerDriftDetail]`
       - `schema_drift_count: int`
2. **Update CLI (`src/mcp_fingerprints/cli.py`)**:
   - Extend `scan-configs` (or add `inventory` subcommand):
     - `--save-snapshot <FILE>`: Save current scan as baseline snapshot (default: `.mcp-inventory.json`).
     - `--compare-snapshot <FILE>`: Compare current scan against a previous baseline snapshot.
     - `--fail-on-drift`: Exit with non-zero status code (exit 2) if schema drift or unexpected additions are detected (ideal for CI/CD).
     - `--format [summary|detailed|json]`: Formats drift output.
3. **Public Python API**:
   - Expose `compare_snapshots(baseline, current)` and `save_inventory_snapshot(inventory, path)`.

---

### 4. Concrete Usage Examples

#### CLI Usage
```bash
# Save initial baseline snapshot
mcp-fingerprints scan-configs --auto --save-snapshot mcp-baseline.json

# (Later) Audit against baseline to detect changes
mcp-fingerprints scan-configs --auto --compare-snapshot mcp-baseline.json

# CI/CD Gate: Fail build if local MCP servers drifted
mcp-fingerprints scan-configs --compare-snapshot mcp-baseline.json --fail-on-drift
```

#### Sample Terminal Output
```text
======================================================================
               LOCAL MCP INVENTORY DRIFT REPORT
======================================================================
Baseline Snapshot: mcp-baseline.json (Captured: 2026-10-15 14:22:01)
Current Scan:      2026-10-17 20:00:36 (5 servers observed)

➕ ADDED SERVERS (1):
  • [Cursor] github-tools -> @modelcontextprotocol/server-github (v0.6.0)

➖ REMOVED SERVERS (0):
  (None)

🔄 MODIFIED / DRIFTED SERVERS (1):
  • [Claude] postgres -> @modelcontextprotocol/server-postgres
    - Version: 0.6.1 -> 0.6.2 (Upgraded)
    - Toolset Canonical Hash: Drifted (9a8f... -> 4b2c...)
    - Tool Contract Mutations:
      * 'read_query': Parameter 'timeout_ms' added (type: integer, optional)
======================================================================
Result: 1 server added, 1 server drifted.
```

#### Python Library SDK Usage
```python
from mcp_fingerprints import scan_local_configs, compare_snapshots, InventorySnapshot

# Load saved baseline
baseline = InventorySnapshot.load_file("mcp-baseline.json")

# Perform current scan
current = scan_local_configs(probe_live=True)

# Compute differential drift
diff = compare_snapshots(baseline, current)

if diff.has_changes:
    print(f"Drift detected! Added: {len(diff.added_servers)}, Modified: {len(diff.modified_servers)}")
    for mod in diff.modified_servers:
        print(f"Server {mod.server_name} drifted: {mod.changes}")
```

---

### 5. README Documentation Plan

Add the following section to `README.md`:

```markdown
## Tracking Local MCP Drift & Run-to-Run Changes

Establish a baseline of your local MCP tools and catch unauthorized modifications, accidental package upgrades, or tool contract drift:

\`\`\`bash
# 1. Establish baseline snapshot of your local environment
mcp-fingerprints scan-configs --auto --save-snapshot .mcp-baseline.json

# 2. Check for drift on subsequent runs
mcp-fingerprints scan-configs --auto --compare-snapshot .mcp-baseline.json

# 3. Use in pre-commit hooks or CI to block drifted configurations
mcp-fingerprints scan-configs --compare-snapshot .mcp-baseline.json --fail-on-drift
\`\`\`
```

---

### 6. Clear Acceptance Criteria & Test Plan

- [x] `InventorySnapshot` correctly serializes all server tool contracts, hashes, and client origins.
- [x] `InventoryDiffer` identifies added, removed, and modified servers accurately.
- [x] Parametric mutations (added parameters, type changes, description shifts) are surfaced in detail.
- [x] `--fail-on-drift` flag properly returns exit code 2 when differences are found, exit code 0 when identical.
- [x] Unit tests in `tests/test_snapshot_diff.py` pass with comprehensive mock diff fixtures.
