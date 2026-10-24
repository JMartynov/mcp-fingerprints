# MCP Fingerprints Technical Reports Directory

This directory contains the technical reports, invariant verification documentation, codebase audits, and ecosystem gap analyses for `mcp-fingerprints`.

---

## 📑 Cumulative Master Reports

The two cumulative master reports synthesize all invariant verification runs, test profiles, codebase audits, competitive benchmarks, and strategic blueprints across the project lifecycle:

| Report | Description | Scope & Coverage |
|:---|:---|:---|
| [**`WORKFLOW_INVARIANTS_AND_CODE_AUDIT_REPORT.md`**](WORKFLOW_INVARIANTS_AND_CODE_AUDIT_REPORT.md) | **Cumulative Master Report: Workflow Invariants, System Architecture & Code Audit** | Comprehensive architectural review across Tasks 1–5; 43 module map; verification matrix of 5 invariant pillars across 400 passed tests; unified technical findings ledger (MED-01 drift detector fix, MED-02 floating-point metric bounding). |
| [**`ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md`**](ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md) | **Cumulative Master Report: MCP Ecosystem Benchmark & Strategic Gap Analysis** | Multi-ecosystem competitive benchmark against 14+ industry players (runtime proxies, commercial registries, automated fuzzers, AI guardrails, Sigstore/SLSA L3); 4 concrete architectural blueprints (Sidecar Policy Generator, Schema-Driven Fuzzer, Sigstore Keyless Attestation, CLI Registry Connectors). |

---

## 🛡️ Invariant Verification & Technical Task Reports (Tasks 1–9)

The 9 discrete technical task reports detail the implementation and verification of each specific subsystem:

### Invariant Pillars (Tasks 1–5)

| Task | Report Link | Domain Area | Target Invariants & Key Verifications |
|:---|:---|:---|:---|
| **Task 1** | [**`task1_cli_sandbox_protocol_report.md`**](task1_cli_sandbox_protocol_report.md) | CLI Subprocess Sandboxing & JSON-RPC Protocol | Child environment credential scrubbing (`AWS_*`, `OPENAI_*`, `GITHUB_*`, `SSH_AUTH_SOCK`), execution timeout boundaries ($\le 5\text{s}$) with process tree reaping (SIGTERM/SIGKILL), strict JSON-RPC 2.0 version & ID reflection, malformed error object handling, and MCP handshake sequence (`initialize` $\rightarrow$ `notifications/initialized`). |
| **Task 2** | [**`task2_canonicalizer_snapshot_invariants_report.md`**](task2_canonicalizer_snapshot_invariants_report.md) | Canonicalizer, Domain Isolation & Snapshots | Order-independent & whitespace-invariant SHA-256 canonical hashing across 500 permutations; pure structural domain isolation (rejection of dynamic vulnerability fields); two-tier cache coherency (`mtime` check with SHA-256 fallback); DuckDB ephemeral SQL resilience; deterministic gzip snapshot compilation. |
| **Task 3** | [**`task3_matcher_search_invariants_report.md`**](task3_matcher_search_invariants_report.md) | Tri-Layer Matcher, Distance Metrics & Fast Index | Layer 1 exact cryptographic hash matching ($O(1)$, confidence 1.0); Layer 2 topological Jaccard distance metric boundaries ($[0.0, 1.0]$, weighted property/required/type matching with $>0.65$ threshold); Layer 3 composite capability matching ($0.7 \cdot \text{Topology} + 0.3 \cdot \text{Capabilities}$); graceful semantic search fallback to lexical BM25; fast multi-index lookup scalability ($<10\text{ms}$ across 2,000 packages). |
| **Task 4** | [**`task4_config_scanner_tamper_drift_report.md`**](task4_config_scanner_tamper_drift_report.md) | Config Scanner, Lossless Exporters & Supply-Chain Drift | Multi-client workstation configuration discovery across 8+ agents (Claude Desktop, Cursor, Zed, Cline, Roo, Antigravity, OpenHands, Windsurf); lossless in-place JSONC comment and whitespace preserving modification; supply-chain tamper detection escalation (`hash_tamper` $\rightarrow$ CRITICAL, `tool_added` $\rightarrow$ HIGH, empty hash exemption); workstation baseline diffing. |
| **Task 5** | [**`task5_ast_openapi_zero_tool_report.md`**](task5_ast_openapi_zero_tool_report.md) | Polyglot AST Extractors, OpenAPI & Zero-Tool Parsers | Multi-language AST parameter and docstring extraction across Python FastMCP decorators, TypeScript Zod schemas, Go `mark3labs/mcp-go` builder patterns, Rust `rmcp` macros, JVM Spring AI `@Tool`, C# .NET `[McpServerTool]`; OpenAPI v3 JSON/YAML endpoint extraction; Markdown README table parsing; international CJK/UTF-8 Unicode sanitization with ASCII control character byte filtering. |

