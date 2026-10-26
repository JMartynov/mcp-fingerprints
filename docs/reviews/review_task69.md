# EULIS Code Review & Gap Analysis: Task 69 (Swift MCP AST Parser)

## 1. Executive Summary & Verification Findings
The introduction of `parse_swift_mcp_code` in `src/mcp_fingerprints/ast_parser.py` (Task 69) successfully added static extraction capabilities for simple Swift MCP tool definitions. The parser currently utilizes regular expressions to identify three primary patterns: structs conforming to `MCPTool`, macro/attribute definitions like `@McpTool` and `@Tool`, and method calls for `server.registerTool`. 

However, upon cross-referencing these implemented patterns against the provided dataset of 200 real-world Swift MCP repositories (`data/samples/swift_mcp_200.json`), significant gaps were identified. Modern Swift paradigms, complex types, and alternative architectural patterns common in macOS/iOS development (such as `actor` and `class` based tools, or `#mcpTool` macros) are currently unhandled, leading to high false-negative rates for tool discovery in idiomatic Swift codebases. For example, repos like `mediar-ai/mcp-server-macos-use`, `mattt/iMCP`, and `giginet/xcodeproj-mcp-server` contain patterns that the current parser fails to correctly identify.

## 2. Caught Capabilities vs Missed Tool Definitions

### 2.1 Caught Capabilities
The current implementation successfully catches:
*   **Struct-based Tools:** Structs explicitly conforming to `Tool`, `MCPTool`, or `ToolDefinition` (e.g., `struct MyTool: MCPTool`).
*   **Property Extraction:** Basic string literal extraction for `name` and `description` properties via `let name = "..."` or `var description: String { "..." }`.
*   **Input Schema (Arguments):** Nested `struct Arguments: Codable` or `struct Input: Decodable` to extract basic scalar properties (String, Int, Double, Bool) and simple arrays/dictionaries.
*   **Macros/Attributes:** Functions annotated with `@McpTool` or `@Tool`, including their parameters mapped to JSON Schema properties.
*   **Dynamic Registration:** Inline `server.registerTool("name", description: "...")` or `app.registerTool(...)` calls.

### 2.2 Missed Patterns from Real-World Repositories
Analysis of the 200 Swift repositories revealed several idiomatic patterns that the current regex-based AST parser misses:

*   **Modern Swift 6 Macros:** The parser checks for `@McpTool` but misses `#mcpTool` and other custom Swift macros (`#Tool`).
*   **Class and Actor based Tools:** The regex `struct\s+[a-zA-Z0-9_]+\s*:\s*...` explicitly ignores tools implemented as `final class` or `actor`, which are heavily used for stateful tools or concurrency-safe operations (e.g., `actor MyServer`, `final class DatabaseTool: Tool`).
*   **Dispatch Tables / Switch Statements:** Many Swift MCP servers implement a central `CallToolRequest` handler that uses a `switch` statement on `request.params.name` rather than distinct structs/functions per tool. The parser cannot infer tools from these dispatch tables.
*   **Docstring Comments for Descriptions:** In real Swift code, tool descriptions are frequently provided via triple-slash docstrings (`/// Description of the tool`) directly above the struct/function, rather than a hardcoded `let description = "..."` string.
*   **Complex Type Mappings:** 
    *   The parser misses standard Swift Foundation types common in MCP tools, such as `URL`, `Date`, `UUID`, and `Data`, failing to map them to the `string` schema type.
    *   Nested `Codable` schemas (e.g., arguments referencing another custom struct) are not recursively evaluated, leading to missing schema properties.
*   **Property Wrappers:** Usage of property wrappers like `@Option`, `@Argument`, or `@Flag` in `ArgumentParser` based CLIs wrapped as MCP servers are ignored.

## 3. Actionable List of Proposed Fixes (Prioritized)

### High Priority
1.  **Support Classes and Actors:** Modify the struct regex to capture `class`, `final class`, and `actor` definitions conforming to Tool/MCPTool protocols.
    *   *Implementation:* Update regex from `struct\s+` to `(?:struct|class|final\s+class|actor)\s+`.
2.  **Docstring Description Extraction:** Add parsing logic to capture `///` comments immediately preceding a tool definition, using them as the description if an explicit `description` property is not found.
3.  **Expanded Foundation Types Mapping:** Enhance `parse_swift_args` to map `URL`, `Date`, and `UUID` to `{"type": "string"}` in the JSON schema.

### Medium Priority
4.  **Modern Swift Macros:** Update the macro regex to capture both `@` and `#` prefixed macros (e.g., `#mcpTool`, `#Tool`).
5.  **CallToolRequest Dispatch Tables:** Implement a heuristic to scan for `switch request.params.name` or `switch name` blocks and extract the `case "tool_name":` string literals as available tools.
6.  **Property Wrappers in Arguments:** Strip common property wrappers (`@Option`, `@Argument`) before parsing variable types in `parse_swift_args`.

### Low Priority
7.  **Recursive Nested Codable Types:** Attempt to resolve nested struct references within `Arguments` to generate proper nested JSON object schemas.

## 4. Proposed Unit Test Fixtures

```python
def test_swift_class_and_actor_mcp_tool():
    code = """
import Foundation

final class DatabaseTool: Tool {
    let name = "query_db"
    let description = "Execute a database query."
    struct Input: Codable {
        let query: String
    }
}

actor StateTool: MCPTool {
    let name = "get_state"
    let description = "Get server state."
}
"""
    # Expected: 2 tools extracted ("query_db" and "get_state")

def test_swift_docstring_and_macros():
    code = """
import Foundation

/// Fetches the latest logs from the remote server.
#mcpTool(name: "fetch_logs")
func fetchLogs(serverUrl: URL, since: Date?) -> String {
    return ""
}
"""
    # Expected: 1 tool ("fetch_logs"), description "Fetches the latest logs from the remote server.", parameters schema including URL and Date mapped to string.

def test_swift_switch_dispatch():
    code = """
func handleCallTool(request: CallToolRequest) {
    switch request.params.name {
    case "list_files":
        return listFiles()
    case "read_file":
        return readFile(request.params.arguments)
    default:
        throw Error.unknownTool
    }
}
"""
    # Expected: 2 tools ("list_files", "read_file") extracted based on dispatch table.
```
