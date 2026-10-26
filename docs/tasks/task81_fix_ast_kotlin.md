# Task Contract: Task 81 — Kotlin MCP AST Parser Hardening (Spring AI, Parameter Descriptions & Data Classes)

## 1. Problem Statement
Based on the code review and gap analysis in `docs/reviews/review_task71.md` comparing `parse_kotlin_mcp_code` against 200 real-world Kotlin MCP repositories (`data/samples/kotlin_mcp_200.json`), several prominent Kotlin tool patterns are currently missed.

## 2. Technical Requirements & Deliverables

### A. Parser Enhancements in `src/mcp_fingerprints/ast_parser.py` (`parse_kotlin_mcp_code`)
1. **Spring AI & Annotation Variations**:
   - Support Spring AI `@Tool` annotations placed on functions inside `@Service` / `@Component` beans.
   - Support `@McpTool` and `@ToolMethod` annotations.
2. **Parameter Descriptions via `@Description`**:
   - Parse `@Description("...")` annotations on function parameters to populate `inputSchema.properties[param]["description"]`.
3. **Data Class Composite Parameter Models**:
   - When a parameter type is a Kotlin `data class`, parse its constructor properties into a structured `object` schema rather than defaulting to generic `string`.
4. **Bracket-Aware Argument Splitting**:
   - Enhance function parameter splitting to respect nested generics (`Map<String, List<Int>>`) and complex default expressions without splitting prematurely on inner commas.
5. **Suspend Functions**:
   - Ensure `suspend fun` signatures with multiple modifiers (`override suspend fun`, `inline fun`) are reliably captured.

### B. Unit Test Enhancements in `tests/test_ast_kotlin_mcp.py`
Add tests for:
- Spring AI `@Tool` annotations on bean methods.
- `@Description("...")` annotations on parameters.
- Data class composite parameter schemas.
- Suspend functions and complex generic parameter types.
- Verify 100% test pass rate with zero regression across all test suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement the fixes in `src/mcp_fingerprints/ast_parser.py`, update `tests/test_ast_kotlin_mcp.py`, run `pytest tests/test_ast_kotlin_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
