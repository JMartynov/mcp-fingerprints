# Remediation Plan for 2026-11-04 Daily Web Card Audit

## 1. Technical Root Causes
The primary issue stems from false positives during markdown parsing (`doc_parser.py`) invoked by `DeepZeroToolAuditor`. The auditor scans for tools in markdown tables but is erroneously extracting tabular data from agent skills definitions, evaluation results, configuration files, and contributing guides.

## 2. Targeted Code Modifications

### 2.1 `src/mcp_fingerprints/deep_zero_tool_auditor.py`
- Modify the `secondary_patterns` path exclusion list (around line 69) to explicitly exclude the following paths/filenames:
  - `".agents/"`
  - `".claude/"`
  - `"configs/"`
  - `"eval/"`
  - `"evals/"`
  - `"results.md"`
  - `"release_notes"`
  - `"contributing.md"`
  - `"license"`

### 2.2 `src/mcp_fingerprints/doc_parser.py`
- Strengthen the table header validation. Currently, `doc_parser.py` allows tables if they have certain headers or tool-related keywords.
- Need to ensure we do not parse tables from ADRs, roadmaps, or other non-tool files.
- We will add stricter filtering to ensure the table contains actual MCP tool definitions (e.g. requiring 'name', 'description', etc., and actively rejecting tables containing 'status', 'milestone', 'owner').

## 3. Unit Testing Plan
- Create/update unit tests (e.g., `tests/test_audit_remediation.py` or `tests/test_doc_parser.py`).
- Validate that files with paths like `.agents/skills/create-mcp-tool/SKILL.md`, `configs/prompt.md`, `eval/RESULTS.md`, `CONTRIBUTING.md` return 0 tools when passed to the auditor.
- Ensure the changes result in passing tests without regressions.
