# Master Empirical Research Audit & Remediation Roadmap

## 1. Executive Summary

- **Total candidates audited:** 1000
- **Global Coverage Ratio:** Present: 117 (11.7%), Missing: 883 (88.3%)

### Group-by-group comparative matrix
| Group | Total | Present | Missing | Present % |
|-------|-------|---------|---------|-----------|
| rust_systems | 200 | 0 | 200 | 0.0% |
| go_cloud_native | 200 | 35 | 165 | 17.5% |
| jvm_dotnet_enterprise | 200 | 0 | 200 | 0.0% |
| regional_international | 200 | 13 | 187 | 6.5% |
| monorepo_docker_emerging | 200 | 69 | 131 | 34.5% |

## 2. Systemic Root-Cause Taxonomy & Failure Analysis

### Issue Types Breakdown
| Issue Type | Count | Percentage | Severity |
|------------|-------|------------|----------|
| MISSING_REGISTRY_INDEXER_PKG_GO_DEV | 157 | 17.8% | High |
| MISSING_GITHUB_TOPICS | 150 | 17.0% | High |
| AST_UNSUPPORTED_SDK_MACRO | 146 | 16.5% | High |
| UVX_STANDALONE_SCRIPT | 129 | 14.6% | High |
| MISSING_REGISTRY_INDEXER_CRATES_IO | 84 | 9.5% | High |
| MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | 75 | 8.5% | High |
| KEYWORD_TAG_MISMATCH | 56 | 6.3% | High |
| NON_ENGLISH_METADATA_FILTER | 27 | 3.1% | Medium |
| BINARY_CONTAINER_ONLY | 25 | 2.8% | Medium |
| MONOREPO_NESTED_PATH | 23 | 2.6% | Medium |
| CUSTOM_COMMUNITY_SDK | 9 | 1.0% | Low |
| ENTERPRISE_VENDOR_WRAPPER | 1 | 0.1% | Low |
| REGIONAL_PLATFORM_ECOSYSTEM | 1 | 0.1% | Low |

### Deep Dive into Failure Modes

The failure modes observed highlight critical gaps in the current AST and crawling pipelines:
- **`rmcp` Rust macros & Custom SDKs**: The current crawler focuses strictly on standard AST parsing of functions but fails to recognize or evaluate declarative macros used by libraries like `rmcp` in Rust.
- **`mark3labs/mcp-go`**: Go code utilizing `mcp-go` SDK constructs tools using custom builder patterns that the current standard AST parsing does not explicitly track.
- **Spring AI `@Tool`**: In JVM/Java ecosystems, annotations drive runtime behavior. The static analysis is missing support for parsing and evaluating Spring AI annotations like `@Tool`.
- **PEP 723 `# /// script` headers**: Python scripts utilizing the emerging PEP 723 specification embed dependencies in comment blocks, which aren't typically evaluated by older AST parsing methods looking primarily at `requirements.txt` or `pyproject.toml`.
- **Registry Indexer Misses**: Many tools are published on custom indices or miss conventional tagging.


## 3. Comprehensive Master Audit Catalog Table

