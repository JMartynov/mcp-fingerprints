# Task 27: First-Class Zed, Cline & Windsurf Native Config Exporters

### 1. Architectural Context & Technical Objective
Currently, `mcp_fingerprints` primarily supports exporting client configurations for generic environments or Claude Desktop.
The objective is to expand `src/mcp_fingerprints/exporters.py` to natively support popular IDE extensions and clients like Zed, Cline, and Windsurf. These tools have specific configuration schemas (often JSONC) that require careful parsing and modification to preserve comments and structural integrity, avoiding destructive updates from standard `json.dumps`.

### 2. Technical Implementation Specifications
1. Expand `src/mcp_fingerprints/exporters.py` with specific exporter classes: `ZedExporter`, `ClineExporter`, `WindsurfExporter`.
2. Implement safe string manipulation or use a robust JSONC parsing method (if standard regex/string patching is viable as per project constraints) to inject MCP server configurations without destroying existing comments.
3. Update the CLI `export-config` command to support these new targets (e.g., `--target zed`).
4. Define the strict dictionary schemas expected by each tool based on their public documentation.

### 3. Clear Acceptance Criteria
- [ ] Exporter classes for Zed, Cline, and Windsurf exist.
- [ ] Configurations are patched safely without stripping JSONC comments.
- [ ] `export-config` CLI command supports `--target zed`, `--target cline`, `--target windsurf`.

### 4. Unit Test Plan
1. **JSONC Preservation:** Create mock JSONC strings containing comments. Pass them through the exporters and assert the output retains the comments and correctly inserts the new server config.
2. **Schema Validation:** Assert that the generated configuration dictionaries conform exactly to the known schemas of Zed, Cline, and Windsurf.
3. **CLI Integration:** Invoke the CLI runner programmatically with `--target zed` and verify it calls the correct exporter class.

### 5. Live Acceptance Test Plan
Create a dummy `zed_config.jsonc` file with comments. Run `uv run mcp-fingerprints export-config --target zed --config zed_config.jsonc --server my-server`. Open the file manually to verify comments are untouched and the new server is appended properly.
