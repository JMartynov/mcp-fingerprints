# Task Contract: Task 73 — EULIS Code Review & Gap Analysis: Task 68 (Ruby MCP AST Parser)

## 1. Problem Statement
In Task 68, `parse_ruby_mcp_code` was introduced in `src/mcp_fingerprints/ast_parser.py` to statically extract tool definitions from Ruby source code.
We have collected a dataset of 200 real Ruby MCP repositories in `data/samples/ruby_mcp_200.json` (such as `rails-mcp-server`, `tidewave_rails`, `mcp-rb`, `sketchup-mcp2`).
This review analyzes:
1. What patterns `parse_ruby_mcp_code` currently catches (`tool :name`, `server.register_tool`, `class < Tool`).
2. What patterns from the 200 real-world repositories are missed:
   - Block keyword arguments: `tool(:name) { |param1:, param2: "default"| ... }`
   - Class-based definitions using Dry-types or attribute declarations (`attribute :foo, Types::String`)
   - Preceding method docstrings or `desc "..."` declarations
   - Multiline string heredocs (`<<~DESC`) for descriptions
   - FastMCP Ruby syntax variations.
3. Proposing a concrete list of parser enhancements and edge-case fixes.

## 2. Technical Deliverables
- Author comprehensive review report in `docs/reviews/review_task68.md`:
  1. Executive Summary & Verification Findings
  2. Caught Capabilities vs Missed Tool Definitions in the 200 Real Ruby Repos
  3. Actionable List of Proposed Fixes (High/Medium/Low priority)
  4. Proposed Unit Test Fixtures for missed Ruby patterns.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Inspect `src/mcp_fingerprints/ast_parser.py:parse_ruby_mcp_code`, `data/samples/ruby_mcp_200.json`, and `tests/test_ast_ruby_mcp.py`. Author `docs/reviews/review_task68.md`, commit cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
