# Task Contract: Task 75 — EULIS Code Review & Gap Analysis: Task 70 (PHP MCP AST Parser)

## 1. Problem Statement
In Task 70, `parse_php_mcp_code` was introduced in `src/mcp_fingerprints/ast_parser.py` to statically extract tool definitions from PHP source code.
We have collected a dataset of 200 real PHP MCP repositories in `data/samples/php_mcp_200.json` (such as `laravel/boost`, `laravel/mcp`, `php-mcp/server`, `php-mcp/laravel`, `php-llm/mcp-bundle`).
This review analyzes:
1. What patterns `parse_php_mcp_code` currently catches (`#[McpTool]`, `class extends Tool`, `$server->registerTool`).
2. What patterns from the 200 real-world repositories are missed:
   - Symfony attributes: `#[AsTool]`, `#[AsMcpTool]`, `#[AutoconfigureTag]`
   - Single-action classes implementing `__invoke(...)` with docblocks
   - Docblock parameter type inference (`/** @param string $query Description */`) when PHP native types are omitted
   - Union types (`string|int`, `?string`) and array element types (`array<string, mixed>`, `ToolInput[]`)
   - Laravel FormRequest/DTO schemas used as tool arguments.
3. Proposing a concrete list of parser enhancements and edge-case fixes.

## 2. Technical Deliverables
- Author comprehensive review report in `docs/reviews/review_task70.md`:
  1. Executive Summary & Verification Findings
  2. Caught Capabilities vs Missed Tool Definitions in the 200 Real PHP Repos
  3. Actionable List of Proposed Fixes (High/Medium/Low priority)
  4. Proposed Unit Test Fixtures for missed PHP patterns.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Inspect `src/mcp_fingerprints/ast_parser.py:parse_php_mcp_code`, `data/samples/php_mcp_200.json`, and `tests/test_ast_php_mcp.py`. Author `docs/reviews/review_task70.md`, commit cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
