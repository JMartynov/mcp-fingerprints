# Action Plan: 2026-11-09 Daily Audit Remediation

## 1. Root Cause Summary
- **False Positives in Markdown Extraction**: The auditor is extracting theoretical tools from design proposals (e.g. `docs/design/visimark-simulate-mcp-tool-plan.md`), leading to a false `MISSED_TOOLS` flag for `michal-niedzwiedzki/visimark`.
- **Missed JSON Addon Manifests**: Tool entries in static JSON configurations (like `aamio-addon.json` or `server.json`) aren't fully recognized if they don't exactly fit `{"tools": [...]}` in a standard named file. Need broader handling for JSON manifest file extensions / structures.
- **Missed Explicit JS/TS Registration**: Modern Explicit Tool registrations such as `server.tool(...)`, `server.registerTool(...)`, or `server.addTool(...)` in TypeScript/JavaScript aren't captured completely in the `inspect_file` TS parsing loop.

## 2. Targeted Modifications (`src/mcp_fingerprints/deep_zero_tool_auditor.py`)
1. **False-Positive Path Exclusion**: Update `secondary_patterns` in `DeepZeroToolAuditor.inspect_file` to explicitly exclude `docs/design/`, `design/`, and `"-plan.md"`.
2. **JSON Config Extraction Support**: Improve the JSON block to handle files ending in `.json` that may contain a `tools` dict/list, or specific files like `*-addon.json` / `server.json`. We will verify the `tools` key parsing.
3. **Explicit TS/JS Registrations**: Update the TS/JS regex logic in `inspect_file` to capture `server.tool(`, `server.registerTool(`, and `server.addTool(`.

## 3. Testing Strategy (`tests/test_audit_remediation_2026_11_09.py`)
- **Test 1**: Verify `docs/design/visimark-simulate-mcp-tool-plan.md` returns 0 tools (exclusion).
- **Test 2**: Verify `aamio-addon.json` and `server.json` containing `{"tools": [{"name": "test_tool"}]}` successfully returns 1 tool with format `JSON Config`.
- **Test 3**: Verify `src/index.ts` with `server.tool("my_tool", ...)` and `server.registerTool("other_tool", ...)` returns tools.
