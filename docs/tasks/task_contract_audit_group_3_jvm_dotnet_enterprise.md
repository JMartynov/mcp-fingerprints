# Task Contract: Audit Group 3 (JVM & .NET Enterprise MCPs)

## Objective
Audit the 200 JVM (Java/Kotlin) & .NET (C#) Enterprise candidate MCP servers defined under `jvm_dotnet_enterprise` in `docs/research/mcp_candidates_by_group.json` against the current repository index (`data/fingerprints/` and `passports.json.gz`). For every missing server, pinpoint the exact root cause / issue type and prescribe a specific technical remedy.

## Scope of Work

1. **Candidate Verification & Matching**:
   - Load the 200 candidates from `docs/research/mcp_candidates_by_group.json["jvm_dotnet_enterprise"]`.
   - Cross-reference each candidate against `data/fingerprints/` and `passports.json.gz` using package names, repository URLs, aliases, and GitHub owner/repo patterns.
   - If present: record `in_repo = true` and `matched_passport = "<file>"`.

2. **Root Cause Diagnosis (for all missing servers)**:
   - For every missing server (`in_repo = false`), categorize into standardized issue types:
     * `MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL`: Published on Maven/Gradle without npm/PyPI bridge.
     * `MISSING_REGISTRY_INDEXER_NUGET`: Published on NuGet (`Microsoft.SemanticKernel`, `ModelContextProtocol.NET`) without npm/PyPI bridge.
     * `KEYWORD_TAG_MISMATCH`: Uses enterprise keywords or framework tags (`spring-ai`, `quarkus`, `dotnet`) without `mcp-server`.
     * `MISSING_GITHUB_TOPICS`: GitHub repo has empty or non-matching topics.
     * `AST_UNSUPPORTED_SDK_MACRO`: Implemented using Spring AI `@Tool`, Quarkus MCP annotations, or .NET C# `[McpServerTool]`/`[KernelFunction]` not recognized by `ast_parser.py`.
     * `ENTERPRISE_VENDOR_WRAPPER`: Proprietary or enterprise binary requiring authentication or custom launcher (e.g. JetBrains, Atlassian, Neo4j, Couchbase).
   - Provide concrete technical explanation under `issue_details`.

3. **Formulate Specific Remedies**:
   - For each missing server, define the exact technical remedy:
     * Maven Central and NuGet indexer crawler additions.
     * AST parser support for Spring AI `@Tool` and C# `[McpServerTool]`/`[KernelFunction]`.
     * Curated seed configurations for vendor enterprise MCP servers.

4. **Deliverables**:
   - `docs/research/audit_group_3_jvm_dotnet_enterprise.json`: JSON array with all 200 audited candidates (fields: `name`, `location`, `ecosystem`, `in_repo`, `matched_passport`, `issue_type`, `issue_details`, `remedy`).
   - `docs/research/audit_group_3_jvm_dotnet_enterprise.md`: Full markdown table (`| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |`) and category breakdown summary.
   - Conformance test `tests/test_audit_group_3.py`:
     * Asserts `docs/research/audit_group_3_jvm_dotnet_enterprise.json` exists.
     * Asserts exactly 200 entries.
     * Asserts every missing entry has non-empty `issue_type` and `remedy`.
     * Passes `pytest tests/test_audit_group_3.py`.

## Non-Interactive Completion Directive
Execute the audit autonomously. Generate the JSON and markdown deliverables, create and run the test suite, and finalize directly so the remote environment transitions cleanly to `Completed`.