| MCP Name | Group | Location | Status | Issue Type | Specific Technical Remedy |
|---|---|---|---|---|---|
| mcp | rust_systems | https://crates.io/crates/mcp | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rust-mcp-sdk | rust_systems | https://crates.io/crates/rust-mcp-sdk | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| brontes | rust_systems | https://crates.io/crates/brontes | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| clap-mcp | rust_systems | https://crates.io/crates/clap-mcp | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| mcp-attr | rust_systems | https://crates.io/crates/mcp-attr | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| mcp-attr-macros | rust_systems | https://crates.io/crates/mcp-attr-macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| pmcp | rust_systems | https://crates.io/crates/pmcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcp-host | rust_systems | https://crates.io/crates/mcp-host | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| dravr-tronc | rust_systems | https://crates.io/crates/dravr-tronc | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| computer-use-linux | rust_systems | https://crates.io/crates/computer-use-linux | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| rust-mcp-macros | rust_systems | https://crates.io/crates/rust-mcp-macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| rust-mcp-schema | rust_systems | https://crates.io/crates/rust-mcp-schema | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| turul-mcp-protocol | rust_systems | https://crates.io/crates/turul-mcp-protocol | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| rmcp | rust_systems | https://crates.io/crates/rmcp | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rmcp-macros | rust_systems | https://crates.io/crates/rmcp-macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| ultrafast-mcp | rust_systems | https://crates.io/crates/ultrafast-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| adk-mcp-sdk | rust_systems | https://crates.io/crates/adk-mcp-sdk | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| tokensave | rust_systems | https://crates.io/crates/tokensave | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| mcp-repl | rust_systems | https://crates.io/crates/mcp-repl | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| embacle | rust_systems | https://crates.io/crates/embacle | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| pmat | rust_systems | https://crates.io/crates/pmat | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| smg-mcp | rust_systems | https://crates.io/crates/smg-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| turul-mcp-client | rust_systems | https://crates.io/crates/turul-mcp-client | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| rag-rat-mcp | rust_systems | https://crates.io/crates/rag-rat-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| tauri-plugin-hushlor-mcp-bridge | rust_systems | https://crates.io/crates/tauri-plugin-hushlor-mcp-bridge | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| rust-mcp-axum | rust_systems | https://crates.io/crates/rust-mcp-axum | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| pmcp-macros | rust_systems | https://crates.io/crates/pmcp-macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| sylphx-mcp-kit | rust_systems | https://crates.io/crates/sylphx-mcp-kit | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| tauri-plugin-mcp-bridge | rust_systems | https://crates.io/crates/tauri-plugin-mcp-bridge | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| arete-mcp | rust_systems | https://crates.io/crates/arete-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| fastmcp-protocol | rust_systems | https://crates.io/crates/fastmcp-protocol | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| fastmcp-client | rust_systems | https://crates.io/crates/fastmcp-client | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| fastmcp-server | rust_systems | https://crates.io/crates/fastmcp-server | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| fastmcp-rust | rust_systems | https://crates.io/crates/fastmcp-rust | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| turbomcp-protocol | rust_systems | https://crates.io/crates/turbomcp-protocol | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| fastmcp-core | rust_systems | https://crates.io/crates/fastmcp-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| fastmcp-transport | rust_systems | https://crates.io/crates/fastmcp-transport | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| fastmcp-derive | rust_systems | https://crates.io/crates/fastmcp-derive | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| tower-mcp-types | rust_systems | https://crates.io/crates/tower-mcp-types | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcp-protocol-sdk | rust_systems | https://crates.io/crates/mcp-protocol-sdk | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| rag-rat-base | rust_systems | https://crates.io/crates/rag-rat-base | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| rag-rat-db | rust_systems | https://crates.io/crates/rag-rat-db | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| rag-rat-papertrail | rust_systems | https://crates.io/crates/rag-rat-papertrail | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rag-rat-query | rust_systems | https://crates.io/crates/rag-rat-query | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rag-rat-clones | rust_systems | https://crates.io/crates/rag-rat-clones | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rag-rat-llm | rust_systems | https://crates.io/crates/rag-rat-llm | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rag-rat-oplog | rust_systems | https://crates.io/crates/rag-rat-oplog | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rag-rat-oracle | rust_systems | https://crates.io/crates/rag-rat-oracle | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rag-rat-dream | rust_systems | https://crates.io/crates/rag-rat-dream | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| rag-rat-core | rust_systems | https://crates.io/crates/rag-rat-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| adk-tool | rust_systems | https://crates.io/crates/adk-tool | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| cedar-policy-mcp-schema-generator | rust_systems | https://crates.io/crates/cedar-policy-mcp-schema-generator | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| endpoint-libs | rust_systems | https://crates.io/crates/endpoint-libs | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| trusty-memory | rust_systems | https://crates.io/crates/trusty-memory | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| rust-mcp-transport | rust_systems | https://crates.io/crates/rust-mcp-transport | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| tower-mcp | rust_systems | https://crates.io/crates/tower-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcp-core | rust_systems | https://crates.io/crates/mcp-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| kmp-mcp | rust_systems | https://crates.io/crates/kmp-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| assay-mcp-server | rust_systems | https://crates.io/crates/assay-mcp-server | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| katana-markdown-linter | rust_systems | https://crates.io/crates/katana-markdown-linter | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| hexser | rust_systems | https://crates.io/crates/hexser | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| trusty-mcp | rust_systems | https://crates.io/crates/trusty-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| surrealdb-mcp | rust_systems | https://crates.io/crates/surrealdb-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| aprender-mcp | rust_systems | https://crates.io/crates/aprender-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| symgraph | rust_systems | https://crates.io/crates/symgraph | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| knot | rust_systems | https://crates.io/crates/knot | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| cratestack-mcp | rust_systems | https://crates.io/crates/cratestack-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| rmcp-openapi | rust_systems | https://crates.io/crates/rmcp-openapi | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| turul-mcp-protocol-2025-11-25 | rust_systems | https://crates.io/crates/turul-mcp-protocol-2025-11-25 | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| model-context-protocol | rust_systems | https://crates.io/crates/model-context-protocol | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| rust-analyzer-mcp | rust_systems | https://crates.io/crates/rust-analyzer-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| harness-rs-mcp-client | rust_systems | https://crates.io/crates/harness-rs-mcp-client | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| turbomcp | rust_systems | https://crates.io/crates/turbomcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| vtcode-mcp | rust_systems | https://crates.io/crates/vtcode-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| trustee | rust_systems | https://crates.io/crates/trustee | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| omni-dev | rust_systems | https://crates.io/crates/omni-dev | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| ljos | rust_systems | https://crates.io/crates/ljos | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| egui_mcp | rust_systems | https://crates.io/crates/egui_mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcp-methods | rust_systems | https://crates.io/crates/mcp-methods | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| agentkit-mcp | rust_systems | https://crates.io/crates/agentkit-mcp | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| agent-config | rust_systems | https://crates.io/crates/agent-config | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| a3s-use | rust_systems | https://crates.io/crates/a3s-use | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| ppt-rs | rust_systems | https://crates.io/crates/ppt-rs | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| arbor-mcp | rust_systems | https://crates.io/crates/arbor-mcp | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| chematic-mcp | rust_systems | https://crates.io/crates/chematic-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| kglite-mcp-server | rust_systems | https://crates.io/crates/kglite-mcp-server | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| mcpkit | rust_systems | https://crates.io/crates/mcpkit | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| hwpforge-foundation | rust_systems | https://crates.io/crates/hwpforge-foundation | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| hwpforge-blueprint | rust_systems | https://crates.io/crates/hwpforge-blueprint | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| hwpforge-smithy-hwpx | rust_systems | https://crates.io/crates/hwpforge-smithy-hwpx | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| agent-client-protocol-rmcp | rust_systems | https://crates.io/crates/agent-client-protocol-rmcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| greentic-mcp-client | rust_systems | https://crates.io/crates/greentic-mcp-client | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| nu-mcp | rust_systems | https://crates.io/crates/nu-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| loctree | rust_systems | https://crates.io/crates/loctree | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-evidence | rust_systems | https://crates.io/crates/assay-evidence | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-core | rust_systems | https://crates.io/crates/assay-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| assay-policy | rust_systems | https://crates.io/crates/assay-policy | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-metrics | rust_systems | https://crates.io/crates/assay-metrics | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-adapter-api | rust_systems | https://crates.io/crates/assay-adapter-api | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-runner-schema | rust_systems | https://crates.io/crates/assay-runner-schema | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-sim | rust_systems | https://crates.io/crates/assay-sim | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-registry | rust_systems | https://crates.io/crates/assay-registry | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| assay-runner-core | rust_systems | https://crates.io/crates/assay-runner-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| rmcp-actix-web | rust_systems | https://crates.io/crates/rmcp-actix-web | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| llmy-types | rust_systems | https://crates.io/crates/llmy-types | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| llmy-tokenizer | rust_systems | https://crates.io/crates/llmy-tokenizer | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| llmy-client | rust_systems | https://crates.io/crates/llmy-client | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| llmy-agent-derive | rust_systems | https://crates.io/crates/llmy-agent-derive | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| llmy-agent | rust_systems | https://crates.io/crates/llmy-agent | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| llmy-agent-tools | rust_systems | https://crates.io/crates/llmy-agent-tools | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| llmy-harness | rust_systems | https://crates.io/crates/llmy-harness | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| llmy-clap | rust_systems | https://crates.io/crates/llmy-clap | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| prism-mcp-rs | rust_systems | https://crates.io/crates/prism-mcp-rs | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| turbomcp-telemetry | rust_systems | https://crates.io/crates/turbomcp-telemetry | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| aether-mcp-servers | rust_systems | https://crates.io/crates/aether-mcp-servers | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| systemprompt-mcp | rust_systems | https://crates.io/crates/systemprompt-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| greentic-mcp | rust_systems | https://crates.io/crates/greentic-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| dirge-agent | rust_systems | https://crates.io/crates/dirge-agent | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| oak-mcp | rust_systems | https://crates.io/crates/oak-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| greentic-mcp-dev | rust_systems | https://crates.io/crates/greentic-mcp-dev | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| worbrow | rust_systems | https://crates.io/crates/worbrow | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| bevy_brp_mcp | rust_systems | https://crates.io/crates/bevy_brp_mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| ikigai-mcp | rust_systems | https://crates.io/crates/ikigai-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| velesdb-memory | rust_systems | https://crates.io/crates/velesdb-memory | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| claude-agent-sdk-rs | rust_systems | https://crates.io/crates/claude-agent-sdk-rs | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| turbomcp-auth | rust_systems | https://crates.io/crates/turbomcp-auth | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcport | rust_systems | https://crates.io/crates/mcport | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| codex-wrapper | rust_systems | https://crates.io/crates/codex-wrapper | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| mur-common | rust_systems | https://crates.io/crates/mur-common | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| stateknot-core | rust_systems | https://crates.io/crates/stateknot-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| stateknot-integrations | rust_systems | https://crates.io/crates/stateknot-integrations | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| pctx_code_mode | rust_systems | https://crates.io/crates/pctx_code_mode | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| agentmesh-mcp | rust_systems | https://crates.io/crates/agentmesh-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| trusty-search | rust_systems | https://crates.io/crates/trusty-search | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| kodegen_mcp_schema | rust_systems | https://crates.io/crates/kodegen_mcp_schema | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| greentic-mcp-exec | rust_systems | https://crates.io/crates/greentic-mcp-exec | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| incurs | rust_systems | https://crates.io/crates/incurs | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| turul-mcp-schema-validation | rust_systems | https://crates.io/crates/turul-mcp-schema-validation | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| greentic-mcp-exec-dev | rust_systems | https://crates.io/crates/greentic-mcp-exec-dev | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| embacle-mcp | rust_systems | https://crates.io/crates/embacle-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| sdforge | rust_systems | https://crates.io/crates/sdforge | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| docling-cli | rust_systems | https://crates.io/crates/docling-cli | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| agentgear-derive | rust_systems | https://crates.io/crates/agentgear-derive | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| agentgear | rust_systems | https://crates.io/crates/agentgear | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| async-mcp | rust_systems | https://crates.io/crates/async-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcp_rust_sdk | rust_systems | https://crates.io/crates/mcp_rust_sdk | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcp-sdk-rs | rust_systems | https://crates.io/crates/mcp-sdk-rs | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcp-tools-sdk | rust_systems | https://crates.io/crates/mcp-tools-sdk | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| vastlint-core | rust_systems | https://crates.io/crates/vastlint-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| everruns-mcp | rust_systems | https://crates.io/crates/everruns-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| ultrafast-mcp-core | rust_systems | https://crates.io/crates/ultrafast-mcp-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| ultrafast-mcp-transport | rust_systems | https://crates.io/crates/ultrafast-mcp-transport | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| ultrafast-mcp-monitoring | rust_systems | https://crates.io/crates/ultrafast-mcp-monitoring | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| ultrafast-mcp-auth | rust_systems | https://crates.io/crates/ultrafast-mcp-auth | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| ultrafast-mcp-server | rust_systems | https://crates.io/crates/ultrafast-mcp-server | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| ultrafast-mcp-client | rust_systems | https://crates.io/crates/ultrafast-mcp-client | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| kurir | rust_systems | https://crates.io/crates/kurir | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| typeduck-codex-utils-rustls-provider | rust_systems | https://crates.io/crates/typeduck-codex-utils-rustls-provider | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| mcp-core-macros | rust_systems | https://crates.io/crates/mcp-core-macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| vastlint-cli | rust_systems | https://crates.io/crates/vastlint-cli | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| tmcp-macros | rust_systems | https://crates.io/crates/tmcp-macros | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| tmcp | rust_systems | https://crates.io/crates/tmcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| io-harness | rust_systems | https://crates.io/crates/io-harness | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcplease | rust_systems | https://crates.io/crates/mcplease | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| heliosdb-nano | rust_systems | https://crates.io/crates/heliosdb-nano | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| uteke-core | rust_systems | https://crates.io/crates/uteke-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| zendriver-mcp | rust_systems | https://crates.io/crates/zendriver-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| ed-mcp | rust_systems | https://crates.io/crates/ed-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| areev-mcp | rust_systems | https://crates.io/crates/areev-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mistralrs-mcp | rust_systems | https://crates.io/crates/mistralrs-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| opentdf | rust_systems | https://crates.io/crates/opentdf | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| beads_rust | rust_systems | https://crates.io/crates/beads_rust | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| greentic-dev | rust_systems | https://crates.io/crates/greentic-dev | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| greentic-dev-dev | rust_systems | https://crates.io/crates/greentic-dev-dev | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| tower-mcp-macros | rust_systems | https://crates.io/crates/tower-mcp-macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| mcp-session | rust_systems | https://crates.io/crates/mcp-session | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| yantrikdb | rust_systems | https://crates.io/crates/yantrikdb | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| inference-gateway-sdk | rust_systems | https://crates.io/crates/inference-gateway-sdk | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| agent-client-protocol | rust_systems | https://crates.io/crates/agent-client-protocol | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| docling-core | rust_systems | https://crates.io/crates/docling-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| docling-pdf | rust_systems | https://crates.io/crates/docling-pdf | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| ruskel-mcp | rust_systems | https://crates.io/crates/ruskel-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| turbomcp-transport | rust_systems | https://crates.io/crates/turbomcp-transport | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| docling-onnx | rust_systems | https://crates.io/crates/docling-onnx | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| docling-asr | rust_systems | https://crates.io/crates/docling-asr | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| trusty-common | rust_systems | https://crates.io/crates/trusty-common | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| tagpath | rust_systems | https://crates.io/crates/tagpath | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| onde-mistralrs-mcp | rust_systems | https://crates.io/crates/onde-mistralrs-mcp | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| turul-mcp-protocol-2026-07-28 | rust_systems | https://crates.io/crates/turul-mcp-protocol-2026-07-28 | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| nanocodex-tools | rust_systems | https://crates.io/crates/nanocodex-tools | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| ebook-rs | rust_systems | https://crates.io/crates/ebook-rs | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| mcpkit-macros | rust_systems | https://crates.io/crates/mcpkit-macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| xberg-cli | rust_systems | https://crates.io/crates/xberg-cli | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| bevy_brp_mcp_macros | rust_systems | https://crates.io/crates/bevy_brp_mcp_macros | Missing | AST_UNSUPPORTED_SDK_MACRO | Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros. |
| anyrepair | rust_systems | https://crates.io/crates/anyrepair | Missing | BINARY_CONTAINER_ONLY | Add binary probing for Rust CLI tools using stdio fallback. |
| aethershell | rust_systems | https://crates.io/crates/aethershell | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| agent-bridle | rust_systems | https://crates.io/crates/agent-bridle | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| blazingly-json | rust_systems | https://crates.io/crates/blazingly-json | Missing | KEYWORD_TAG_MISMATCH | Expand crawler queries. |
| cc-audit | rust_systems | https://crates.io/crates/cc-audit | Missing | MISSING_REGISTRY_INDEXER_CRATES_IO | Implement a Crates.io registry crawler targeting the 'mcp' keyword. |
| arbor-core | rust_systems | https://crates.io/crates/arbor-core | Missing | MONOREPO_NESTED_PATH | Implement recursive Cargo workspace scanning to index sub-crates appropriately. |
| github-mcp-server | go_cloud_native | https://github.com/github/github-mcp-server | Present |  |  |
| whatsapp-mcp | go_cloud_native | https://github.com/lharries/whatsapp-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-toolbox | go_cloud_native | https://github.com/googleapis/mcp-toolbox | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-grafana | go_cloud_native | https://github.com/grafana/mcp-grafana | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kubernetes-mcp-server | go_cloud_native | https://github.com/containers/kubernetes-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| slack-mcp-server | go_cloud_native | https://github.com/korotovsky/slack-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp | go_cloud_native | https://github.com/neo4j/mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| terraform-mcp-server | go_cloud_native | https://github.com/hashicorp/terraform-mcp-server | Present |  |  |
| matlab-mcp-server | go_cloud_native | https://github.com/matlab/matlab-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-language-server | go_cloud_native | https://github.com/isaacphi/mcp-language-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| excel-mcp-server | go_cloud_native | https://github.com/negokaz/excel-mcp-server | Present |  |  |
| registry | go_cloud_native | https://github.com/modelcontextprotocol/registry | Present |  |  |
| mcp-proxy | go_cloud_native | https://github.com/tbxark/mcp-proxy | Present |  |  |
| mcp-filesystem-server | go_cloud_native | https://github.com/mark3labs/mcp-filesystem-server | Missing | AST_UNSUPPORTED_SDK_MACRO | AST parser enhancements for mark3labs/mcp-go tool registrations. |
| MCPJungle | go_cloud_native | https://github.com/mcpjungle/MCPJungle | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kite-mcp-server | go_cloud_native | https://github.com/zerodha/kite-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| db-mcp-server | go_cloud_native | https://github.com/FreePeak/db-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-k8s-go | go_cloud_native | https://github.com/strowk/mcp-k8s-go | Present |  |  |
| go-sdk | go_cloud_native | https://github.com/modelcontextprotocol/go-sdk | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| render-mcp-server | go_cloud_native | https://github.com/render-oss/render-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcptools | go_cloud_native | https://github.com/f/mcptools | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| whatsapp-mcp | go_cloud_native | https://github.com/verygoodplugins/whatsapp-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-link | go_cloud_native | https://github.com/automation-ai-labs/mcp-link | Present |  |  |
| annas-mcp | go_cloud_native | https://github.com/iosifache/annas-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcprouter | go_cloud_native | https://github.com/chatmcp/mcprouter | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp | go_cloud_native | https://github.com/Teamwork/mcp | Present |  |  |
| mcp-golang | go_cloud_native | https://github.com/metoro-io/mcp-golang | Missing | AST_UNSUPPORTED_SDK_MACRO | AST parser enhancements for mark3labs/mcp-go tool registrations. |
| razorpay-mcp-server | go_cloud_native | https://github.com/razorpay/razorpay-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| nightingale | go_cloud_native | https://github.com/ccfos/nightingale | Present |  |  |
| signoz-mcp-server | go_cloud_native | https://github.com/SigNoz/signoz-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gtm-mcp-server | go_cloud_native | https://github.com/paolobietolini/gtm-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| figma-mcp-go | go_cloud_native | https://github.com/RamenSV/figma-mcp-go | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| clihub | go_cloud_native | https://github.com/thellimist/clihub | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| weather-mcp-server | go_cloud_native | https://github.com/ezh0v/weather-mcp-server | Present |  |  |
| k8s-mcp-server | go_cloud_native | https://github.com/reza-gholizade/k8s-mcp-server | Present |  |  |
| caido-mcp-server | go_cloud_native | https://github.com/c0tton-fluff/caido-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| buildkite-mcp-server | go_cloud_native | https://github.com/buildkite/buildkite-mcp-server | Present |  |  |
| toolhive | go_cloud_native | https://github.com/stacklok/toolhive | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| casdoor | go_cloud_native | https://github.com/casdoor/casdoor | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| loki-mcp | go_cloud_native | https://github.com/grafana/loki-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| yutu | go_cloud_native | https://github.com/eat-pray-ai/yutu | Present |  |  |
| mcp-nomad | go_cloud_native | https://github.com/kocierik/mcp-nomad | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| openapi-to-mcpserver | go_cloud_native | https://github.com/higress-group/openapi-to-mcpserver | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-victoriametrics | go_cloud_native | https://github.com/VictoriaMetrics/mcp-victoriametrics | Present |  |  |
| engram | go_cloud_native | https://github.com/Gentleman-Programming/engram | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-trino | go_cloud_native | https://github.com/tuannvm/mcp-trino | Present |  |  |
| pgedge-postgres-mcp | go_cloud_native | https://github.com/pgEdge/pgedge-postgres-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| one-mcp | go_cloud_native | https://github.com/burugo/one-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| vault-mcp-server | go_cloud_native | https://github.com/hashicorp/vault-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | go_cloud_native | https://github.com/tektoncd/mcp-server | Present |  |  |
| meshery-mcp-server | go_cloud_native | https://github.com/meshery-extensions/meshery-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-dap-server | go_cloud_native | https://github.com/go-delve/mcp-dap-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| openapi-mcp | go_cloud_native | https://github.com/ckanthony/openapi-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ks-mcp-server | go_cloud_native | https://github.com/kubesphere/ks-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| code-sandbox-mcp | go_cloud_native | https://github.com/Automata-Labs-team/code-sandbox-mcp | Missing | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| podman-mcp-server | go_cloud_native | https://github.com/manusa/podman-mcp-server | Missing | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| prometheus-mcp | go_cloud_native | https://github.com/prometheus/prometheus-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| protoc-gen-go-mcp | go_cloud_native | https://github.com/redpanda-data/protoc-gen-go-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kafka-mcp-server | go_cloud_native | https://github.com/tuannvm/kafka-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-auth-proxy | go_cloud_native | https://github.com/sigbit/mcp-auth-proxy | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-forge | go_cloud_native | https://github.com/achetronic/mcp-forge | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-victorialogs | go_cloud_native | https://github.com/VictoriaMetrics/mcp-victorialogs | Present |  |  |
| pgmcp | go_cloud_native | https://github.com/subnetmarco/pgmcp | Present |  |  |
| azure-cosmos-mcp-server-samples | go_cloud_native | https://github.com/AzureCosmosDB/azure-cosmos-mcp-server-samples | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-1c | go_cloud_native | https://github.com/feenlace/mcp-1c | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| reportportal-mcp-server | go_cloud_native | https://github.com/reportportal/reportportal-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-difyworkflow-server | go_cloud_native | https://github.com/gotoolkits/mcp-difyworkflow-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpsnoop | go_cloud_native | https://github.com/kerlenton/mcpsnoop | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| kmcp | go_cloud_native | https://github.com/kagent-dev/kmcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-tts | go_cloud_native | https://github.com/blacktop/mcp-tts | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gateway | go_cloud_native | https://github.com/centralmind/gateway | Present |  |  |
| slack-mcp-client | go_cloud_native | https://github.com/tuannvm/slack-mcp-client | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| swagger-mcp | go_cloud_native | https://github.com/danishjsheikh/swagger-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| metoro-mcp-server | go_cloud_native | https://github.com/metoro-io/metoro-mcp-server | Present |  |  |
| auto-mcp | go_cloud_native | https://github.com/brizzai/auto-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| agentdock | go_cloud_native | https://github.com/uvwt/agentdock | Missing | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| toolhive-catalog | go_cloud_native | https://github.com/stacklok/toolhive-catalog | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-1panel | go_cloud_native | https://github.com/1Panel-dev/mcp-1panel | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server-axiom | go_cloud_native | https://github.com/axiomhq/mcp-server-axiom | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-devtools | go_cloud_native | https://github.com/sammcj/mcp-devtools | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| vision-one-mcp-server | go_cloud_native | https://github.com/trendmicro/vision-one-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-client-go | go_cloud_native | https://github.com/yincongcyincong/mcp-client-go | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| last9-mcp-server | go_cloud_native | https://github.com/last9/last9-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| aks-mcp | go_cloud_native | https://github.com/Azure/aks-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-k6 | go_cloud_native | https://github.com/grafana/mcp-k6 | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| sandbox-mcp | go_cloud_native | https://github.com/pottekkat/sandbox-mcp | Missing | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| xiaozhi-esp32-server-golang | go_cloud_native | https://github.com/hackers365/xiaozhi-esp32-server-golang | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| pixel-mcp | go_cloud_native | https://github.com/willibrandon/pixel-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-k8s | go_cloud_native | https://github.com/silenceper/mcp-k8s | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| skywalking-mcp | go_cloud_native | https://github.com/apache/skywalking-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpgen | go_cloud_native | https://github.com/lyeslabs/mcpgen | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| jellyfin-mcp | go_cloud_native | https://github.com/jaredtrent/jellyfin-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-package-version | go_cloud_native | https://github.com/sammcj/mcp-package-version | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| memory-mcp-server-go | go_cloud_native | https://github.com/okooo5km/memory-mcp-server-go | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-shell | go_cloud_native | https://github.com/sonirico/mcp-shell | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| tunnel-client | go_cloud_native | https://github.com/openai/tunnel-client | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| forgejo-mcp | go_cloud_native | https://github.com/goern/forgejo-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-netbird | go_cloud_native | https://github.com/aantti/mcp-netbird | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gentleman-book-mcp | go_cloud_native | https://github.com/Alan-TheGentleman/gentleman-book-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gmail-mcp-server | go_cloud_native | https://github.com/PaulFidika/gmail-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| lazy-mcp | go_cloud_native | https://github.com/voicetreelab/lazy-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| things-cloud-mcp | go_cloud_native | https://github.com/wbopan/things-cloud-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-lifecycle-operator | go_cloud_native | https://github.com/kubernetes-sigs/mcp-lifecycle-operator | Missing | MONOREPO_NESTED_PATH | Monorepo scanning patterns for Go `/cmd/*` structures. |
| ah-mcp | go_cloud_native | https://github.com/mrserzhan/ah-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-boss-zp | go_cloud_native | https://github.com/namejiahui/mcp-boss-zp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| cpi-mcp-server | go_cloud_native | https://github.com/vadimklimov/cpi-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| n9e-mcp-server | go_cloud_native | https://github.com/n9e/n9e-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| forgejo-mcp | go_cloud_native | https://github.com/raohwork/forgejo-mcp | Present |  |  |
| buttplug-mcp | go_cloud_native | https://github.com/ConAcademy/buttplug-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | go_cloud_native | https://github.com/TencentCloudCommunity/mcp-server | Present |  |  |
| paprika-3-mcp | go_cloud_native | https://github.com/soggycactus/paprika-3-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| miro-mcp-server | go_cloud_native | https://github.com/olgasafonova/miro-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| tsidp | go_cloud_native | https://github.com/tailscale/tsidp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gomcp | go_cloud_native | https://github.com/lightpanda-io/gomcp | Present |  |  |
| kodit | go_cloud_native | https://github.com/helixml/kodit | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gateway | go_cloud_native | https://github.com/hyprmcp/mcp-gateway | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ophis | go_cloud_native | https://github.com/njayp/ophis | Present |  |  |
| godoc-mcp | go_cloud_native | https://github.com/mrjoshuak/godoc-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gateway | go_cloud_native | https://github.com/lucky-aeon/mcp-gateway | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpshim | go_cloud_native | https://github.com/mcpshim/mcpshim | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| github-brain | go_cloud_native | https://github.com/wham/github-brain | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| chip | go_cloud_native | https://github.com/collibra/chip | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mysql-mcp-server | go_cloud_native | https://github.com/askdba/mysql-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-openweather | go_cloud_native | https://github.com/mschneider82/mcp-openweather | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-wecombot-server | go_cloud_native | https://github.com/gotoolkits/mcp-wecombot-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| bitrise-mcp | go_cloud_native | https://github.com/bitrise-io/bitrise-mcp | Present |  |  |
| openings-mcp | go_cloud_native | https://github.com/amikai/openings-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| oauth-mcp-proxy | go_cloud_native | https://github.com/tuannvm/oauth-mcp-proxy | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-front | go_cloud_native | https://github.com/stainless-api/mcp-front | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| trivy-mcp | go_cloud_native | https://github.com/aquasecurity/trivy-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcpeserver | go_cloud_native | https://github.com/codehz/mcpeserver | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ontap-mcp | go_cloud_native | https://github.com/NetApp/ontap-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| langcare-mcp-fhir | go_cloud_native | https://github.com/langcare/langcare-mcp-fhir | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| md2wechat-mcp-server | go_cloud_native | https://github.com/geekjourneyx/md2wechat-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| tasker-mcp | go_cloud_native | https://github.com/dceluis/tasker-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gopls | go_cloud_native | https://github.com/hloiseau/mcp-gopls | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| litmus-mcp-server | go_cloud_native | https://github.com/litmuschaos/litmus-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| agent-lsp | go_cloud_native | https://github.com/blackwell-systems/agent-lsp | Present |  |  |
| chronosphere-mcp | go_cloud_native | https://github.com/chronosphereio/chronosphere-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-cron | go_cloud_native | https://github.com/jolks/mcp-cron | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-nutanix | go_cloud_native | https://github.com/thunderboltsid/mcp-nutanix | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| FastDomainCheck-MCP-Server | go_cloud_native | https://github.com/bingal/FastDomainCheck-MCP-Server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ovn-kubernetes-mcp | go_cloud_native | https://github.com/ovn-kubernetes/ovn-kubernetes-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| linkwarden-mcp-server | go_cloud_native | https://github.com/irfansofyana/linkwarden-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | go_cloud_native | https://github.com/perses/mcp-server | Present |  |  |
| fritzbox-mcp-server | go_cloud_native | https://github.com/kambriso/fritzbox-mcp-server | Present |  |  |
| tempo-mcp-server | go_cloud_native | https://github.com/grafana-cold-storage/tempo-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gitlab-mcp-server | go_cloud_native | https://github.com/jmrplens/gitlab-mcp-server | Present |  |  |
| osv-mcp | go_cloud_native | https://github.com/StacklokLabs/osv-mcp | Present |  |  |
| mcp-google-spreadsheet | go_cloud_native | https://github.com/kazz187/mcp-google-spreadsheet | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-kubernetes | go_cloud_native | https://github.com/Azure/mcp-kubernetes | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| api-wrapper-mcp | go_cloud_native | https://github.com/gomcpgo/api-wrapper-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| go-mcp-mysql | go_cloud_native | https://github.com/Zhwt/go-mcp-mysql | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| SecureMCP | go_cloud_native | https://github.com/makalin/SecureMCP | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mediawiki-mcp-server | go_cloud_native | https://github.com/olgasafonova/mediawiki-mcp-server | Present |  |  |
| teamcity-mcp | go_cloud_native | https://github.com/itcaat/teamcity-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-prompt-server-go | go_cloud_native | https://github.com/smallnest/mcp-prompt-server-go | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-nats | go_cloud_native | https://github.com/sinadarbouy/mcp-nats | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| streamnative-mcp-server | go_cloud_native | https://github.com/streamnative/streamnative-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gameguardian-mcp-server | go_cloud_native | https://github.com/giaoimgiao/gameguardian-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| feed-mcp | go_cloud_native | https://github.com/richardwooding/feed-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| minibridge | go_cloud_native | https://github.com/acuvity/minibridge | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| lfx-mcp | go_cloud_native | https://github.com/linuxfoundation/lfx-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| powhttp-mcp | go_cloud_native | https://github.com/usestring/powhttp-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| gemara-mcp | go_cloud_native | https://github.com/gemaraproj/gemara-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| toolhive-registry-server | go_cloud_native | https://github.com/stacklok/toolhive-registry-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| ig-mcp-server | go_cloud_native | https://github.com/inspektor-gadget/ig-mcp-server | Missing | BINARY_CONTAINER_ONLY | Support parsing binary / container images directly. |
| agent-memory-mcp | go_cloud_native | https://github.com/ipiton/agent-memory-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-zero | go_cloud_native | https://github.com/zeromicro/mcp-zero | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gopls | go_cloud_native | https://github.com/Yantrio/mcp-gopls | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server | go_cloud_native | https://github.com/aaPanel/mcp-server | Present |  |  |
| mcp-k8s-eye | go_cloud_native | https://github.com/wenhuwang/mcp-k8s-eye | Present |  |  |
| xiaoyuzhoufm-mcp | go_cloud_native | https://github.com/MosesHe/xiaoyuzhoufm-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| godoc-mcp-server | go_cloud_native | https://github.com/yikakia/godoc-mcp-server | Present |  |  |
| gentle-ai | go_cloud_native | https://github.com/Gentleman-Programming/gentle-ai | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| xk6-mcp | go_cloud_native | https://github.com/grafana/xk6-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-tradovate | go_cloud_native | https://github.com/0xjmp/mcp-tradovate | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| umami-mcp-server | go_cloud_native | https://github.com/Macawls/umami-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-gitee | go_cloud_native | https://github.com/oschina/mcp-gitee | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| asgardeo-mcp-server | go_cloud_native | https://github.com/asgardeo/asgardeo-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-oauth-proxy | go_cloud_native | https://github.com/drpebcak/mcp-oauth-proxy | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp | go_cloud_native | https://github.com/DepsHubHQ/mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-unreal | go_cloud_native | https://github.com/remiphilippe/mcp-unreal | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-cyclops | go_cloud_native | https://github.com/cyclops-ui/mcp-cyclops | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| langchaingo-mcp-adapter | go_cloud_native | https://github.com/i2y/langchaingo-mcp-adapter | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| sysdig-mcp-server | go_cloud_native | https://github.com/sysdiglabs/sysdig-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| obs-mcp | go_cloud_native | https://github.com/rhobs/obs-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| systemd-mcp | go_cloud_native | https://github.com/openSUSE/systemd-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| miniflux-mcp | go_cloud_native | https://github.com/tssujt/miniflux-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| outlook-local-mcp | go_cloud_native | https://github.com/desek/outlook-local-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| altinity-mcp | go_cloud_native | https://github.com/Altinity/altinity-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| opentelemetry-mcp-server | go_cloud_native | https://github.com/pavolloffay/opentelemetry-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-web-ui | go_cloud_native | https://github.com/MegaGrindStone/mcp-web-ui | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| honeybadger-mcp-server | go_cloud_native | https://github.com/honeybadger-io/honeybadger-mcp-server | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| har-mcp | go_cloud_native | https://github.com/tjamet/har-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| things-cloud-mcp | go_cloud_native | https://github.com/mattydsmith/things-cloud-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| dolt-mcp | go_cloud_native | https://github.com/dolthub/dolt-mcp | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| mcp-server-proxy | go_cloud_native | https://github.com/leizongmin/mcp-server-proxy | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| sports-mcp-server | go_cloud_native | https://github.com/cloudbet/sports-mcp-server | Present |  |  |
| dev-machine-guard | go_cloud_native | https://github.com/step-security/dev-machine-guard | Missing | MISSING_REGISTRY_INDEXER_PKG_GO_DEV | Ingestion via Go proxy / GitHub crawler adjustments. |
| GhidraMCP | jvm_dotnet_enterprise | https://github.com/LaurieWired/GhidraMCP | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| ghidra-mcp | jvm_dotnet_enterprise | https://github.com/bethington/ghidra-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| MCProtocolLib | jvm_dotnet_enterprise | https://github.com/GeyserMC/MCProtocolLib | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| jadx-ai-mcp | jvm_dotnet_enterprise | https://github.com/zinja-coder/jadx-ai-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| sonarqube-mcp-server | jvm_dotnet_enterprise | https://github.com/SonarSource/sonarqube-mcp-server | Missing | ENTERPRISE_VENDOR_WRAPPER | Curate seed configurations for vendor enterprise MCP servers. |
| quarkus-mcp-server | jvm_dotnet_enterprise | https://github.com/quarkiverse/quarkus-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| GhidrAssistMCP | jvm_dotnet_enterprise | https://github.com/symgraph/GhidrAssistMCP | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| quarkus-mcp-servers | jvm_dotnet_enterprise | https://github.com/quarkiverse/quarkus-mcp-servers | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-server-plugin | jvm_dotnet_enterprise | https://github.com/jenkinsci/mcp-server-plugin | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| java-sdk | jvm_dotnet_enterprise | https://github.com/modelcontextprotocol/java-sdk | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| alibabacloud-tablestore-mcp-server | jvm_dotnet_enterprise | https://github.com/aliyun/alibabacloud-tablestore-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-mianshiya-server | jvm_dotnet_enterprise | https://github.com/yuyuanweb/mcp-mianshiya-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| discord-mcp | jvm_dotnet_enterprise | https://github.com/SaseQ/discord-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| reverse-engineering-assistant | jvm_dotnet_enterprise | https://github.com/cyberkaida/reverse-engineering-assistant | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| xiaozhi-esp32-server-java | jvm_dotnet_enterprise | https://github.com/joey-zhou/xiaozhi-esp32-server-java | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| eclipse-chatgpt-plugin | jvm_dotnet_enterprise | https://github.com/gradusnikov/eclipse-chatgpt-plugin | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| GhidraMCP | jvm_dotnet_enterprise | https://github.com/13bm/GhidraMCP | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| spine2d-animation-mcp | jvm_dotnet_enterprise | https://github.com/ampersante/spine2d-animation-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| sweethome3d-mcp-server | jvm_dotnet_enterprise | https://github.com/grimashevich/sweethome3d-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| geoserver-mcp | jvm_dotnet_enterprise | https://github.com/mahdin75/geoserver-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-zap-server | jvm_dotnet_enterprise | https://github.com/dtkmn/mcp-zap-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| solr-mcp | jvm_dotnet_enterprise | https://github.com/apache/solr-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| keycloak-mcp-server | jvm_dotnet_enterprise | https://github.com/sshaaf/keycloak-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-codestyle-server | jvm_dotnet_enterprise | https://github.com/itxaiohanglover/mcp-codestyle-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| OsqueryMcpServer | jvm_dotnet_enterprise | https://github.com/kousen/OsqueryMcpServer | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| spring-boot-mcp-server-example | jvm_dotnet_enterprise | https://github.com/sohamkamani/spring-boot-mcp-server-example | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| WeatherMcpServer | jvm_dotnet_enterprise | https://github.com/Cooosin/WeatherMcpServer | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-server-steam | jvm_dotnet_enterprise | https://github.com/dsp/mcp-server-steam | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| tda | jvm_dotnet_enterprise | https://github.com/irockel/tda | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| d360-mcp-server | jvm_dotnet_enterprise | https://github.com/forcedotcom/d360-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-jdbc-server | jvm_dotnet_enterprise | https://github.com/OpenLinkSoftware/mcp-jdbc-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| archi-mcp-server | jvm_dotnet_enterprise | https://github.com/fanievh/archi-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| spring-rest-to-mcp | jvm_dotnet_enterprise | https://github.com/addozhang/spring-rest-to-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| jadx-mcp-server | jvm_dotnet_enterprise | https://github.com/Qtty/jadx-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| plinth | jvm_dotnet_enterprise | https://github.com/jabrena/plinth | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| api2mcp4j | jvm_dotnet_enterprise | https://github.com/TheEterna/api2mcp4j | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-nullbr-server | jvm_dotnet_enterprise | https://github.com/chenglu1129/mcp-nullbr-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| spring-documentation-mcp-server | jvm_dotnet_enterprise | https://github.com/akvdevav/spring-documentation-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| beehiiv-mcp-server | jvm_dotnet_enterprise | https://github.com/danvega/beehiiv-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| MCProxyCommand | jvm_dotnet_enterprise | https://github.com/michiruf/MCProxyCommand | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-server-weather | jvm_dotnet_enterprise | https://github.com/yestarz/mcp-server-weather | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| druid-mcp-server | jvm_dotnet_enterprise | https://github.com/iunera/druid-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| lets-learn-mcp-java | jvm_dotnet_enterprise | https://github.com/microsoft/lets-learn-mcp-java | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| infobip-openapi-mcp | jvm_dotnet_enterprise | https://github.com/infobip/infobip-openapi-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| oracle-mcp-server | jvm_dotnet_enterprise | https://github.com/yyue9527/oracle-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| WigAI | jvm_dotnet_enterprise | https://github.com/fabb/WigAI | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| wildfly-mcp | jvm_dotnet_enterprise | https://github.com/wildfly-extras/wildfly-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| javalens-mcp | jvm_dotnet_enterprise | https://github.com/pzalutski-pixel/javalens-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-contrast | jvm_dotnet_enterprise | https://github.com/Contrast-Security-OSS/mcp-contrast | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-mysql-server | jvm_dotnet_enterprise | https://github.com/JamesSmith888/mcp-mysql-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-annotated-java-sdk | jvm_dotnet_enterprise | https://github.com/thought2code/mcp-annotated-java-sdk | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mysql-mcp-server-java | jvm_dotnet_enterprise | https://github.com/kioyong/mysql-mcp-server-java | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| eclipse-mcp-server | jvm_dotnet_enterprise | https://github.com/vogellacompany/eclipse-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-springboot-server | jvm_dotnet_enterprise | https://github.com/James-Zou/mcp-springboot-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| sap-adt-mcp-server | jvm_dotnet_enterprise | https://github.com/YahorNovik/sap-adt-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| WxMCPServer | jvm_dotnet_enterprise | https://github.com/IBM/WxMCPServer | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| quarkus-agent-mcp | jvm_dotnet_enterprise | https://github.com/quarkusio/quarkus-agent-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| jolokia-mcp-server | jvm_dotnet_enterprise | https://github.com/jolokia/jolokia-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-java-sdk-examples | jvm_dotnet_enterprise | https://github.com/thought2code/mcp-java-sdk-examples | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| workday-mcp-server-by-cdata | jvm_dotnet_enterprise | https://github.com/CDataSoftware/workday-mcp-server-by-cdata | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| jvm-mcp | jvm_dotnet_enterprise | https://github.com/oscarbol09/jvm-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| GeminiMcpServer | jvm_dotnet_enterprise | https://github.com/kousen/GeminiMcpServer | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| openstack-mcp-server | jvm_dotnet_enterprise | https://github.com/DragomirAlin/openstack-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| IBM-AS-400-ISeries-MCP-Server | jvm_dotnet_enterprise | https://github.com/abstracta/IBM-AS-400-ISeries-MCP-Server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| LSP4J-MCP | jvm_dotnet_enterprise | https://github.com/stephanj/LSP4J-MCP | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-chess | jvm_dotnet_enterprise | https://github.com/alexandreroman/mcp-chess | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| metersphere-mcp-server | jvm_dotnet_enterprise | https://github.com/metersphere/metersphere-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcpal-bedrock | jvm_dotnet_enterprise | https://github.com/raphaellueckl/mcpal-bedrock | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-server-spring-java | jvm_dotnet_enterprise | https://github.com/mtwn105/mcp-server-spring-java | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| maven-tools-mcp | jvm_dotnet_enterprise | https://github.com/arvindand/maven-tools-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| gh_mcp_server | jvm_dotnet_enterprise | https://github.com/kousen/gh_mcp_server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| astah-pro-mcp | jvm_dotnet_enterprise | https://github.com/takaakit/astah-pro-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| ones-wiki-mcp-server | jvm_dotnet_enterprise | https://github.com/brianxiadong/ones-wiki-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-server-ra2-jdbc | jvm_dotnet_enterprise | https://github.com/balejosg/mcp-server-ra2-jdbc | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| burp-mcp-bridge | jvm_dotnet_enterprise | https://github.com/fwaeytens/burp-mcp-bridge | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| tencent-send-article-mcp-server | jvm_dotnet_enterprise | https://github.com/yangbuyiya/tencent-send-article-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| quickbooks-mcp-server-by-cdata | jvm_dotnet_enterprise | https://github.com/CDataSoftware/quickbooks-mcp-server-by-cdata | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mockserver-monorepo | jvm_dotnet_enterprise | https://github.com/mock-server/mockserver-monorepo | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| sap-business-one-mcp-server-by-cdata | jvm_dotnet_enterprise | https://github.com/CDataSoftware/sap-business-one-mcp-server-by-cdata | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| BurpMCP | jvm_dotnet_enterprise | https://github.com/N0el4kLs/BurpMCP | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| netsuite-mcp-server-by-cdata | jvm_dotnet_enterprise | https://github.com/CDataSoftware/netsuite-mcp-server-by-cdata | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| llm-sse-mcp-demo-2025 | jvm_dotnet_enterprise | https://github.com/nlinhvu/llm-sse-mcp-demo-2025 | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| jdb-mcp | jvm_dotnet_enterprise | https://github.com/d4n-sec/jdb-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| ghidra-mcp | jvm_dotnet_enterprise | https://github.com/suidpit/ghidra-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| MCP-ASD | jvm_dotnet_enterprise | https://github.com/hoodoer/MCP-ASD | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-jdwp-java | jvm_dotnet_enterprise | https://github.com/FgForrest/mcp-jdwp-java | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-spring-ai-mcp-server | jvm_dotnet_enterprise | https://github.com/chaozai0304/mcp-spring-ai-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| minecraft-java-fabric-mcp-server | jvm_dotnet_enterprise | https://github.com/chapmanjw/minecraft-java-fabric-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| cpage-pivotal__cloud-foundry-mcp | jvm_dotnet_enterprise | https://github.com/mcp-research/cpage-pivotal__cloud-foundry-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| ebay-mcp-server-by-cdata | jvm_dotnet_enterprise | https://github.com/CDataSoftware/ebay-mcp-server-by-cdata | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp-server-demo | jvm_dotnet_enterprise | https://github.com/liqingdong/mcp-server-demo | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| tachyon | jvm_dotnet_enterprise | https://github.com/tachyonmcp/tachyon | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| jenkins-mcp-server | jvm_dotnet_enterprise | https://github.com/ProgrammerAgua/jenkins-mcp-server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| MCPE_Server | jvm_dotnet_enterprise | https://github.com/skyrising/MCPE_Server | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| spring-ai-mcp-server | jvm_dotnet_enterprise | https://github.com/haeseoky/spring-ai-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| spring-ai-mcp-server | jvm_dotnet_enterprise | https://github.com/cagritrk/spring-ai-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| hoverfly-mcp-server | jvm_dotnet_enterprise | https://github.com/kapishmalik/hoverfly-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| vertx-mcp | jvm_dotnet_enterprise | https://github.com/kinotic-ai/vertx-mcp | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| BurpMCP | jvm_dotnet_enterprise | https://github.com/swgee/BurpMCP | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| benchmark-mcp-servers-v2 | jvm_dotnet_enterprise | https://github.com/thiagomendes/benchmark-mcp-servers-v2 | Missing | MISSING_REGISTRY_INDEXER_MAVEN_CENTRAL | Add Maven Central indexer crawler to scripts. |
| mcp | jvm_dotnet_enterprise | https://github.com/microsoft/mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| azure-mcp | jvm_dotnet_enterprise | https://github.com/Azure/azure-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-server-excel | jvm_dotnet_enterprise | https://github.com/sbroenne/mcp-server-excel | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-servers-for-revit | jvm_dotnet_enterprise | https://github.com/mcp-servers-for-revit/mcp-servers-for-revit | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-gateway | jvm_dotnet_enterprise | https://github.com/microsoft/mcp-gateway | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| STS2MCP | jvm_dotnet_enterprise | https://github.com/Gennadiyev/STS2MCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| tiaportal-mcp | jvm_dotnet_enterprise | https://github.com/heilingbrunner/tiaportal-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| csharp-sdk | jvm_dotnet_enterprise | https://github.com/modelcontextprotocol/csharp-sdk | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-dotnet-samples | jvm_dotnet_enterprise | https://github.com/microsoft/mcp-dotnet-samples | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| revit-mcp-server | jvm_dotnet_enterprise | https://github.com/LuDattilo/revit-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mssql-mcp | jvm_dotnet_enterprise | https://github.com/Aaronontheweb/mssql-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| MCPSharp | jvm_dotnet_enterprise | https://github.com/afrise/MCPSharp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| memorizer | jvm_dotnet_enterprise | https://github.com/petabridge/memorizer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| remote-mcp-functions-dotnet | jvm_dotnet_enterprise | https://github.com/Azure-Samples/remote-mcp-functions-dotnet | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| FlaUI-MCP | jvm_dotnet_enterprise | https://github.com/shanselman/FlaUI-MCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| rvt-mcp | jvm_dotnet_enterprise | https://github.com/bimwright/rvt-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mssqlclient-mcp-server | jvm_dotnet_enterprise | https://github.com/aadversteeg/mssqlclient-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| Windows-MCP.Net | jvm_dotnet_enterprise | https://github.com/shuyu-labs/Windows-MCP.Net | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| MCPSqlServer | jvm_dotnet_enterprise | https://github.com/ian-cowley/MCPSqlServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| funplay-unity-mcp | jvm_dotnet_enterprise | https://github.com/FunplayAI/funplay-unity-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| ImmichMCP | jvm_dotnet_enterprise | https://github.com/barryw/ImmichMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| PolarionMcpServers | jvm_dotnet_enterprise | https://github.com/peakflames/PolarionMcpServers | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mobile-dev-mcp-server | jvm_dotnet_enterprise | https://github.com/jsuarezruiz/mobile-dev-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| UnityNaturalMCP | jvm_dotnet_enterprise | https://github.com/notargs/UnityNaturalMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| RoslynMcpServer | jvm_dotnet_enterprise | https://github.com/JoshuaRamirez/RoslynMcpServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| QuickMCP | jvm_dotnet_enterprise | https://github.com/gunpal5/QuickMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mssql-mcp-server | jvm_dotnet_enterprise | https://github.com/ConnorBritain/mssql-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| PaperlessMCP | jvm_dotnet_enterprise | https://github.com/barryw/PaperlessMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| MCP-Server-ArcGIS-Pro-AddIn | jvm_dotnet_enterprise | https://github.com/nicogis/MCP-Server-ArcGIS-Pro-AddIn | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| McpServerYouTubeDemo | jvm_dotnet_enterprise | https://github.com/dracan/McpServerYouTubeDemo | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| DotNetMetadataMcpServer | jvm_dotnet_enterprise | https://github.com/V0v1kkk/DotNetMetadataMcpServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| DatabaseMcpServer | jvm_dotnet_enterprise | https://github.com/ttcc666/DatabaseMcpServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| AvaloniaUI.MCP | jvm_dotnet_enterprise | https://github.com/decriptor/AvaloniaUI.MCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| google-keyword-planner-mcp | jvm_dotnet_enterprise | https://github.com/ncosentino/google-keyword-planner-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| MudMCP | jvm_dotnet_enterprise | https://github.com/mcbodge/MudMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| NDepend.MCP.Server | jvm_dotnet_enterprise | https://github.com/ndepend/NDepend.MCP.Server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| NugetMcpServer | jvm_dotnet_enterprise | https://github.com/DimonSmart/NugetMcpServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| WzImg-MCP-Server | jvm_dotnet_enterprise | https://github.com/lastbattle/WzImg-MCP-Server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| rhinoMcpServer | jvm_dotnet_enterprise | https://github.com/always-tinkering/rhinoMcpServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| UnityMCP-VRC | jvm_dotnet_enterprise | https://github.com/swax/UnityMCP-VRC | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| GameDev-MCP-Server | jvm_dotnet_enterprise | https://github.com/IvanMurzak/GameDev-MCP-Server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| VS-MCPServer | jvm_dotnet_enterprise | https://github.com/CodingWithCalvin/VS-MCPServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| dajet-mcp-server | jvm_dotnet_enterprise | https://github.com/zhichkin/dajet-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| RoslynMCP | jvm_dotnet_enterprise | https://github.com/carquiza/RoslynMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| tia-portal-openness-mcpserver | jvm_dotnet_enterprise | https://github.com/chewcw/tia-portal-openness-mcpserver | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| aps-aecdm-mcp-dotnet | jvm_dotnet_enterprise | https://github.com/autodesk-platform-services/aps-aecdm-mcp-dotnet | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| resharper-mcp | jvm_dotnet_enterprise | https://github.com/joshua-light/resharper-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp_xpp | jvm_dotnet_enterprise | https://github.com/ccampora/mcp_xpp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| Genexus18MCP | jvm_dotnet_enterprise | https://github.com/lennix1337/Genexus18MCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| seq-mcp-server | jvm_dotnet_enterprise | https://github.com/willibrandon/seq-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| PerformanceMonitor | jvm_dotnet_enterprise | https://github.com/erikdarlingdata/PerformanceMonitor | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| Unofficial-VS-MCP | jvm_dotnet_enterprise | https://github.com/dhq-boiler/Unofficial-VS-MCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| MCPServerPS | jvm_dotnet_enterprise | https://github.com/daxian-dbw/MCPServerPS | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| openapi-to-mcp | jvm_dotnet_enterprise | https://github.com/criteo/openapi-to-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-ms-sql-server | jvm_dotnet_enterprise | https://github.com/0xhubed/mcp-ms-sql-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| TiaMcp | jvm_dotnet_enterprise | https://github.com/rickgaiser/TiaMcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-afl-server | jvm_dotnet_enterprise | https://github.com/willvelida/mcp-afl-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| aspose-mcp-server | jvm_dotnet_enterprise | https://github.com/xjustloveux/aspose-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-server-graph-api | jvm_dotnet_enterprise | https://github.com/MartinM85/mcp-server-graph-api | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| revit-mcp-server | jvm_dotnet_enterprise | https://github.com/schauh11/revit-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| skunit | jvm_dotnet_enterprise | https://github.com/mehrandvd/skunit | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| DecompilerServer | jvm_dotnet_enterprise | https://github.com/pardeike/DecompilerServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| roslyn-codelens-mcp | jvm_dotnet_enterprise | https://github.com/MarcelRoozekrans/roslyn-codelens-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| MCPE.AlphaServer | jvm_dotnet_enterprise | https://github.com/atipls/MCPE.AlphaServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| dnspy-mcp | jvm_dotnet_enterprise | https://github.com/soufianetahiri/dnspy-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| sharplens-mcp | jvm_dotnet_enterprise | https://github.com/pzalutski-pixel/sharplens-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-server-powerpoint | jvm_dotnet_enterprise | https://github.com/sbroenne/mcp-server-powerpoint | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| debug-mcp | jvm_dotnet_enterprise | https://github.com/jkolo/debug-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| unity-mcp-server | jvm_dotnet_enterprise | https://github.com/nurture-tech/unity-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| sjtu-mcp-server | jvm_dotnet_enterprise | https://github.com/SJTU-Geek/sjtu-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| SimpleMcp.Demo | jvm_dotnet_enterprise | https://github.com/hassanhabib/SimpleMcp.Demo | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| RiMCP_hybrid | jvm_dotnet_enterprise | https://github.com/h7lu/RiMCP_hybrid | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| twincat-mcp | jvm_dotnet_enterprise | https://github.com/eponce00/twincat-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| PerformanceStudio | jvm_dotnet_enterprise | https://github.com/erikdarlingdata/PerformanceStudio | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| csharp-lsp-mcp | jvm_dotnet_enterprise | https://github.com/HYMMA/csharp-lsp-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| re-engine-mcp | jvm_dotnet_enterprise | https://github.com/praydog/re-engine-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| PowerShell.MCP | jvm_dotnet_enterprise | https://github.com/yotsuda/PowerShell.MCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| RimBridgeServer | jvm_dotnet_enterprise | https://github.com/pardeike/RimBridgeServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| windbg-mcp | jvm_dotnet_enterprise | https://github.com/memoryforensics1/windbg-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| lubelog_mcp | jvm_dotnet_enterprise | https://github.com/hargata/lubelog_mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| S08-E01-MCP-Server | jvm_dotnet_enterprise | https://github.com/binarythistle/S08-E01-MCP-Server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcpbi | jvm_dotnet_enterprise | https://github.com/jonaolden/mcpbi | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mssqlMCP | jvm_dotnet_enterprise | https://github.com/MCPRUNNER/mssqlMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| Ozmium-MCP-Server-for-Sbox | jvm_dotnet_enterprise | https://github.com/ozmium7/Ozmium-MCP-Server-for-Sbox | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| RoslynMcp | jvm_dotnet_enterprise | https://github.com/MadQ/RoslynMcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| outsystems11-mcp | jvm_dotnet_enterprise | https://github.com/OutSystems/outsystems11-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| aps-sample-mcp-server-revit-automation | jvm_dotnet_enterprise | https://github.com/autodesk-platform-services/aps-sample-mcp-server-revit-automation | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| mcp-server-for-revit-dotnet | jvm_dotnet_enterprise | https://github.com/mcp-servers-for-revit/mcp-server-for-revit-dotnet | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| tsql-mcp-server | jvm_dotnet_enterprise | https://github.com/Popplywop/tsql-mcp-server | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| tutorial-mcp-server-dotnet | jvm_dotnet_enterprise | https://github.com/mehrandvd/tutorial-mcp-server-dotnet | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| desktop-pilot-mcp | jvm_dotnet_enterprise | https://github.com/floatingbrij/desktop-pilot-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| calendar-mcp | jvm_dotnet_enterprise | https://github.com/MarimerLLC/calendar-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| postg-mem | jvm_dotnet_enterprise | https://github.com/dariogriffo/postg-mem | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| DotnetMCPServer | jvm_dotnet_enterprise | https://github.com/andreluizsecco/DotnetMCPServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| D365BCAdminMCP | jvm_dotnet_enterprise | https://github.com/demiliani/D365BCAdminMCP | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| dax-formatter-mcp | jvm_dotnet_enterprise | https://github.com/EmanueleMeazzo/dax-formatter-mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| Greg.Xrm.Mcp | jvm_dotnet_enterprise | https://github.com/neronotte/Greg.Xrm.Mcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| MCP-SqlServer | jvm_dotnet_enterprise | https://github.com/RodrigoPAml/MCP-SqlServer | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| WPFVisualTreeMcp | jvm_dotnet_enterprise | https://github.com/faze79/WPFVisualTreeMcp | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| Yamu | jvm_dotnet_enterprise | https://github.com/keijiro/Yamu | Missing | AST_UNSUPPORTED_SDK_MACRO | Add AST parser support for Spring AI @Tool and C# [McpServerTool]/[KernelFunction]. |
| @playwright/mcp | regional_international | https://www.npmjs.com/package/@playwright/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @hono/mcp | regional_international | https://www.npmjs.com/package/@hono/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @upstash/context7-mcp | regional_international | https://www.npmjs.com/package/@upstash/context7-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| hostinger-api-mcp | regional_international | https://www.npmjs.com/package/hostinger-api-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @ai-sdk/mcp | regional_international | https://www.npmjs.com/package/@ai-sdk/mcp | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| chrome-devtools-mcp | regional_international | https://www.npmjs.com/package/chrome-devtools-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @storybook/mcp | regional_international | https://www.npmjs.com/package/@storybook/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @supabase/mcp-utils | regional_international | https://www.npmjs.com/package/@supabase/mcp-utils | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @better-auth/mcp | regional_international | https://www.npmjs.com/package/@better-auth/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @langchain/mcp-adapters | regional_international | https://www.npmjs.com/package/@langchain/mcp-adapters | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mcp-ui/client | regional_international | https://www.npmjs.com/package/@mcp-ui/client | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| @mobilenext/mobile-mcp | regional_international | https://www.npmjs.com/package/@mobilenext/mobile-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mcp-use/inspector | regional_international | https://www.npmjs.com/package/@mcp-use/inspector | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-proxy | regional_international | https://www.npmjs.com/package/mcp-proxy | Present |  |  |
| @deepseek-ai/dsh-mcp-client | regional_international | https://www.npmjs.com/package/@deepseek-ai/dsh-mcp-client | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @currents/mcp | regional_international | https://www.npmjs.com/package/@currents/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mcp-ui/server | regional_international | https://www.npmjs.com/package/@mcp-ui/server | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| pi-mcp-extension | regional_international | https://www.npmjs.com/package/pi-mcp-extension | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| n8n-nodes-mcp | regional_international | https://www.npmjs.com/package/n8n-nodes-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| add-mcp | regional_international | https://www.npmjs.com/package/add-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @notionhq/notion-mcp-server | regional_international | https://www.npmjs.com/package/@notionhq/notion-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| pi-mcp-adapter | regional_international | https://www.npmjs.com/package/pi-mcp-adapter | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @aikidosec/mcp | regional_international | https://www.npmjs.com/package/@aikidosec/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @eslint/mcp | regional_international | https://www.npmjs.com/package/@eslint/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @sap-ux/fiori-mcp-server | regional_international | https://www.npmjs.com/package/@sap-ux/fiori-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @modelcontextprotocol/ext-apps | regional_international | https://www.npmjs.com/package/@modelcontextprotocol/ext-apps | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @browsermcp/mcp | regional_international | https://www.npmjs.com/package/@browsermcp/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| agentation-mcp | regional_international | https://www.npmjs.com/package/agentation-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @clerk/mcp-tools | regional_international | https://www.npmjs.com/package/@clerk/mcp-tools | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @payloadcms/plugin-mcp | regional_international | https://www.npmjs.com/package/@payloadcms/plugin-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @ui5/mcp-server | regional_international | https://www.npmjs.com/package/@ui5/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @rekog/mcp-nest | regional_international | https://www.npmjs.com/package/@rekog/mcp-nest | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @posthog/mcp | regional_international | https://www.npmjs.com/package/@posthog/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @pandacss/mcp | regional_international | https://www.npmjs.com/package/@pandacss/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @azure-devops/mcp | regional_international | https://www.npmjs.com/package/@azure-devops/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-searxng | regional_international | https://www.npmjs.com/package/mcp-searxng | Present |  |  |
| @traceloop/instrumentation-mcp | regional_international | https://www.npmjs.com/package/@traceloop/instrumentation-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @azure/mcp | regional_international | https://www.npmjs.com/package/@azure/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @shortcut/mcp | regional_international | https://www.npmjs.com/package/@shortcut/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @hubspot/mcp-server | regional_international | https://www.npmjs.com/package/@hubspot/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @ag-ui/mcp-apps-middleware | regional_international | https://www.npmjs.com/package/@ag-ui/mcp-apps-middleware | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @larksuiteoapi/lark-mcp | regional_international | https://www.npmjs.com/package/@larksuiteoapi/lark-mcp | Missing | REGIONAL_PLATFORM_ECOSYSTEM | Add specific search query tags for these ecosystems. |
| @expo/mcp-tunnel | regional_international | https://www.npmjs.com/package/@expo/mcp-tunnel | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @hostinger/mcp | regional_international | https://www.npmjs.com/package/@hostinger/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| argocd-mcp | regional_international | https://www.npmjs.com/package/argocd-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @apify/actors-mcp-server | regional_international | https://www.npmjs.com/package/@apify/actors-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-admin | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-admin | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @togglhq/mcp | regional_international | https://www.npmjs.com/package/@togglhq/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-workflows | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-workflows | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| mcp-hello-world | regional_international | https://www.npmjs.com/package/mcp-hello-world | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @browserstack/mcp-server | regional_international | https://www.npmjs.com/package/@browserstack/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| n8n-mcp | regional_international | https://www.npmjs.com/package/n8n-mcp | Present |  |  |
| @sentry/mcp-server | regional_international | https://www.npmjs.com/package/@sentry/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @deepseek-ai/dsh-mcp-resources | regional_international | https://www.npmjs.com/package/@deepseek-ai/dsh-mcp-resources | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @n8n/mcp-apps | regional_international | https://www.npmjs.com/package/@n8n/mcp-apps | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @discourse/mcp | regional_international | https://www.npmjs.com/package/@discourse/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @modelcontextprotocol/server-everything | regional_international | https://www.npmjs.com/package/@modelcontextprotocol/server-everything | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| workers-mcp | regional_international | https://www.npmjs.com/package/workers-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| next-devtools-mcp | regional_international | https://www.npmjs.com/package/next-devtools-mcp | Present |  |  |
| expo-mcp | regional_international | https://www.npmjs.com/package/expo-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-framework | regional_international | https://www.npmjs.com/package/mcp-framework | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp | regional_international | https://www.npmjs.com/package/@transcend-io/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @smartbear/mcp | regional_international | https://www.npmjs.com/package/@smartbear/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @automattic/mcp-wordpress-remote | regional_international | https://www.npmjs.com/package/@automattic/mcp-wordpress-remote | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @zereight/mcp-gitlab | regional_international | https://www.npmjs.com/package/@zereight/mcp-gitlab | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @wonderwhy-er/desktop-commander | regional_international | https://www.npmjs.com/package/@wonderwhy-er/desktop-commander | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mastra/mcp-docs-server | regional_international | https://www.npmjs.com/package/@mastra/mcp-docs-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| excalidraw-mcp | regional_international | https://www.npmjs.com/package/excalidraw-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @openai/mcp-extensions | regional_international | https://www.npmjs.com/package/@openai/mcp-extensions | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @salesforce/mcp | regional_international | https://www.npmjs.com/package/@salesforce/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mcp-b/webmcp-ts-sdk | regional_international | https://www.npmjs.com/package/@mcp-b/webmcp-ts-sdk | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| @amplitude/mcp-analytics | regional_international | https://www.npmjs.com/package/@amplitude/mcp-analytics | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| @mui/mcp | regional_international | https://www.npmjs.com/package/@mui/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @typia/mcp | regional_international | https://www.npmjs.com/package/@typia/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @drawio/mcp | regional_international | https://www.npmjs.com/package/@drawio/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-inventory | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-inventory | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @letoribo/mcp-graphql-enhanced | regional_international | https://www.npmjs.com/package/@letoribo/mcp-graphql-enhanced | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| kubernetes-mcp-server | regional_international | https://www.npmjs.com/package/kubernetes-mcp-server | Present |  |  |
| @mcp-b/transports | regional_international | https://www.npmjs.com/package/@mcp-b/transports | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @agimon-ai/mcp-proxy | regional_international | https://www.npmjs.com/package/@agimon-ai/mcp-proxy | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| resend-mcp | regional_international | https://www.npmjs.com/package/resend-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @modelcontextprotocol/server-filesystem | regional_international | https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| tavily-mcp | regional_international | https://www.npmjs.com/package/tavily-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @knip/mcp | regional_international | https://www.npmjs.com/package/@knip/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @univerjs-pro/mcp | regional_international | https://www.npmjs.com/package/@univerjs-pro/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @theia/ai-mcp | regional_international | https://www.npmjs.com/package/@theia/ai-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-dsr | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-dsr | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| mcp-use | regional_international | https://www.npmjs.com/package/mcp-use | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| @digitalocean/mcp | regional_international | https://www.npmjs.com/package/@digitalocean/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| fastmcp | regional_international | https://www.npmjs.com/package/fastmcp | Present |  |  |
| @transcend-io/mcp-server-docs | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-docs | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| tiny-http-mcp-server | regional_international | https://www.npmjs.com/package/tiny-http-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @heroku/mcp-server | regional_international | https://www.npmjs.com/package/@heroku/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @goke/mcp | regional_international | https://www.npmjs.com/package/@goke/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-assessment | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-assessment | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @ericthered926/duckduckgo-mcp-server | regional_international | https://www.npmjs.com/package/@ericthered926/duckduckgo-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @iobroker/mcp-server | regional_international | https://www.npmjs.com/package/@iobroker/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @zencoderai/slack-mcp-server | regional_international | https://www.npmjs.com/package/@zencoderai/slack-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @brightdata/mcp | regional_international | https://www.npmjs.com/package/@brightdata/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @vercel/mcp-adapter | regional_international | https://www.npmjs.com/package/@vercel/mcp-adapter | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @winor30/mcp-server-datadog | regional_international | https://www.npmjs.com/package/@winor30/mcp-server-datadog | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-echo-server | regional_international | https://www.npmjs.com/package/mcp-echo-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-image | regional_international | https://www.npmjs.com/package/mcp-image | Present |  |  |
| @sveltejs/mcp | regional_international | https://www.npmjs.com/package/@sveltejs/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @productbrain/mcp | regional_international | https://www.npmjs.com/package/@productbrain/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @primeuix/mcp | regional_international | https://www.npmjs.com/package/@primeuix/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mcpmarket/mcp-auto-install | regional_international | https://www.npmjs.com/package/@mcpmarket/mcp-auto-install | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @cap-js/mcp-server | regional_international | https://www.npmjs.com/package/@cap-js/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @google-cloud/observability-mcp | regional_international | https://www.npmjs.com/package/@google-cloud/observability-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| scryfall-mcp-server | regional_international | https://www.npmjs.com/package/scryfall-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-evals | regional_international | https://www.npmjs.com/package/mcp-evals | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-lite | regional_international | https://www.npmjs.com/package/mcp-lite | Present |  |  |
| @shopify/dev-mcp | regional_international | https://www.npmjs.com/package/@shopify/dev-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mcp-use/cli | regional_international | https://www.npmjs.com/package/@mcp-use/cli | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| freee-mcp | regional_international | https://www.npmjs.com/package/freee-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @gongrzhe/server-gmail-autoauth-mcp | regional_international | https://www.npmjs.com/package/@gongrzhe/server-gmail-autoauth-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @tpsdev-ai/flair-mcp | regional_international | https://www.npmjs.com/package/@tpsdev-ai/flair-mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @google-cloud/gcloud-mcp | regional_international | https://www.npmjs.com/package/@google-cloud/gcloud-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @siemens/element-mcp | regional_international | https://www.npmjs.com/package/@siemens/element-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @youdotcom-oss/mcp | regional_international | https://www.npmjs.com/package/@youdotcom-oss/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @azure/mcp-darwin-arm64 | regional_international | https://www.npmjs.com/package/@azure/mcp-darwin-arm64 | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @descope/mcp-express | regional_international | https://www.npmjs.com/package/@descope/mcp-express | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| @transloadit/mcp-server | regional_international | https://www.npmjs.com/package/@transloadit/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| openapi-mcp-generator | regional_international | https://www.npmjs.com/package/openapi-mcp-generator | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @univerjs-pro/sheets-mcp | regional_international | https://www.npmjs.com/package/@univerjs-pro/sheets-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @netlify/mcp | regional_international | https://www.npmjs.com/package/@netlify/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @transcend-io/mcp-server-consent | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-consent | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @transcend-io/mcp-server-discovery | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-discovery | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @google-cloud/storage-mcp | regional_international | https://www.npmjs.com/package/@google-cloud/storage-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @gleanwork/mcp-config-schema | regional_international | https://www.npmjs.com/package/@gleanwork/mcp-config-schema | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @primeng/mcp | regional_international | https://www.npmjs.com/package/@primeng/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @gleanwork/mcp-config-glean | regional_international | https://www.npmjs.com/package/@gleanwork/mcp-config-glean | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @agentmemory/mcp | regional_international | https://www.npmjs.com/package/@agentmemory/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @abbit/abbit-mcp | regional_international | https://www.npmjs.com/package/@abbit/abbit-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-preferences | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-preferences | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @primer/mcp | regional_international | https://www.npmjs.com/package/@primer/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| document-mcp | regional_international | https://www.npmjs.com/package/document-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @anthropic-ai/mcpb | regional_international | https://www.npmjs.com/package/@anthropic-ai/mcpb | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| playwright-mcp-advanced | regional_international | https://www.npmjs.com/package/playwright-mcp-advanced | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-policy | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-policy | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @ahrefs/mcp | regional_international | https://www.npmjs.com/package/@ahrefs/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| ios-simulator-mcp | regional_international | https://www.npmjs.com/package/ios-simulator-mcp | Present |  |  |
| @phenomenalorg/mcp | regional_international | https://www.npmjs.com/package/@phenomenalorg/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @kubb/mcp | regional_international | https://www.npmjs.com/package/@kubb/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| rsbuild-plugin-vue-mcp | regional_international | https://www.npmjs.com/package/rsbuild-plugin-vue-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @structured-world/gitlab-mcp | regional_international | https://www.npmjs.com/package/@structured-world/gitlab-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mantine/mcp-server | regional_international | https://www.npmjs.com/package/@mantine/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @bitwarden/mcp-server | regional_international | https://www.npmjs.com/package/@bitwarden/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @infisical/mcp | regional_international | https://www.npmjs.com/package/@infisical/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @agimon-ai/log-sink-mcp | regional_international | https://www.npmjs.com/package/@agimon-ai/log-sink-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @claude-flow/mcp | regional_international | https://www.npmjs.com/package/@claude-flow/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @turbopuffer/turbopuffer-mcp | regional_international | https://www.npmjs.com/package/@turbopuffer/turbopuffer-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| hlims-mcp | regional_international | https://www.npmjs.com/package/hlims-mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| mcp-server-kubernetes | regional_international | https://www.npmjs.com/package/mcp-server-kubernetes | Present |  |  |
| @qase/mcp-server | regional_international | https://www.npmjs.com/package/@qase/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @azure/mcp-linux-x64 | regional_international | https://www.npmjs.com/package/@azure/mcp-linux-x64 | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @runpod/mcp-server | regional_international | https://www.npmjs.com/package/@runpod/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @dokploy/mcp | regional_international | https://www.npmjs.com/package/@dokploy/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @n8n/mcp-browser | regional_international | https://www.npmjs.com/package/@n8n/mcp-browser | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @cyanheads/mcp-ts-core | regional_international | https://www.npmjs.com/package/@cyanheads/mcp-ts-core | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| opencode-mcp | regional_international | https://www.npmjs.com/package/opencode-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-base | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-base | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @stripe/mcp | regional_international | https://www.npmjs.com/package/@stripe/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @google-cloud/cloud-run-mcp | regional_international | https://www.npmjs.com/package/@google-cloud/cloud-run-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @agentistics/mcp | regional_international | https://www.npmjs.com/package/@agentistics/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @nextscope/mcp | regional_international | https://www.npmjs.com/package/@nextscope/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| xmcp | regional_international | https://www.npmjs.com/package/xmcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @palisadeemail/mcp | regional_international | https://www.npmjs.com/package/@palisadeemail/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @azure/mcp-win32-x64 | regional_international | https://www.npmjs.com/package/@azure/mcp-win32-x64 | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @avallon-labs/mcp | regional_international | https://www.npmjs.com/package/@avallon-labs/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @pipeworx/mcp-civitai | regional_international | https://www.npmjs.com/package/@pipeworx/mcp-civitai | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @phantom/mcp-server | regional_international | https://www.npmjs.com/package/@phantom/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @serdnaley/metabase-mcp | regional_international | https://www.npmjs.com/package/@serdnaley/metabase-mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @starreel/mcp | regional_international | https://www.npmjs.com/package/@starreel/mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @dbx-app/mcp-win32-x64 | regional_international | https://www.npmjs.com/package/@dbx-app/mcp-win32-x64 | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @transcend-io/mcp-server-custom-functions | regional_international | https://www.npmjs.com/package/@transcend-io/mcp-server-custom-functions | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| runbios-mcp | regional_international | https://www.npmjs.com/package/runbios-mcp | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| @inkeep/agents-mcp | regional_international | https://www.npmjs.com/package/@inkeep/agents-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-client | regional_international | https://www.npmjs.com/package/mcp-client | Present |  |  |
| @fangjunjie/ssh-mcp-server | regional_international | https://www.npmjs.com/package/@fangjunjie/ssh-mcp-server | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| slite-mcp-server | regional_international | https://www.npmjs.com/package/slite-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @thirdstrandstudio/mcp-figma | regional_international | https://www.npmjs.com/package/@thirdstrandstudio/mcp-figma | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @tocharianou/mcp-server-kibana | regional_international | https://www.npmjs.com/package/@tocharianou/mcp-server-kibana | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| vite-plugin-mcp | regional_international | https://www.npmjs.com/package/vite-plugin-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @tanstack/ai-mcp | regional_international | https://www.npmjs.com/package/@tanstack/ai-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @lovable.dev/mcp-js | regional_international | https://www.npmjs.com/package/@lovable.dev/mcp-js | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @react-aria/mcp | regional_international | https://www.npmjs.com/package/@react-aria/mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @meshy-ai/meshy-mcp-server | regional_international | https://www.npmjs.com/package/@meshy-ai/meshy-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @elgato/mcp-server | regional_international | https://www.npmjs.com/package/@elgato/mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @xeroapi/xero-mcp-server | regional_international | https://www.npmjs.com/package/@xeroapi/xero-mcp-server | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| brightspace-mcp-server | regional_international | https://www.npmjs.com/package/brightspace-mcp-server | Present |  |  |
| openinputbridge-mcp | regional_international | https://www.npmjs.com/package/openinputbridge-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @armature-tech/mcp-analytics | regional_international | https://www.npmjs.com/package/@armature-tech/mcp-analytics | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| @copilotkit/mcp-apps-renderer | regional_international | https://www.npmjs.com/package/@copilotkit/mcp-apps-renderer | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| mcp-auth | regional_international | https://www.npmjs.com/package/mcp-auth | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| supergateway | regional_international | https://www.npmjs.com/package/supergateway | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @postman/postman-mcp-server | regional_international | https://www.npmjs.com/package/@postman/postman-mcp-server | Missing | NON_ENGLISH_METADATA_FILTER | Sanitizer whitelist rules preventing false-positive rejection of international characters. |
| davinci-resolve-mcp | regional_international | https://www.npmjs.com/package/davinci-resolve-mcp | Present |  |  |
| @suthio/redash-mcp | regional_international | https://www.npmjs.com/package/@suthio/redash-mcp | Missing | MISSING_GITHUB_TOPICS | Multilingual search query expansions. |
| @mcp-use/ext-apps | regional_international | https://www.npmjs.com/package/@mcp-use/ext-apps | Missing | CUSTOM_COMMUNITY_SDK | Extend parsers to handle custom JSON-RPC wrappers and community SDKs. |
| mcp | monorepo_docker_emerging | https://github.com/awslabs/mcp | Present |  |  |
| pal-mcp-server | monorepo_docker_emerging | https://github.com/BeehiveInnovations/pal-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-atlassian | monorepo_docker_emerging | https://github.com/sooperset/mcp-atlassian | Present |  |  |
| linkedin-mcp-server | monorepo_docker_emerging | https://github.com/stickerdaniel/linkedin-mcp-server | Present |  |  |
| Windows-MCP | monorepo_docker_emerging | https://github.com/CursorTouch/Windows-MCP | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| excel-mcp-server | monorepo_docker_emerging | https://github.com/haris-musa/excel-mcp-server | Present |  |  |
| mcp-server | monorepo_docker_emerging | https://github.com/financial-datasets/mcp-server | Present |  |  |
| mcpo | monorepo_docker_emerging | https://github.com/open-webui/mcpo | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| arxiv-mcp-server | monorepo_docker_emerging | https://github.com/blazickjp/arxiv-mcp-server | Present |  |  |
| KiCAD-MCP-Server | monorepo_docker_emerging | https://github.com/mixelpixx/KiCAD-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp | monorepo_docker_emerging | https://github.com/baidu-maps/mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-qdrant | monorepo_docker_emerging | https://github.com/qdrant/mcp-server-qdrant | Present |  |  |
| mcp | monorepo_docker_emerging | https://github.com/oracle/mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp | monorepo_docker_emerging | https://github.com/MariaDB/mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| alpaca-mcp-server | monorepo_docker_emerging | https://github.com/alpacahq/alpaca-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| freecad-mcp | monorepo_docker_emerging | https://github.com/neka-nat/freecad-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| cve-mcp-server | monorepo_docker_emerging | https://github.com/mukul975/cve-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mysql_mcp_server | monorepo_docker_emerging | https://github.com/designcomputer/mysql_mcp_server | Present |  |  |
| davinci-resolve-mcp | monorepo_docker_emerging | https://github.com/samuelgursky/davinci-resolve-mcp | Present |  |  |
| garmin_mcp | monorepo_docker_emerging | https://github.com/Taxuspt/garmin_mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| rocketride-server | monorepo_docker_emerging | https://github.com/rocketride-org/rocketride-server | Present |  |  |
| Office-Word-MCP-Server | monorepo_docker_emerging | https://github.com/GongRzhe/Office-Word-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-guide | monorepo_docker_emerging | https://github.com/figma/mcp-server-guide | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| fastmcp | monorepo_docker_emerging | https://github.com/PrefectHQ/fastmcp | Present |  |  |
| metatrader-mcp-server | monorepo_docker_emerging | https://github.com/ariadng/metatrader-mcp-server | Present |  |  |
| ros-mcp-server | monorepo_docker_emerging | https://github.com/robotmcp/ros-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| jupyter-mcp-server | monorepo_docker_emerging | https://github.com/datalayer/jupyter-mcp-server | Present |  |  |
| mcp | monorepo_docker_emerging | https://github.com/Snowflake-Labs/mcp | Present |  |  |
| mcp | monorepo_docker_emerging | https://github.com/semgrep/mcp | Present |  |  |
| elevenlabs-mcp | monorepo_docker_emerging | https://github.com/elevenlabs/elevenlabs-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| duckduckgo-mcp-server | monorepo_docker_emerging | https://github.com/nickclyde/duckduckgo-mcp-server | Present |  |  |
| ha-mcp | monorepo_docker_emerging | https://github.com/homeassistant-ai/ha-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-obsidian | monorepo_docker_emerging | https://github.com/MarkusPfundstein/mcp-obsidian | Present |  |  |
| mcp-brasil | monorepo_docker_emerging | https://github.com/Mcp-Brasil/mcp-brasil | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| MODULAR-RAG-MCP-SERVER | monorepo_docker_emerging | https://github.com/jerry-ai-dev/MODULAR-RAG-MCP-SERVER | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| kubectl-mcp-server | monorepo_docker_emerging | https://github.com/rohitg00/kubectl-mcp-server | Present |  |  |
| damn-vulnerable-MCP-server | monorepo_docker_emerging | https://github.com/harishsg993010/damn-vulnerable-MCP-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| Office-PowerPoint-MCP-Server | monorepo_docker_emerging | https://github.com/GongRzhe/Office-PowerPoint-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| MetasploitMCP | monorepo_docker_emerging | https://github.com/GH05TCREW/MetasploitMCP | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| python-sdk | monorepo_docker_emerging | https://github.com/modelcontextprotocol/python-sdk | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| MCP-Kali-Server | monorepo_docker_emerging | https://github.com/Wh0am123/MCP-Kali-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server | monorepo_docker_emerging | https://github.com/volcengine/mcp-server | Present |  |  |
| mcp | monorepo_docker_emerging | https://github.com/frappe/mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| gemini-notebook-mcp-cli | monorepo_docker_emerging | https://github.com/jacob-bd/gemini-notebook-mcp-cli | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| google_workspace_mcp | monorepo_docker_emerging | https://github.com/taylorwilsdon/google_workspace_mcp | Present |  |  |
| intervals-mcp-server | monorepo_docker_emerging | https://github.com/mvilanova/intervals-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp2cli | monorepo_docker_emerging | https://github.com/knowsuchagency/mcp2cli | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| colab-mcp | monorepo_docker_emerging | https://github.com/googlecolab/colab-mcp | Present |  |  |
| jadx-mcp-server | monorepo_docker_emerging | https://github.com/zinja-coder/jadx-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| polymarket-mcp-server | monorepo_docker_emerging | https://github.com/caiovicentino/polymarket-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-odoo | monorepo_docker_emerging | https://github.com/ivnvxd/mcp-server-odoo | Present |  |  |
| plane-mcp-server | monorepo_docker_emerging | https://github.com/makeplane/plane-mcp-server | Present |  |  |
| servicenow-mcp | monorepo_docker_emerging | https://github.com/echelon-ai-labs/servicenow-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| monarch-mcp-server | monorepo_docker_emerging | https://github.com/robcerda/monarch-mcp-server | Present |  |  |
| mcp-neo4j | monorepo_docker_emerging | https://github.com/neo4j-contrib/mcp-neo4j | Present |  |  |
| tradingview-mcp | monorepo_docker_emerging | https://github.com/atilaahmettaner/tradingview-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| supabase-mcp-server | monorepo_docker_emerging | https://github.com/alexander-zuev/supabase-mcp-server | Present |  |  |
| mcp-server-docker | monorepo_docker_emerging | https://github.com/ckreiling/mcp-server-docker | Present |  |  |
| mcp-email-server | monorepo_docker_emerging | https://github.com/Wh1isper/mcp-email-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| android-mcp-server | monorepo_docker_emerging | https://github.com/minhalvp/android-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| CAD-MCP | monorepo_docker_emerging | https://github.com/daobataotie/CAD-MCP | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| browser-use-mcp-server | monorepo_docker_emerging | https://github.com/kontext-security/browser-use-mcp-server | Present |  |  |
| mssql_mcp_server | monorepo_docker_emerging | https://github.com/RichardHan/mssql_mcp_server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| manim-mcp-server | monorepo_docker_emerging | https://github.com/abhiemj/manim-mcp-server | Present |  |  |
| nanobanana-mcp-server | monorepo_docker_emerging | https://github.com/zhongweili/nanobanana-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| prometheus-mcp-server | monorepo_docker_emerging | https://github.com/pab1it0/prometheus-mcp-server | Present |  |  |
| nextcloud-mcp-server | monorepo_docker_emerging | https://github.com/cbcoutinho/nextcloud-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| Awesome-MCP-Servers | monorepo_docker_emerging | https://github.com/AIAnytime/Awesome-MCP-Servers | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-scanner | monorepo_docker_emerging | https://github.com/cisco-ai-defense/mcp-scanner | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| docker-android | monorepo_docker_emerging | https://github.com/budtmo/docker-android | Missing | BINARY_CONTAINER_ONLY | Docker Hub API crawler for docker-mcp tags. |
| ida-mcp | monorepo_docker_emerging | https://github.com/HexRaysSA/ida-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| telegram-mcp | monorepo_docker_emerging | https://github.com/chigwell/telegram-mcp | Present |  |  |
| mcp-server-motherduck | monorepo_docker_emerging | https://github.com/motherduckdb/mcp-server-motherduck | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| Android-MCP | monorepo_docker_emerging | https://github.com/CursorTouch/Android-MCP | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| doris-mcp-server | monorepo_docker_emerging | https://github.com/apache/doris-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mem-agent-mcp | monorepo_docker_emerging | https://github.com/firstbatchxyz/mem-agent-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| create-python-server | monorepo_docker_emerging | https://github.com/modelcontextprotocol/create-python-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server | monorepo_docker_emerging | https://github.com/strands-agents/mcp-server | Present |  |  |
| apktool-mcp-server | monorepo_docker_emerging | https://github.com/zinja-coder/apktool-mcp-server | Present |  |  |
| mcp-mem0 | monorepo_docker_emerging | https://github.com/coleam00/mcp-mem0 | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| comfyui-mcp-server | monorepo_docker_emerging | https://github.com/joenorton/comfyui-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| netbox-mcp-server | monorepo_docker_emerging | https://github.com/netboxlabs/netbox-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| facebook-ads-mcp-server | monorepo_docker_emerging | https://github.com/gomarble-ai/facebook-ads-mcp-server | Present |  |  |
| openapi-servers | monorepo_docker_emerging | https://github.com/open-webui/openapi-servers | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| arcticdb_mcp | monorepo_docker_emerging | https://github.com/YMuskrat/arcticdb_mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp | monorepo_docker_emerging | https://github.com/arm/mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-solidworks | monorepo_docker_emerging | https://github.com/eyfel/mcp-server-solidworks | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| invisible_playwright_mcp | monorepo_docker_emerging | https://github.com/feder-cr/invisible_playwright_mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| things-mcp | monorepo_docker_emerging | https://github.com/hald/things-mcp | Present |  |  |
| ida-mcp-server | monorepo_docker_emerging | https://github.com/MxIris-Reverse-Engineering/ida-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| zabbix-mcp-server | monorepo_docker_emerging | https://github.com/mpeirone/zabbix-mcp-server | Present |  |  |
| mcp-endpoint-server | monorepo_docker_emerging | https://github.com/xinnan-tech/mcp-endpoint-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| dbt-mcp | monorepo_docker_emerging | https://github.com/dbt-labs/dbt-mcp | Present |  |  |
| xmcp | monorepo_docker_emerging | https://github.com/xdevplatform/xmcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mikrotik-mcp | monorepo_docker_emerging | https://github.com/wiresage/mikrotik-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| facebook-mcp-server | monorepo_docker_emerging | https://github.com/HagaiHen/facebook-mcp-server | Present |  |  |
| MiniMax-MCP | monorepo_docker_emerging | https://github.com/MiniMax-AI/MiniMax-MCP | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| linux-mcp-server | monorepo_docker_emerging | https://github.com/rhel-lightspeed/linux-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-google-sheets | monorepo_docker_emerging | https://github.com/xing5/mcp-google-sheets | Present |  |  |
| mcp-snowflake-server | monorepo_docker_emerging | https://github.com/isaacwasserman/mcp-snowflake-server | Present |  |  |
| mcp-server-12306 | monorepo_docker_emerging | https://github.com/drfccv/mcp-server-12306 | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| elasticsearch-mcp-server | monorepo_docker_emerging | https://github.com/cr7258/elasticsearch-mcp-server | Present |  |  |
| jcodemunch-mcp | monorepo_docker_emerging | https://github.com/jgravelle/jcodemunch-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| django-mcp-server | monorepo_docker_emerging | https://github.com/gts360/django-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| Wazuh-MCP-Server | monorepo_docker_emerging | https://github.com/gensecaihq/Wazuh-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-gsuite | monorepo_docker_emerging | https://github.com/MarkusPfundstein/mcp-gsuite | Present |  |  |
| MCP-Salesforce | monorepo_docker_emerging | https://github.com/smn2gnt/MCP-Salesforce | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| docker-mcp | monorepo_docker_emerging | https://github.com/QuantGeekDev/docker-mcp | Present |  |  |
| mcp-server-milvus | monorepo_docker_emerging | https://github.com/zilliztech/mcp-server-milvus | Present |  |  |
| agent-scan | monorepo_docker_emerging | https://github.com/snyk/agent-scan | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-template | monorepo_docker_emerging | https://github.com/InteractionCo/mcp-server-template | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| arcade-mcp | monorepo_docker_emerging | https://github.com/ArcadeAI/arcade-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-data-exploration | monorepo_docker_emerging | https://github.com/reading-plus-ai/mcp-server-data-exploration | Present |  |  |
| opensearch-mcp-server-py | monorepo_docker_emerging | https://github.com/opensearch-project/opensearch-mcp-server-py | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-foundry | monorepo_docker_emerging | https://github.com/microsoft-foundry/mcp-foundry | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| frida-mcp | monorepo_docker_emerging | https://github.com/dnakov/frida-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp_massive | monorepo_docker_emerging | https://github.com/massive-com/mcp_massive | Present |  |  |
| mcp | monorepo_docker_emerging | https://github.com/baidu-netdisk/mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| zendesk-mcp-server | monorepo_docker_emerging | https://github.com/reminia/zendesk-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| aider-mcp-server | monorepo_docker_emerging | https://github.com/disler/aider-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| aseprite-mcp | monorepo_docker_emerging | https://github.com/diivi/aseprite-mcp | Present |  |  |
| ableton-live-mcp-server | monorepo_docker_emerging | https://github.com/Simon-Kansara/ableton-live-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| unifi-mcp | monorepo_docker_emerging | https://github.com/sirkirby/unifi-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-for-revit-python | monorepo_docker_emerging | https://github.com/mcp-servers-for-revit/mcp-server-for-revit-python | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| freecad-addon-robust-mcp-server | monorepo_docker_emerging | https://github.com/spkane/freecad-addon-robust-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-proxy-for-aws | monorepo_docker_emerging | https://github.com/aws/mcp-proxy-for-aws | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| pg-mcp-server | monorepo_docker_emerging | https://github.com/stuzero/pg-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| Google-Scholar-MCP-Server | monorepo_docker_emerging | https://github.com/JackKuo666/Google-Scholar-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| data-go-mcp-servers | monorepo_docker_emerging | https://github.com/Koomook/data-go-mcp-servers | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| gimp-mcp | monorepo_docker_emerging | https://github.com/maorcc/gimp-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-starrocks | monorepo_docker_emerging | https://github.com/StarRocks/mcp-server-starrocks | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mealie-mcp-server | monorepo_docker_emerging | https://github.com/rldiao/mealie-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-metatrader5-server | monorepo_docker_emerging | https://github.com/Qoyyuum/mcp-metatrader5-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| unifi-mcp-server | monorepo_docker_emerging | https://github.com/enuno/unifi-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| supabase-mcp | monorepo_docker_emerging | https://github.com/coleam00/supabase-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-datahub | monorepo_docker_emerging | https://github.com/acryldata/mcp-server-datahub | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcpm.sh | monorepo_docker_emerging | https://github.com/pathintegral-institute/mcpm.sh | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| sample-serverless-mcp-servers | monorepo_docker_emerging | https://github.com/aws-samples/sample-serverless-mcp-servers | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| Drissionpage-MCP-Server | monorepo_docker_emerging | https://github.com/jumodada/Drissionpage-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| zabbix-mcp-server | monorepo_docker_emerging | https://github.com/initMAX/zabbix-mcp-server | Present |  |  |
| mcp-server | monorepo_docker_emerging | https://github.com/kubeflow/mcp-server | Present |  |  |
| chroma-mcp | monorepo_docker_emerging | https://github.com/chroma-core/chroma-mcp | Present |  |  |
| mcp-teams-server | monorepo_docker_emerging | https://github.com/InditexTech/mcp-teams-server | Present |  |  |
| sec-edgar-mcp | monorepo_docker_emerging | https://github.com/stefanoamorelli/sec-edgar-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| oracle-mcp-server | monorepo_docker_emerging | https://github.com/danielmeppiel/oracle-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-example | monorepo_docker_emerging | https://github.com/alejandro-ao/mcp-server-example | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-youtube-transcript | monorepo_docker_emerging | https://github.com/jkawamoto/mcp-youtube-transcript | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| Custom-MCP-Server | monorepo_docker_emerging | https://github.com/Sharan-Kumar-R/Custom-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-pandoc | monorepo_docker_emerging | https://github.com/vivekVells/mcp-pandoc | Present |  |  |
| xiyan_mcp_server | monorepo_docker_emerging | https://github.com/XGenerationLab/xiyan_mcp_server | Present |  |  |
| mcp-server-synology | monorepo_docker_emerging | https://github.com/atom2ueki/mcp-server-synology | Missing | BINARY_CONTAINER_ONLY | Docker Hub API crawler for docker-mcp tags. |
| portainer-mcp | monorepo_docker_emerging | https://github.com/portainer/portainer-mcp | Present |  |  |
| Lambda-MCP-Server | monorepo_docker_emerging | https://github.com/mikegc-aws/Lambda-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| borsa-mcp | monorepo_docker_emerging | https://github.com/saidsurucu/borsa-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-shell-server | monorepo_docker_emerging | https://github.com/tumf/mcp-shell-server | Present |  |  |
| kicad-mcp | monorepo_docker_emerging | https://github.com/lamaalrajih/kicad-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| fhir-mcp-server | monorepo_docker_emerging | https://github.com/wso2/fhir-mcp-server | Present |  |  |
| mcp-apache-spark-history-server | monorepo_docker_emerging | https://github.com/kubeflow/mcp-apache-spark-history-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| web-eval-agent | monorepo_docker_emerging | https://github.com/refreshdotdev/web-eval-agent | Present |  |  |
| mcp | monorepo_docker_emerging | https://github.com/appwrite/mcp | Present |  |  |
| 3dsmax-mcp | monorepo_docker_emerging | https://github.com/cl0nazepamm/3dsmax-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| alpha_vantage_mcp | monorepo_docker_emerging | https://github.com/alphavantage/alpha_vantage_mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| template-mcp-server | monorepo_docker_emerging | https://github.com/redhat-data-and-ai/template-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| datagouv-mcp | monorepo_docker_emerging | https://github.com/datagouv/datagouv-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| dify-mcp-server | monorepo_docker_emerging | https://github.com/YanxingLiu/dify-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| myfitnesspal-mcp-python | monorepo_docker_emerging | https://github.com/AdamWalt/myfitnesspal-mcp-python | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-nixos | monorepo_docker_emerging | https://github.com/utensils/mcp-nixos | Present |  |  |
| onshape-mcp | monorepo_docker_emerging | https://github.com/hedless/onshape-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| openproject-mcp-server | monorepo_docker_emerging | https://github.com/AndyEverything/openproject-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcpadapt | monorepo_docker_emerging | https://github.com/grll/mcpadapt | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| maverick-mcp | monorepo_docker_emerging | https://github.com/wshobson/maverick-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| ticktick-mcp | monorepo_docker_emerging | https://github.com/jacepark12/ticktick-mcp | Present |  |  |
| mcp-telegram | monorepo_docker_emerging | https://github.com/dryeab/mcp-telegram | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| aws-finops-mcp-server | monorepo_docker_emerging | https://github.com/ravikiranvm/aws-finops-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| junos-mcp-server | monorepo_docker_emerging | https://github.com/Juniper/junos-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| linkedin-mcp-server | monorepo_docker_emerging | https://github.com/eliasbiondo/linkedin-mcp-server | Present |  |  |
| isaac-sim-mcp | monorepo_docker_emerging | https://github.com/omni-mcp/isaac-sim-mcp | Present |  |  |
| okta-mcp-server | monorepo_docker_emerging | https://github.com/okta/okta-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mysql_mcp_server_pro | monorepo_docker_emerging | https://github.com/wenb1n-dev/mysql_mcp_server_pro | Present |  |  |
| private-gpt | monorepo_docker_emerging | https://github.com/zylon-ai/private-gpt | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| x-reader | monorepo_docker_emerging | https://github.com/runesleo/x-reader | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-tree-sitter | monorepo_docker_emerging | https://github.com/wrale/mcp-server-tree-sitter | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| penpot-mcp | monorepo_docker_emerging | https://github.com/montevive/penpot-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-discord | monorepo_docker_emerging | https://github.com/hanweg/mcp-discord | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| meta-ads-mcp | monorepo_docker_emerging | https://github.com/pipeboard-co/meta-ads-mcp | Present |  |  |
| code-index-mcp | monorepo_docker_emerging | https://github.com/johnhuang316/code-index-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp | monorepo_docker_emerging | https://github.com/jumpserver/mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| blender-ai-mcp-addon | monorepo_docker_emerging | https://github.com/LiCinCan/blender-ai-mcp-addon | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-reddit | monorepo_docker_emerging | https://github.com/Hawstein/mcp-server-reddit | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-box | monorepo_docker_emerging | https://github.com/box-community/mcp-server-box | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-apache-airflow | monorepo_docker_emerging | https://github.com/yangkyeongmo/mcp-server-apache-airflow | Present |  |  |
| cli-mcp-server | monorepo_docker_emerging | https://github.com/MladenSU/cli-mcp-server | Present |  |  |
| Sci-Hub-MCP-Server | monorepo_docker_emerging | https://github.com/JackKuo666/Sci-Hub-MCP-Server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| geo-mcp-servers | monorepo_docker_emerging | https://github.com/sparkgeo/geo-mcp-servers | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-redis | monorepo_docker_emerging | https://github.com/redis/mcp-redis | Present |  |  |
| teradata-mcp-server | monorepo_docker_emerging | https://github.com/Teradata/teradata-mcp-server | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| mcp-server-bigquery | monorepo_docker_emerging | https://github.com/LucasHild/mcp-server-bigquery | Present |  |  |
| scrapegraph-mcp | monorepo_docker_emerging | https://github.com/ScrapeGraphAI/scrapegraph-mcp | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| awesome-mcp-lists | monorepo_docker_emerging | https://github.com/collabnix/awesome-mcp-lists | Missing | UVX_STANDALONE_SCRIPT | Single-file script header parsing recipes. |
| imagesorcery-mcp | monorepo_docker_emerging | https://github.com/sunriseapps/imagesorcery-mcp | Present |  |  |

## 4. Architectural Remediation Roadmap


1. **Update `synchronizer.py`:**
   - Integrate custom logic to parse PEP 723 script blocks for inline dependencies.
   - Expand registry endpoints to include Go packages (`pkg.go.dev` custom scraping) and Crates.io with fallback to GitHub releases.

2. **Update `ast_parser.py`:**
   - Add a tree-sitter or regex-based macro evaluator for Rust code (e.g. `rmcp` macros).
   - Incorporate Java annotation scanning for JVM languages, extracting `@Tool` details from Spring AI.
   - Recognize Go custom builder patterns by tracking references to `mark3labs/mcp-go`.

3. **Crawler Modules:**
   - Extend GitHub search scopes to include `Dockerfile` labels referencing MCP and Monorepo custom path discovery.

4. **Curated Seed Lists:**
   - Seed crawler with standard "Awesome-MCP" repositories, international mirrors, and enterprise registries.
