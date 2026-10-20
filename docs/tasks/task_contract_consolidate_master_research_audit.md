# Task Contract: Consolidate Master Empirical Research Audit & Remediation Roadmap (1,000 Real MCPs)

## Objective
Consolidate the 5 separate group audit reports (`audit_group_1_rust_systems.json`, `audit_group_2_go_cloud_native.json`, `audit_group_3_jvm_dotnet_enterprise.json`, `audit_group_4_regional_international.json`, and `audit_group_5_monorepo_docker_emerging.json`) into a single, comprehensive master dataset and an exhaustive research report.

Every candidate (all 1,000) must be included, and for every missing server, the report must clearly articulate:
`MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy`.

## Deliverables

### 1. Unified Machine-Readable Master Database
- File: `docs/research/master_mcp_ecosystem_audit_1000.json`
- Schema: List of 1,000 candidate objects:
  ```json
  [
    {
      "name": "...",
      "group": "rust_systems | go_cloud_native | jvm_dotnet_enterprise | regional_international | monorepo_docker_emerging",
      "location": "https://...",
      "ecosystem": "...",
      "in_repo": true | false,
      "matched_passport": "..." | null,
      "issue_type": "MATCHED_IN_REPO" | "MISSING_REGISTRY_INDEXER_..." | "AST_UNSUPPORTED_SDK_MACRO" | "UVX_STANDALONE_SCRIPT" | "...",
      "issue_details": "...",
      "remedy": "..."
    }
  ]
  ```

### 2. Comprehensive Master Research Report
- File: `docs/research/master_mcp_ecosystem_audit_report.md`
- Structure:
  1. **Executive Summary**:
     - Total candidates audited: exactly 1,000 (200 in each of the 5 groups).
     - Global Coverage Ratio: Present vs Missing count and percentage.
     - Group-by-group comparative matrix (Rust, Go, JVM/.NET, Regional/International, Monorepo/Docker).
  2. **Systemic Root-Cause Taxonomy & Failure Analysis**:
     - Full statistical breakdown of Issue Types across all 1,000 candidates (count, percentage, and severity).
     - Deep dive into why each failure mode exists (e.g. why `rmcp` Rust macros, `mark3labs/mcp-go`, Spring AI `@Tool`, and PEP 723 `# /// script` headers are missed by current AST and crawling pipelines).
  3. **Comprehensive Master Audit Catalog Table**:
     - Complete table of all 1,000 servers formatted as:
       `| MCP Name | Group | Location | Status | Issue Type | Specific Technical Remedy |`
  4. **Architectural Remediation Roadmap**:
     - Concrete, implementation-ready architectural specifications for updating `synchronizer.py`, `ast_parser.py`, crawler modules, and curated seed lists.

### 3. Automated Conformance Test
- File: `tests/test_master_audit_conformance.py`
- Test Assertions:
  - Asserts `docs/research/master_mcp_ecosystem_audit_1000.json` exists.
  - Asserts length is exactly 1,000.
  - Asserts each of the 5 groups has exactly 200 items.
  - Asserts every missing server (`in_repo == False`) has a populated `issue_type` and `remedy` (minimum 15 characters).
  - Asserts `pytest tests/test_master_audit_conformance.py` passes cleanly.

## Non-Interactive Completion Directive
Execute the consolidation script, generate the JSON dataset and markdown report, create the test verification suite, verify all tests pass with `pytest tests/test_master_audit_conformance.py`, and finalize directly so the remote environment cleanly transitions to `Completed`.
