# Task Contract: Task 62 — Implement Remedies for Zero-Tool Servers (JSON Manifests, Alternative Decorators & Dynamic Array Resolution)

## 1. Problem Statement
The Task 61 audit ([`docs/reports/audit_zero_tools_deep_research.md`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/docs/reports/audit_zero_tools_deep_research.md)) audited all 2,948 servers with 0 tools and identified 3 key unexpected architectural formats where tool implementations were missed by our current AST parsers:
1. **JSON/YAML Tool Manifests**: Static tool declarations stored directly in config/manifest files (e.g., `mcp.json`, `tools.json`, `mcp-config.json`, `manifest.json`) without explicit code registration calls.
2. **Alternative Python Decorators**: Tool functions decorated with `@action`, `@command`, `@tool` (e.g., in `server.py`).
3. **Dynamic Array Identifier Tracing in TS/JS**: Tool definitions declared in array variables (e.g., `const TOOLS = [...]`) and returned by reference in `ListToolsRequestSchema` handlers rather than inlined directly in the return object.

Task 62 implements these remedies into the ingestion engine, enriches the affected passports, and provides comprehensive unit tests.

---

## 2. Requirements & Deliverables

### A. JSON & YAML Tool Manifest Parser
- In `src/mcp_fingerprints/ast_parser.py` (or dedicated helper `src/mcp_fingerprints/manifest_parser.py`):
  - Support extracting tool signatures from `mcp.json`, `tools.json`, `mcp-config.json`, and `manifest.json`.
  - Handle both root arrays `[{ "name": "...", "description": "..." }]` and object schemas `{"tools": [...]}` or `{"tool_definitions": [...]}`.
  - Parse tool names, descriptions, and JSON Schema `inputSchema`/`parameters` into normalized `tool_signatures`.

### B. Alternative Python Decorator Support in `ast_parser.py`
- In `PythonASTVisitor`:
  - Broaden decorator matching beyond `@mcp.tool()` to include:
    - `@action` / `@action(...)`
    - `@command` / `@command(...)`
    - `@tool` / `@tool(...)`
  - Extract function docstring as description and type hints as parameter schemas.

### C. Dynamic Array Identifier Resolution in TypeScript/JavaScript
- In `TypeScriptASTParser` / JS AST extraction:
  - When a `ListToolsRequestSchema` handler returns `{ tools: IDENTIFIER }` or `return { tools: IDENTIFIER }`:
    - Search the module scope for `const IDENTIFIER = [...]` or `let IDENTIFIER = [...]`.
    - Extract tool definitions from the referenced array literal.

### D. Passport Enrichment & Catalog Update
- Enrich the affected passports in `data/fingerprints/` and update `web/catalog.json`:
  - `0spoon/seamless` (`data/fingerprints/0spoon_seamless.json` or equivalent)
  - `26zl/cybersec-toolkit` (`data/fingerprints/26zl_cybersec-toolkit.json` or equivalent)
  - `930m310n/geomelon-mcp` (`data/fingerprints/930m310n_geomelon-mcp.json` or equivalent)
- Update `data/zero_tools_audit_manifest.json` marking remedies implemented.

### E. Unit Tests (`tests/test_zero_tool_remedies.py`)
- Author unit tests verifying:
  1. JSON manifest parser extracts tools from `mcp.json` and `tools.json`.
  2. Alternative Python decorators (`@action`, `@command`) are extracted correctly.
  3. Dynamic array identifier references in TypeScript `ListToolsRequestSchema` are resolved.
  4. Ensure all project tests pass (`pytest -q tests/test_zero_tool_remedies.py`).

---

## 3. Non-Interactive Completion Directive
This task is dispatched to Google Jules (EULIS) for non-interactive execution.
Implement the remedies, write the unit tests, enrich the passports and catalog, and ensure all tests pass. Conclude directly with complete patch.
