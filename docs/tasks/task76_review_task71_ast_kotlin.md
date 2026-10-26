# Task Contract: Task 76 — EULIS Code Review & Gap Analysis: Task 71 (Kotlin MCP AST Parser)

## 1. Problem Statement
In Task 71, `parse_kotlin_mcp_code` was introduced in `src/mcp_fingerprints/ast_parser.py` to statically extract tool definitions from Kotlin source code.
We have collected a dataset of 200 real Kotlin MCP repositories in `data/samples/kotlin_mcp_200.json` (such as `PortSwigger/mcp-server`, `CrossPaste/crosspaste-desktop`, `JetBrains/mcp-server-plugin`, `IlyaGulya/gradle-mcp-server`).
This review analyzes:
1. What patterns `parse_kotlin_mcp_code` currently catches (`@Tool`, `mcpServer { tool(...) }`, `class: McpTool`).
2. What patterns from the 200 real-world repositories are missed:
   - Spring AI Kotlin `@Tool` annotations on Spring `@Service`/`@Component` beans
   - `@Description("...")` annotations on function parameters
   - Suspend functions: `suspend fun executeTool(...)`
   - Ktor route handlers and WebSockets/SSE tool dispatchers
   - Kotlin Data Class parameter models (composite objects unpacked into tool inputs)
   - Nullable types (`String?`) vs default argument handling.
3. Proposing a concrete list of parser enhancements and edge-case fixes.

## 2. Technical Deliverables
- Author comprehensive review report in `docs/reviews/review_task71.md`:
  1. Executive Summary & Verification Findings
  2. Caught Capabilities vs Missed Tool Definitions in the 200 Real Kotlin Repos
  3. Actionable List of Proposed Fixes (High/Medium/Low priority)
  4. Proposed Unit Test Fixtures for missed Kotlin patterns.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Inspect `src/mcp_fingerprints/ast_parser.py:parse_kotlin_mcp_code`, `data/samples/kotlin_mcp_200.json`, and `tests/test_ast_kotlin_mcp.py`. Author `docs/reviews/review_task71.md`, commit cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
