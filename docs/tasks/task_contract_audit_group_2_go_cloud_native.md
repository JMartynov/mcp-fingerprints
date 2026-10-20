# Task Contract: Audit Group 2 (Go & Cloud-Native MCPs)

## Objective
Audit the 200 Go & Cloud-Native candidate MCP servers defined under `go_cloud_native` in `docs/research/mcp_candidates_by_group.json` against the current repository index (`data/fingerprints/` and `passports.json.gz`). For every missing server, pinpoint the exact root cause / issue type and prescribe a specific technical remedy.

## Scope of Work

1. **Candidate Verification & Matching**:
   - Load the 200 candidates from `docs/research/mcp_candidates_by_group.json["go_cloud_native"]`.
   - Cross-reference each candidate against `data/fingerprints/` and `passports.json.gz` using package names, repository URLs, aliases, and GitHub owner/repo patterns.
   - If present: record `in_repo = true` and `matched_passport = "<file>"`.

2. **Root Cause Diagnosis (for all missing servers)**:
   - For every missing server (`in_repo = false`), categorize into standardized issue types:
     * `MISSING_REGISTRY_INDEXER_PKG_GO_DEV`: Go module published on `pkg.go.dev` or GitHub releases without npm/PyPI bridge.
     * `KEYWORD_TAG_MISMATCH`: Uses `mcp`, `model-context-protocol`, or Kubernetes/Docker tags without `mcp-server`.
     * `MISSING_GITHUB_TOPICS`: Repo has empty or non-standard GitHub topics.
     * `AST_UNSUPPORTED_SDK_MACRO`: Implemented using `mark3labs/mcp-go`, `metoro-io/mcp-golang`, or custom JSON-RPC stdio dispatchers not matched by `parse_golang_mcp_code`.
     * `MONOREPO_NESTED_PATH`: Located in a nested directory (`/cmd/mcp`, `/pkg/mcp`, or Kubernetes operator monorepo).
     * `BINARY_CONTAINER_ONLY`: Pre-compiled binary or Docker container without root Go package.
   - Provide concrete technical explanation under `issue_details`.

3. **Formulate Specific Remedies**:
   - For each missing server, define the exact technical remedy:
     * Ingestion via Go proxy / GitHub crawler adjustments.
     * AST parser enhancements for `mark3labs/mcp-go` tool registrations (`mcp.NewTool(...)`, `server.AddTool(...)`).
     * Monorepo scanning patterns for Go `/cmd/*` structures.

4. **Deliverables**:
   - `docs/research/audit_group_2_go_cloud_native.json`: JSON array with all 200 audited candidates (fields: `name`, `location`, `ecosystem`, `in_repo`, `matched_passport`, `issue_type`, `issue_details`, `remedy`).
   - `docs/research/audit_group_2_go_cloud_native.md`: Full markdown table (`| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |`) and category breakdown summary.
   - Conformance test `tests/test_audit_group_2.py`:
     * Asserts `docs/research/audit_group_2_go_cloud_native.json` exists.
     * Asserts exactly 200 entries.
     * Asserts every missing entry has non-empty `issue_type` and `remedy`.
     * Passes `pytest tests/test_audit_group_2.py`.

## Non-Interactive Completion Directive
Execute the audit autonomously. Generate the JSON and markdown deliverables, create and run the test suite, and finalize directly so the remote environment transitions cleanly to `Completed`.