### Ecosystem Benchmarks & Gap Analyses (Tasks 6–9)

| Task | Report Link | Domain Area | Key Findings & Comparative Insights |
|:---|:---|:---|:---|
| **Task 6** | [**`task6_runtime_proxies_policy_engines_report.md`**](task6_runtime_proxies_policy_engines_report.md) | Runtime Proxies & Policy Engines | Comparative analysis against Invariant Labs, Lakera Guard, Cisco AI Agent Gateway, and Cloudflare AI Gateway. Establishes the clear boundary between `mcp-fingerprints` (offline static identity authority) and inline proxies (runtime payload sanitization). Proposes Sidecar Policy Generator (OPA/Rego) blueprint. |
| **Task 7** | [**`task7_registries_hosting_cli_report.md`**](task7_registries_hosting_cli_report.md) | Registries, Hosting & CLI Ergonomics | Deep dive into Smithery.ai, Docker MCP Catalog, and PulseMCP. Evaluates catalog ingestion formats, dynamic configuration synthesis, 1-click installation mechanics, and containerized deployment models. Proposes CLI Registry & Sandbox Connectors. |
| **Task 8** | [**`task8_fuzzing_guardrails_benchmark_report.md`**](task8_fuzzing_guardrails_benchmark_report.md) | Fuzzing & Security Guardrails | Research into Protect AI (Guardian), Verity (OWASP Agentic Top 10), Garak, and Mindgard. Designs schema-driven fuzzer architecture utilizing canonical AST schemas to generate targeted boundary payloads for tool parameter robustness testing. |
| **Task 9** | [**`task9_sbom_attestation_supply_chain_report.md`**](task9_sbom_attestation_supply_chain_report.md) | SBOM, Attestation & Supply-Chain Security | Evaluation of Sigstore Cosign, CycloneDX/SPDX, Snyk/Socket.dev, and SLSA Level 3. Details integration architecture for signing MCP passports via keyless OIDC identities and publishing cryptographic attestations to Rekor public transparency logs. |

---

## 📚 Historical & Specialized Investigation Reports

| Report | Description |
|:---|:---|
| [**`codebase_audit_and_gap_analysis.md`**](codebase_audit_and_gap_analysis.md) | Foundational architecture and codebase audit establishing the 3-layer architecture. |
| [**`clean_architecture_report.md`**](clean_architecture_report.md) | Structural domain model purity and architectural boundary preservation report. |
| [**`deep_code_review_and_proposals_report.md`**](deep_code_review_and_proposals_report.md) | Comprehensive code review across crawler and ingestion subsystems. |
| [**`audit_zero_tools_deep_research.md`**](audit_zero_tools_deep_research.md) | Deep empirical research into packages yielding 0 extracted tools and dynamic dispatch root causes. |
| [**`audit_passports_missing_tools_or_description.md`**](audit_passports_missing_tools_or_description.md) | Audit of catalog entries missing descriptive metadata or tool specifications. |
| [**`automated_pypi_sync_release_report.md`**](automated_pypi_sync_release_report.md) | PyPI release automation and automated daily sync pipeline report. |
| [**`incident_jules_session_interactive_state_fix.md`**](incident_jules_session_interactive_state_fix.md) | Incident post-mortem and resolution for interactive subagent session states. |
| [**`task_23_hierarchical_json_and_duckdb_research.md`**](task_23_hierarchical_json_and_duckdb_research.md) | Storage benchmarks comparing hierarchical JSON partitioning against DuckDB queries. |
| [**`task_29_docker_and_incus_sandbox_report.md`**](task_29_docker_and_incus_sandbox_report.md) | Exploration of isolated container runtimes (Docker / Incus) for live subprocess probing. |
| [**`wave_3_report.md`**](wave_3_report.md) through [**`wave_9_implementation_report.md`**](wave_9_implementation_report.md) | Execution wave milestones covering schema enhancements, performance optimizations, and polyglot expansions. |
