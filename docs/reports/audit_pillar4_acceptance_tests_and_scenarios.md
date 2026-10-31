# Acceptance Testing & Scenario Coverage Audit (Pillar 4)

## Executive Summary

This report documents the Pillar 4 Audit: Acceptance Testing & Scenario Coverage for `mcp-fingerprints`.

* **Total Test Files Examined**: 110
* **Total Tests Identified**: 500

## 1. Coverage Matrix (Test Inventory)

The test suite was mapped against key feature requirements: AST, Probers, Matcher, Scanner, TUI, and CLI.

| Test File | Total Tests | Target Features |
|-----------|-------------|-----------------|
| `test_ast_golang_official_sdk.py` | 5 | AST |
| `test_ast_kotlin_mcp.py` | 8 | AST |
| `test_ast_parser.py` | 7 | AST |
| `test_ast_parser_enriched.py` | 6 | AST |
| `test_ast_php_mcp.py` | 6 | AST |
| `test_ast_real_life_examples.py` | 7 | AST |
| `test_ast_ruby_mcp.py` | 9 | AST |
| `test_ast_swift_mcp.py` | 8 | AST |
| `test_audit_group_1.py` | 3 | Core/Misc |
| `test_audit_group_2.py` | 3 | Core/Misc |
| `test_audit_group_3.py` | 1 | Core/Misc |
| `test_audit_group_4.py` | 1 | Core/Misc |
| `test_audit_group_5.py` | 4 | Core/Misc |
| `test_audit_remediation.py` | 4 | Core/Misc |
| `test_auto_passport.py` | 2 | Core/Misc |
| `test_automated_release_trigger.py` | 4 | Core/Misc |
| `test_cache.py` | 4 | Core/Misc |
| `test_candidate_groups_conformance.py` | 4 | Core/Misc |
| `test_candidate_routing.py` | 1 | Core/Misc |
| `test_canonicalizer.py` | 1 | Matcher |
| `test_checkpoint_engine.py` | 4 | Core/Misc |
| `test_ci_pipeline.py` | 4 | Core/Misc |
| `test_cli_match.py` | 2 | CLI |
| `test_cli_runtime_probe.py` | 3 | CLI |
| `test_community_health.py` | 6 | Core/Misc |
| `test_config_exporter.py` | 13 | Core/Misc |
| `test_config_exporter_extended.py` | 6 | Core/Misc |
| `test_config_scanner.py` | 5 | Scanner |
| `test_config_scanner_http.py` | 1 | Scanner |
| `test_data_loader.py` | 4 | Core/Misc |
| `test_dataset_sanitization.py` | 3 | Core/Misc |
| `test_deep_zero_tool_auditor.py` | 13 | Core/Misc |
| `test_deep_zero_tool_auditor_dir.py` | 1 | Core/Misc |
| `test_detector.py` | 3 | Matcher |
| `test_doc_parser.py` | 4 | Core/Misc |
| `test_drift_detector.py` | 5 | Scanner |
| `test_dynamic_entrypoints.py` | 4 | Core/Misc |
| `test_fingerprint_kb.py` | 6 | Core/Misc |
| `test_github_tree_extractor.py` | 3 | Core/Misc |
| `test_golang_rust_parser.py` | 3 | AST |
| `test_hierarchical_partitioning_and_duckdb.py` | 6 | Core/Misc |
| `test_http_prober.py` | 3 | Probers |
| `test_hub.py` | 8 | Core/Misc |
| `test_hub_resolver.py` | 10 | Matcher |
| `test_ingestion_sanitization.py` | 6 | Core/Misc |
| `test_jvm_dotnet_parser.py` | 3 | AST |
| `test_live_acceptance_go_cloud_native.py` | 3 | Core/Misc |
| `test_live_acceptance_jvm_dotnet.py` | 3 | Core/Misc |
| `test_live_acceptance_monorepo_uvx_docker.py` | 3 | Core/Misc |
| `test_live_acceptance_npm_global_scanner.py` | 2 | Core/Misc |
| `test_live_acceptance_python_class_tools.py` | 2 | Core/Misc |
| `test_live_acceptance_regional_multilingual.py` | 5 | Core/Misc |
| `test_live_acceptance_rust_systems.py` | 3 | Core/Misc |
| `test_live_ast_openapi_zero_tool_parsers.py` | 9 | Core/Misc |
| `test_live_canonicalizer_snapshot_invariants.py` | 5 | Core/Misc |
| `test_live_cli_sandbox_invariants.py` | 10 | Core/Misc |
| `test_live_clusters.py` | 4 | Core/Misc |
| `test_live_config_scanner_tamper_drift.py` | 4 | Core/Misc |
| `test_live_matcher_search_invariants.py` | 5 | Core/Misc |
| `test_master_audit_conformance.py` | 1 | Core/Misc |
| `test_models_and_canonicalizer.py` | 6 | Core/Misc |
| `test_monorepo_prober.py` | 2 | Probers |
| `test_network_guard.py` | 4 | Core/Misc |
| `test_npm_tarball_batcher.py` | 2 | Core/Misc |
| `test_npm_tarball_extractor.py` | 3 | Core/Misc |
| `test_official_go_sdk_parser.py` | 11 | Core/Misc |
| `test_openapi_parser.py` | 4 | Core/Misc |
| `test_packaging_metadata.py` | 3 | Core/Misc |
| `test_pages_workflow.py` | 1 | Core/Misc |
| `test_parallel_synchronizer.py` | 1 | Core/Misc |
| `test_parallel_validator.py` | 1 | Core/Misc |
| `test_passport_invariants.py` | 13 | Core/Misc |
| `test_passport_quality_remedies.py` | 6 | Core/Misc |
| `test_passport_template_conformance.py` | 2 | Core/Misc |
| `test_prober.py` | 2 | Probers |
| `test_protocol_validator.py` | 12 | Core/Misc |
| `test_pwa_and_virtualization.py` | 3 | Core/Misc |
| `test_pydantic_ast_parser.py` | 4 | AST |
| `test_pypi_extractor.py` | 5 | Core/Misc |
| `test_python_complex_tools.py` | 5 | AST |
| `test_reindex_golang_passports.py` | 1 | Core/Misc |
| `test_reindex_sdk_passports.py` | 9 | Core/Misc |
| `test_remote_gateway_detector.py` | 5 | Probers |
| `test_remote_transports.py` | 6 | Core/Misc |
| `test_reporter.py` | 4 | Core/Misc |
| `test_resilient_ingestion.py` | 4 | Core/Misc |
| `test_runtime_sandbox.py` | 5 | Probers |
| `test_sbom_exporter.py` | 4 | Scanner |
| `test_schema_validator.py` | 2 | Core/Misc |
| `test_scratch_sanitizer.py` | 1 | Core/Misc |
| `test_search.py` | 5 | Matcher |
| `test_semantic_index_builder.py` | 2 | Core/Misc |
| `test_semantic_search.py` | 4 | Matcher |
| `test_snapshot.py` | 1 | Core/Misc |
| `test_snapshot_diff.py` | 3 | Core/Misc |
| `test_snapshot_diff_cli.py` | 1 | Core/Misc |
| `test_source_data_varieties.py` | 8 | Core/Misc |
| `test_sync_embeddings.py` | 4 | Core/Misc |
| `test_sync_updates_and_release.py` | 6 | Core/Misc |
| `test_synchronizer_docker_polyglot.py` | 3 | Core/Misc |
| `test_synchronizer_enrichment.py` | 4 | Core/Misc |
| `test_synchronizer_multiregistry.py` | 4 | Core/Misc |
| `test_tombstoning.py` | 5 | Core/Misc |
| `test_tui.py` | 4 | TUI |
| `test_tui_hub_sbom_export.py` | 4 | TUI |
| `test_typescript_complex_tools.py` | 5 | AST |
| `test_wave_8_task_specifications.py` | 2 | Core/Misc |
| `test_web_catalog.py` | 20 | Core/Misc |
| `test_wizard.py` | 4 | CLI |
| `test_zero_tool_remedies.py` | 4 | Core/Misc |


