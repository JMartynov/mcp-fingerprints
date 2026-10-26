# Task Contract: Task 78 — Ruby MCP AST Parser Hardening (Block Args, Heredocs, Curly Braces & Dry-Types)

## 1. Problem Statement
Based on the code review and gap analysis in `docs/reviews/review_task68.md` comparing `parse_ruby_mcp_code` against 200 real-world Ruby MCP repositories (`data/samples/ruby_mcp_200.json`), several prominent Ruby tool definition styles are currently missed.

## 2. Technical Requirements & Deliverables

### A. Parser Enhancements in `src/mcp_fingerprints/ast_parser.py` (`parse_ruby_mcp_code`)
1. **Curly Brace Blocks**:
   - Update DSL tool regex to support tools defined with `{ ... }` in addition to `do ... end` (e.g., `tool(:greet) { ... }`).
2. **Block Parameter Keyword Arguments**:
   - Extract input parameter schemas directly from block pipes `|...|` when tools define arguments inline:
     - `tool(:greet) { |name:, title: "Mr."| ... }`
     - Detect required parameters (no default value) vs optional parameters (with default value).
3. **Multiline Heredoc Descriptions**:
   - Support multiline heredocs (`<<~DESC`, `<<-EOF`, `<<'MARKER'`) used for tool and prompt descriptions.
4. **Dry-Types / Attribute Declarations**:
   - In class-based tools (`class MyTool < MCP::Tool`), parse `attribute :name, Types::String` and `attribute? :count, Types::Integer`.
5. **Method `desc` Declarations**:
   - Recognize `desc "..."` declarations preceding tool blocks or inside class bodies as tool descriptions.

### B. Unit Test Enhancements in `tests/test_ast_ruby_mcp.py`
Add tests for:
- Single-line curly brace tool definitions.
- Block keyword arguments with defaults and required flags.
- Multiline heredoc descriptions.
- Dry-types class attribute declarations.
- Verify 100% test pass rate with zero regression across all test suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement the fixes in `src/mcp_fingerprints/ast_parser.py`, update `tests/test_ast_ruby_mcp.py`, run `pytest tests/test_ast_ruby_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
