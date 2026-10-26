# Task Contract: Task 80 — PHP MCP AST Parser Hardening (Symfony Attributes, Invokables, Docblock Types & Unions)

## 1. Problem Statement
Based on the code review and gap analysis in `docs/reviews/review_task70.md` comparing `parse_php_mcp_code` against 200 real-world PHP MCP repositories (`data/samples/php_mcp_200.json`), several prominent PHP tool patterns are currently missed.

## 2. Technical Requirements & Deliverables

### A. Parser Enhancements in `src/mcp_fingerprints/ast_parser.py` (`parse_php_mcp_code`)
1. **Symfony & Framework Attributes**:
   - Support `#[AsTool]`, `#[AsMcpTool]`, and `#[AutoconfigureTag]` in addition to `#[McpTool]` and `#[Tool]`.
2. **Single-Action Invokable Classes**:
   - Detect classes implementing `__invoke(...)` with tool metadata defined at class or method level.
3. **Docblock Parameter Type & Description Extraction**:
   - Parse `/** @param string $query Description */` docblocks to infer parameter descriptions and types when native typehints are omitted.
4. **Union & Nullable Types**:
   - Properly parse `?string` as nullable optional, and union types `string|int` mapping to JSON schema `anyOf` or fallback primitive type.
5. **Array Shape & Element Types**:
   - Parse typed arrays (`array<string, mixed>`, `string[]`) to `{"type": "array", "items": {"type": "string"}}`.

### B. Unit Test Enhancements in `tests/test_ast_php_mcp.py`
Add tests for:
- Symfony `#[AsTool]` and `#[AsMcpTool]` attributes.
- Invokable `__invoke()` action tool classes.
- Docblock `@param` type and description extraction.
- Union and nullable parameter types.
- Verify 100% test pass rate with zero regression across all test suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement the fixes in `src/mcp_fingerprints/ast_parser.py`, update `tests/test_ast_php_mcp.py`, run `pytest tests/test_ast_php_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
