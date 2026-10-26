# Task Contract: Task 79 — Swift MCP AST Parser Hardening (Classes/Actors, Docstrings, Foundation Types & Macros)

## 1. Problem Statement
Based on the code review and gap analysis in `docs/reviews/review_task69.md` comparing `parse_swift_mcp_code` against 200 real-world Swift MCP repositories (`data/samples/swift_mcp_200.json`), several prominent Swift tool patterns are currently missed.

## 2. Technical Requirements & Deliverables

### A. Parser Enhancements in `src/mcp_fingerprints/ast_parser.py` (`parse_swift_mcp_code`)
1. **Class and Actor Tool Definitions**:
   - Support `class`, `final class`, and `actor` conforming to `Tool`, `MCPTool`, or `ToolDefinition` (in addition to `struct`).
2. **Docstring Description Extraction**:
   - Extract triple-slash docstring comments (`/// Tool description`) immediately preceding structs/classes/functions when explicit description string literals are omitted.
3. **Foundation Type Mapping**:
   - Map standard Swift Foundation types (`URL`, `Date`, `UUID`, `Data`, `FilePath`) to `{"type": "string"}` in JSON schemas.
4. **Swift 6 Macro Syntax**:
   - Support `#mcpTool(...)` and `@Tool` macro attributes with inline parameter reflection.
5. **ArgumentParser Property Wrappers**:
   - Extract `@Option`, `@Argument`, and `@Flag` property wrappers used in CLI-based tools to derive parameter descriptions and types.

### B. Unit Test Enhancements in `tests/test_ast_swift_mcp.py`
Add tests for:
- Actor and class-based tool definitions conforming to `MCPTool`.
- Triple-slash docstring descriptions.
- Foundation type schemas (`URL`, `Date`, `UUID`).
- Swift 6 macro and ArgumentParser wrapper tool definitions.
- Verify 100% test pass rate with zero regression across all test suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement the fixes in `src/mcp_fingerprints/ast_parser.py`, update `tests/test_ast_swift_mcp.py`, run `pytest tests/test_ast_swift_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