## 2. Missing Scenario Analysis

The following failure modes, scenarios, and uncommon patterns were identified as undertested or missing from the current suite:

- [ ] **Unusual language patterns in legacy languages or obscure dialects.**
- [ ] **Complex nested generics in strongly typed languages not handled perfectly by regex.**
- [ ] **Simulated network drops in middle of HTTP/SSE stream parsing.**
- [ ] **Malformed JSON inputs to standard IO probers.**
- [ ] **Deeply nested recursion limits on AST parsers.**
- [ ] **Timeout edge cases (exact millisecond boundaries) on slow stdio MCP servers.**


## 3. Network Isolation Guard Audit

The `tests/conftest.py` file uses an explicit `network_guard` autouse fixture to monkey-patch `socket.socket.connect`.

* **Socket Blocking**: Enforced effectively. Any outbound connection to hosts other than `127.0.0.1`, `::1`, or `localhost` raises a `RuntimeError`.
* **Zero Unmocked Leaks**: Verified. The test suite correctly identifies mocked connections, and the test run ensures zero unmocked leaks unless explicitly marked with `@pytest.mark.network` or `@pytest.mark.integration`.

## 4. Negative Testing & Boundary Values

Current gaps and focus areas for negative testing include:

- Network Guard enforcement preventing real socket calls.
- Timeout limits on sandbox causing exact terminations.
- Malformed/Invalid JSON-RPC payloads crashing endpoints.
- Missing binaries/executables handling gracefully.


## 5. Recommended Update Tasks

1. **Enhance AST Fuzzing**: Integrate property-based testing (e.g., Hypothesis) to generate random, deeply nested source code structures.
2. **Hardening Stream Probers**: Write specific tests injecting simulated TCP resets and partial JSON frame delivery for HTTP/SSE transports.
3. **Strict Timeout Boundaries**: Create mock stdio executables that stall precisely at timeout limits to verify `RuntimeSandbox` kill behavior.
