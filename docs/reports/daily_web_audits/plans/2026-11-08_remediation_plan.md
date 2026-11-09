# Remediation Plan for Daily Audit 2026-11-08

## Technical Root Cause Analysis
The primary technical issue causing massive tool count inflations and `MISSED_TOOLS` discrepancies is the lack of proper deduplication. When MCP tool metadata is scraped from source repositories, it frequently duplicates findings across two boundaries:
1. **Intra-file Duplication (`doc_parser.py`)**: Markdown parsers extract tool signatures from both tables and list items. Authors frequently list tools in a summary table and then detail them in lists, causing the parser to return duplicate entries.
2. **Inter-file Duplication (`deep_zero_tool_auditor.py`)**: When the deep auditor iterates through `README.md`, nested docs (`docs/tools.md`), and actual code implementations (`src/tools.ts`), it mindlessly aggregates all found tools (`all_tools.extend(file_tools)`), failing to deduplicate tools that correctly match by name.

Additionally, certain packages flagged as `MISMATCH` with non-zero claimed tools were correctly identified as non-MCP provider implementations (e.g. SDKs, Frameworks, ESLint plugins).

## Targeted Code Modifications

1. **`src/mcp_fingerprints/doc_parser.py`**:
   - Update `parse_markdown_tool_docs` (or similar extraction methods) to normalize tool names (strip and lowercase) and maintain a set/dict of seen tool names.
   - Return only unique tool representations.

2. **`src/mcp_fingerprints/deep_zero_tool_auditor.py`**:
   - In the `audit()` loop (and/or `inspect_file()` handling), when accumulating `file_tools` into `all_tools`, deduplicate the incoming tools against existing ones using the tool's normalized name (`name.strip().lower()`).
   - The first encountered definition for a tool should be preserved to retain the richest metadata initially found.

## Unit Testing Plan
The fixes will be validated by a new test suite: `tests/test_audit_remediation_2026_11_08.py`.
- **Markdown Deduplication Test**: Provide markdown text containing both a table and list defining the same tool names. Ensure the parser returns a deduplicated count.
- **Multi-File Deduplication Test**: Mock a scenario where `deep_zero_tool_auditor.py` scans a `README.md` and a `src/tools.ts`, both declaring `"search_tool"`. Ensure the final `tools_found_count` is 1, not 2.
- **Status Mapping Verifications**: Verify mapping of unresolvable and mismatched framework statuses remains untouched by the deduplication modifications.
