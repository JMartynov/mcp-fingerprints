# Task Contract: Task 69 — Polyglot Static Code Extraction: Swift MCP Parser (`parse_swift_mcp_code`)

## 1. Problem Statement
The Swift Model Context Protocol ecosystem contains over 739+ active repositories on GitHub, including the official Apple ecosystem SDK (`modelcontextprotocol/swift-sdk`), `mattt/iMCP`, macOS desktop agent integrations, and CLI tools. `src/mcp_fingerprints/ast_parser.py` lacks a native Swift extractor.

To extract MCP passports statically from Swift source code without requiring `swiftc`, Xcode, or an Apple runtime, **Task 69** implements `parse_swift_mcp_code` and validates it against live patterns harvested from 200 real Swift MCP repositories (`data/samples/swift_mcp_200.json`).

## 2. Technical Requirements & Deliverables

### A. Swift MCP Parser (`src/mcp_fingerprints/ast_parser.py`)
Implement `parse_swift_mcp_code(code: str) -> list[dict[str, Any]]`:
1. **Tool Definition Patterns**:
   - Struct-based definitions conforming to `Tool`, `MCPTool`, or `ToolDefinition`:
     - Extract `let name = "..."` or `var name: String { "..." }`
     - Extract `let description = "..."`
     - Extract nested `Arguments: Codable` or `Input: Codable` structs.
   - Macro/Attribute definitions:
     - `@McpTool(name: "...", description: "...")`
     - Function declarations annotated with `@Tool`.
   - Server registration calls:
     - `server.registerTool("name", description: "...") { ... }`
2. **Schema & Argument Extraction**:
   - Map Swift types (`String`, `Int`, `Double`, `Bool`, `[String]`, `[String: Any]`) to JSON Schema types (`string`, `integer`, `number`, `boolean`, `array`, `object`).
   - Extract optionality (`String?` vs non-optional `String`) to construct `required` fields list.
   - Construct standard `inputSchema`.
3. **Dispatcher Integration**:
   - Update `parse_mcp_source_code` in `ast_parser.py` to route `language="swift"` and auto-detect Swift syntax (`import Foundation`, `import MCP`, `func `, `struct .* : .*Tool`).

### B. Invariant & Recall Unit Tests (`tests/test_ast_swift_mcp.py`)
1. Test struct conforming to `MCPTool` with nested `Arguments: Codable`.
2. Test `@McpTool` macro attributes and function arguments.
3. Test `server.registerTool` function calls.
4. Test real-world patterns from `mattt/iMCP` and `mcp-server-macos-use`.
5. Ensure 100% test pass rate with zero regression across all existing suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement `parse_swift_mcp_code` in `src/mcp_fingerprints/ast_parser.py`, wire it to `parse_mcp_source_code`, write comprehensive unit tests in `tests/test_ast_swift_mcp.py`, run `pytest tests/test_ast_swift_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
