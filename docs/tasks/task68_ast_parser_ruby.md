# Task Contract: Task 68 — Polyglot Static Code Extraction: Ruby MCP Parser (`parse_ruby_mcp_code`)

## 1. Problem Statement
The Model Context Protocol ecosystem features over 345+ active Ruby repositories, including official SDK implementations (`modelcontextprotocol/ruby-sdk`), Rails integrations (`maquina-app/rails-mcp-server`), and Sinatra/DSL servers. `src/mcp_fingerprints/ast_parser.py` currently extracts MCP tools from Python, TypeScript, Go, Rust, Java, and C#, but lacks a native static extractor for Ruby. 

To achieve comprehensive multi-ecosystem passport generation without requiring a live Ruby runtime or gem execution, **Task 68** adds `parse_ruby_mcp_code` to `ast_parser.py` and validates it against live patterns harvested from 200 real Ruby MCP repositories (`data/samples/ruby_mcp_200.json`).

## 2. Technical Requirements & Deliverables

### A. Ruby MCP Parser (`src/mcp_fingerprints/ast_parser.py`)
Implement `parse_ruby_mcp_code(code: str) -> list[dict[str, Any]]`:
1. **Tool Definition Patterns**:
   - Block/DSL tool declarations:
     - `tool :name, description: "..." do ... end`
     - `tool "name", "description" do |args| ... end`
     - `server.register_tool(:name, ...) do ... end`
   - Class-based definitions inheriting from `MCP::Tool` or `Tool`:
     - `name "tool_name"` or `@name = "tool_name"`
     - `description "tool description"` or `@description = "..."`
     - Parameter declarations: `param :key, type: :string, required: true` or `argument :name, ...`
2. **Schema & Argument Extraction**:
   - Extract parameter names, types (`string`, `integer`, `boolean`, `array`, `hash`), and required flags.
   - Construct valid JSON Schema `inputSchema` (`{"type": "object", "properties": {...}, "required": [...]}`).
   - Compute `schema_hash` and extract descriptions.
3. **Dispatcher Integration**:
   - Update `parse_mcp_source_code(code: str, language: str | None = None)` in `ast_parser.py` to route `language="ruby"` or auto-detect Ruby syntax (e.g. `def `, `end`, `class .* < .*Tool`, `require "mcp"`).

### B. Invariant & Recall Unit Tests (`tests/test_ast_ruby_mcp.py`)
1. Test DSL block definitions (`tool :get_weather do ... end`).
2. Test Class-based inheritance definitions (`class QueryTool < MCP::Tool`).
3. Test parameter type coercion and JSON schema construction.
4. Test real-world fixtures derived from top repositories (`rails-mcp-server`, `tidewave_rails`, `mcp-rb`).
5. Ensure 100% test pass rate with zero regression across all existing suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement `parse_ruby_mcp_code` in `src/mcp_fingerprints/ast_parser.py`, wire it to `parse_mcp_source_code`, write comprehensive unit tests in `tests/test_ast_ruby_mcp.py`, run `pytest tests/test_ast_ruby_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
