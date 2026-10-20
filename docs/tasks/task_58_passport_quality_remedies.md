# Task Contract: Task 58 (Passport Quality Remedies: Non-Destructive Metadata, Toolset Inheritance & Parser Upgrades)

## Objective
Implement the technical remedies formulated in the Task 57 Quality Audit (`docs/reports/audit_passports_missing_tools_or_description.md`) across `src/mcp_fingerprints/synchronizer.py`, `src/mcp_fingerprints/ast_parser.py`, and `src/mcp_fingerprints/doc_parser.py`. This will recover missing tools and descriptions across >2,400 affected passports and prevent future metadata erasure regressions during automated sync runs.

## Scope of Work

### 1. Synchronizer Non-Destructive Metadata Merge (`src/mcp_fingerprints/synchronizer.py`)
- In `merge_and_enrich_passport(existing_spec, new_spec)`:
  - If `new_spec` has an empty, null, or whitespace `description`, preserve `existing_spec.description`.
  - If `new_spec` has null or empty `repository_url`, preserve `existing_spec.repository_url`.
  - If `new_spec` has null or empty `homepage_url`, preserve `existing_spec.homepage_url`.
  - If `new_spec` has empty `license`, preserve `existing_spec.license`.
  - Merge and deduplicate `keywords` instead of replacing them with an empty list.

### 2. Prior-Version Toolset Inheritance (`src/mcp_fingerprints/synchronizer.py`)
- In `update_existing_passports()` / version update logic:
  - When a new version is detected from npm, PyPI, or Crates.io, and AST tool extraction yields 0 tools:
    - Inspect prior versions in the passport. If the latest prior version contains valid `tool_signatures`, inherit those signatures (`v_tools = copy.deepcopy(prior_version['tool_signatures'])`).
    - Mark the capabilities accordingly (`capabilities['tools'] = True`).
    - Do NOT blacklist the server in `sync_state.json` if prior tools exist.

### 3. Generic GitHub Slug URL Auto-Resolution (`src/mcp_fingerprints/synchronizer.py`)
- In `enrich_zero_tool_passports()` and generic passport loading:
  - If a generic passport has `repository_url: null` or empty, check if its name matches the standard GitHub `owner/repo` pattern (`^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$`).
  - If so, automatically set `repository_url = f"https://github.com/{spec.name}"`.
  - Enable GitHub tree traversal and AST tool extraction for these previously skipped repositories.

### 4. AST Parser Enhancements (`src/mcp_fingerprints/ast_parser.py`)
- **Python `mcp.add_tool` Support**:
  - Update `FastMcpAstVisitor` / Python AST extraction to recognize calls to `mcp.add_tool(fn, ...)` or `server.add_tool(fn, ...)`.
  - Extract tool name from the function argument or explicit `name="..."` keyword, and description from the docstring or `description="..."` keyword.
- **Go Positional & RawSchema Support**:
  - Update `parse_golang_mcp_code()` regex and AST extractor to recognize `mcp.NewToolWithRawSchema(...)` in addition to `mcp.NewTool(...)`.
  - Extract tool names and descriptions when descriptions are passed as positional arguments or string literals.

### 5. Markdown Doc Parser Flexibility (`src/mcp_fingerprints/doc_parser.py`)
- Update `extract_tools_from_markdown()`:
  - Relax section heading match from exact equality to case-insensitive regex matching `r'(?i)\btools?\b'`.
  - Support headers with counts or suffixes (e.g. `## Tools (75)`, `### Available Tools & Functions`).
  - Implement dynamic table column mapping by detecting header names (`name`, `tool`, `description`, `function`) rather than hardcoding column indices.

### 6. Comprehensive Verification Suite (`tests/test_passport_quality_remedies.py`)
- Add automated unit tests verifying:
  1. `merge_and_enrich_passport()` preserves prior description, repo URL, license, and keywords when new spec is empty.
  2. Prior-version toolset inheritance carries over existing tools when a new version has 0 tools.
  3. Generic slug auto-resolution generates `https://github.com/{name}` for `owner/repo` generic passports.
  4. Python `mcp.add_tool()` AST extraction correctly extracts tool name and description.
  5. Go `mcp.NewToolWithRawSchema()` AST extraction correctly extracts tool signatures.
  6. Markdown doc parser extracts tools from `## Tools (5)` with dynamic table headers.
- Ensure all existing and new tests pass: `pytest -q`.

## Non-Interactive Completion Directive
Execute this task end-to-end without asking interactive questions. Implement all changes cleanly across `src/mcp_fingerprints/synchronizer.py`, `src/mcp_fingerprints/ast_parser.py`, and `src/mcp_fingerprints/doc_parser.py`. Add the comprehensive test suite in `tests/test_passport_quality_remedies.py`. Verify that all tests pass (`pytest -q`), and finalize directly so the remote environment cleanly transitions to `Completed`.
