# Task Contract: Audit Group 5 (Monorepos, Alternative Registries, Docker Containers & Emerging Ecosystems)

## Objective
Audit the 200 candidate MCP servers defined under `monorepo_docker_emerging` in `docs/research/mcp_candidates_by_group.json` against the current repository index (`data/fingerprints/` and `passports.json.gz`). For every missing server, pinpoint the exact root cause / issue type and prescribe a specific technical remedy.

## Scope of Work

1. **Candidate Verification & Matching**:
   - Load the 200 candidates from `docs/research/mcp_candidates_by_group.json["monorepo_docker_emerging"]`.
   - Cross-reference each candidate against `data/fingerprints/` and `passports.json.gz` using package names, repository URLs, aliases, and GitHub owner/repo patterns.
   - If present: record `in_repo = true` and `matched_passport = "<file>"`.

2. **Root Cause Diagnosis (for all missing servers)**:
   - For every missing server (`in_repo = false`), categorize into standardized issue types:
     * `MONOREPO_NESTED_PATH`: Located in `/packages/*-mcp`, `/servers/*`, or `/tools/mcp/*` within a large monorepo without an independent GitHub repository.
     * `BINARY_CONTAINER_ONLY`: Distributed strictly as Docker Hub image (`docker pull ...`) without npm/PyPI manifest.
     * `ALTERNATIVE_REGISTRY_ONLY`: Listed only on Glama.ai, PulseMCP, or Mcp.so without public registry release.
     * `EMERGING_LANGUAGE_ECOSYSTEM`: Implemented in Swift, PHP (Packagist), Elixir (Hex.pm), or Ruby (RubyGems) lacking language crawlers in `synchronizer.py`.
     * `UVX_STANDALONE_SCRIPT`: Single-file Python UVX script or script header without `pyproject.toml` package distribution.
   - Provide concrete technical explanation under `issue_details`.

3. **Formulate Specific Remedies**:
   - For each missing server, define the exact technical remedy:
     * Monorepo directory traversal crawler rules.
     * Docker Hub API crawler for `docker-mcp` tags.
     * Packagist/Hex.pm crawler additions or Swift Package Index connectors.
     * Single-file script header parsing recipes.

4. **Deliverables**:
   - `docs/research/audit_group_5_monorepo_docker_emerging.json`: JSON array with all 200 audited candidates (fields: `name`, `location`, `ecosystem`, `in_repo`, `matched_passport`, `issue_type`, `issue_details`, `remedy`).
   - `docs/research/audit_group_5_monorepo_docker_emerging.md`: Full markdown table (`| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |`) and category breakdown summary.
   - Conformance test `tests/test_audit_group_5.py`:
     * Asserts `docs/research/audit_group_5_monorepo_docker_emerging.json` exists.
     * Asserts exactly 200 entries.
     * Asserts every missing entry has non-empty `issue_type` and `remedy`.
     * Passes `pytest tests/test_audit_group_5.py`.

## Non-Interactive Completion Directive
Execute the audit autonomously. Generate the JSON and markdown deliverables, create and run the test suite, and finalize directly so the remote environment transitions cleanly to `Completed`.
