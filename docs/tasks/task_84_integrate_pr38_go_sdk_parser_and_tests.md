# Task Contract: Task 84 — Integrate PR #38 Go SDK Literal Parser & Tests with Constant Resolution

## 1. Problem Statement & Motivation
PR #38 (`fix/official-go-sdk-literals` by `@kimjooyoon`) introduces:
1. `src/mcp_fingerprints/go_sdk_parser.py`: A lexical tokenizer and recursive-descent Go map/slice literal evaluator capable of parsing complex nested Go schemas, string escapes (`\x65`, `\u00e9`, octal), and custom import aliases.
2. `tests/test_official_go_sdk_parser.py`: 17 unit test cases testing edge-case Go string escapes, comments, delimiters, and nested literal schemas.

In Task 83, we implemented constant name resolution (`const x = "val"`, `const ( ... )`) which successfully resolved `kimjooyoon/gooo-go-ports`'s live tools.

This task integrates PR #38 into `main` by combining PR #38's Go map/slice parser and tests with our constant resolver so that:
- Literal schemas, complex Go escapes, and import aliases from PR #38 are supported.
- Constant names and `gooo-go-ports` reproduction from Task 83 are preserved.
- No existing tests or passport signatures are broken.

---

## 2. Technical Scope & Implementation Plan

### A. Ingestion of PR #38 Files
1. Add `src/mcp_fingerprints/go_sdk_parser.py` from PR #38.
2. In `src/mcp_fingerprints/go_sdk_parser.py`:
   - Enhance `_Literal` and `parse_official_go_tools` to accept or look up resolved constants (from file scope constant table) when a token matches an identifier in scope.
3. In `src/mcp_fingerprints/ast_parser.py`:
   - Call `parse_official_go_tools(code)` in `parse_golang_mcp_code(code)`.
   - Ensure deduplication with existing builder definitions (`mcp.NewTool`) and composite literals.

### B. Ingestion & Enhancement of PR #38 Tests
1. Add `tests/test_official_go_sdk_parser.py` from PR #38.
2. Verify all 17 test cases pass cleanly.
3. Ensure `tests/test_ast_golang_official_sdk.py` continues to pass (all 5 tests).
4. Run full pytest suite across `tests/` (ensuring 460+ tests pass).

### C. Safety & Invariants
- Maintain strict domain isolation (zero security/vulnerability keywords).
- Clean up any scratch files.
- Verify Ruff formatting / linting.
