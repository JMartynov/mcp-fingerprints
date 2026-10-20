# Task Contract: Audit Group 1 (Rust & Systems Polyglot MCPs)

## Objective
Audit the 200 Rust & Systems Polyglot candidate MCP servers defined under `rust_systems` in `docs/research/mcp_candidates_by_group.json` against the current repository index (`data/fingerprints/` and `passports.json.gz`). For every missing server, pinpoint the exact root cause / issue type and prescribe a specific technical remedy.

## Scope of Work

1. **Candidate Verification & Matching**:
   - Load the 200 candidates from `docs/research/mcp_candidates_by_group.json["rust_systems"]`.
   - Cross-reference each candidate against `data/fingerprints/` and `passports.json.gz` using package names, repository URLs, aliases, and GitHub owner/repo patterns.
   - If present: record `in_repo = true` and `matched_passport = "<file>"`.

2. **Root Cause Diagnosis (for all missing servers)**:
   - For every missing server (`in_repo = false`), categorize into standardized issue types:
     * `MISSING_REGISTRY_INDEXER_CRATES_IO`: Published on Crates.io but not on npm/PyPI.
     * `KEYWORD_TAG_MISMATCH`: Uses `model-context-protocol` or `mcp` instead of `mcp-server`.
     * `MISSING_GITHUB_TOPICS`: GitHub repo has empty or non-matching topics.
     * `AST_UNSUPPORTED_SDK_MACRO`: Uses `rmcp = "2.x"` (`#[tool(...)] async fn`), `mcp-sdk-rs`, or custom JSON-RPC routers not parsed by `parse_rust_mcp_code`.
     * `BINARY_CONTAINER_ONLY`: Distributed only as compiled native binary or Homebrew tap.
     * `MONOREPO_NESTED_PATH`: Located in a sub-crate within a Cargo workspace.
   - Provide concrete technical explanation under `issue_details`.

3. **Formulate Specific Remedies**:
   - For each missing server, define the exact technical remedy:
     * AST parser enhancements (e.g. exact regex/AST rules for `rmcp` macros).
     * Crawler query expansions (e.g. Crates.io API crawler, GitHub search queries).
     * Curated seed additions or cargo workspace scanning logic.

4. **Deliverables**:
   - `docs/research/audit_group_1_rust_systems.json`: JSON array with all 200 audited candidates (fields: `name`, `location`, `ecosystem`, `in_repo`, `matched_passport`, `issue_type`, `issue_details`, `remedy`).
   - `docs/research/audit_group_1_rust_systems.md`: Full markdown table (`| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |`) and category breakdown summary.
   - Conformance test `tests/test_audit_group_1.py`:
     * Asserts `docs/research/audit_group_1_rust_systems.json` exists.
     * Asserts exactly 200 entries.
     * Asserts every missing entry has non-empty `issue_type` and `remedy`.
     * Passes `pytest tests/test_audit_group_1.py`.

## Non-Interactive Completion Directive
Execute the audit autonomously. Generate the JSON and markdown deliverables, create and run the test suite, and finalize directly so the remote environment transitions cleanly to `Completed`.
