# Task Contract: Task 74 — EULIS Code Review & Gap Analysis: Task 69 (Swift MCP AST Parser)

## 1. Problem Statement
In Task 69, `parse_swift_mcp_code` was introduced in `src/mcp_fingerprints/ast_parser.py` to statically extract tool definitions from Swift source code.
We have collected a dataset of 200 real Swift MCP repositories in `data/samples/swift_mcp_200.json` (such as `mattt/iMCP`, `mediar-ai/mcp-server-macos-use`, `mirroir-mcp`, `giginet/xcodeproj-mcp-server`).
This review analyzes:
1. What patterns `parse_swift_mcp_code` currently catches (`struct: MCPTool`, `@McpTool`, `server.registerTool`).
2. What patterns from the 200 real-world repositories are missed:
   - Modern Swift 6 Macros: `#mcpTool` or `@Tool`
   - Class-based and Actor-based tool implementations (`actor MyServer`, `final class MyTool: Tool`)
   - Dispatch tables based on `CallToolRequest` switch statements
   - Parameter wrappers and docstring comments (`/// Description`)
   - Complex Swift type mappings (e.g., `[String: Any]`, `URL`, `Date`, nested Codable schemas).
3. Proposing a concrete list of parser enhancements and edge-case fixes.

## 2. Technical Deliverables
- Author comprehensive review report in `docs/reviews/review_task69.md`:
  1. Executive Summary & Verification Findings
  2. Caught Capabilities vs Missed Tool Definitions in the 200 Real Swift Repos
  3. Actionable List of Proposed Fixes (High/Medium/Low priority)
  4. Proposed Unit Test Fixtures for missed Swift patterns.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Inspect `src/mcp_fingerprints/ast_parser.py:parse_swift_mcp_code`, `data/samples/swift_mcp_200.json`, and `tests/test_ast_swift_mcp.py`. Author `docs/reviews/review_task69.md`, commit cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
