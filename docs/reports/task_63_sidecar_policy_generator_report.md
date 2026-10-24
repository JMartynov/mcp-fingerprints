# Technical Report: Sidecar Policy Generator (`mcp-fingerprints export-policy`)

## Executive Summary
This report details the successful implementation of the Sidecar Policy Generator functionality within the `mcp-fingerprints` repository. This feature bridges the gap between offline static AST analysis and inline runtime safety enforcement by automatically generating enforcement contracts (OPA Rego v1, Envoy HTTP/JSON-RPC configurations, and Canonical JSON Manifests) derived directly from canonical structural fingerprints.

## Architectural Overview
The solution introduces a pure translation layer that maps structurally sound `ServerPackageSpec` objects into executable policy dialects, operating independently of inline network traffic.

### Core Components
1. **Policy Exporter Engine** (`src/mcp_fingerprints/policy_exporter.py`):
    - `PolicyFormat` & `PolicyMode`: Enums governing output dialect and constraint strictness (`strict`, `read-only`, `allowlist`).
    - `RegoPolicyCompiler`: Generates OPA Rego v1 syntax evaluating `input.method == "tools/call"`. It validates parameters against JSON Schema specifications extracted during AST parsing.
    - `EnvoyWasmConfigCompiler`: Emits Envoy HTTP filter configurations (`envoy.filters.http.rbac`) for high-performance sidecar proxy routing based on allowed tool namespaces.
    - `PolicyExporter`: Provides orchestrator capabilities for dynamic resolution of passports against internal indices or static JSON files.

2. **CLI Integration** (`src/mcp_fingerprints/cli.py`):
    - Implementation of the `export-policy` subcommand providing flexible argument structures for formatting (`--format`), enforcement modes (`--mode`), and I/O redirection (`--output`).

## Design Decisions and Findings

### High Findings
*   **Zero Latency Paradigm Preserved**: By generating standalone OPA Rego and Envoy sidecar configurations, the repository successfully maintains its architectural constraint of providing structurally isolated, zero-latency validation independent of the physical execution topology.
*   **Dynamic Constraint Generation**: `strict` mode logic successfully injects regex-equivalent path constraint logic (blocking `..`, `/etc/`, etc.) derived from standard shell traversal signatures, leveraging parameter types directly captured during static inspection.

### Medium Findings
*   **Annotation Safety Context Mapping**: The `read-only` modes successfully map the protocol’s semantic annotation contexts (`readOnlyHint` and `destructiveHint`) directly into boolean logic filters within Rego rules, ensuring explicit denial of non-conforming operations without deeper payload introspection.
*   **Neutral Contract Terminology**: In adherence to domain isolation mandates, all metadata objects output in JSON formats successfully utilize neutral structural terminology (`safety_classification`, `annotation_summary`, `mode_constraints`) rather than subjective vulnerability assessments.

### Low Findings
*   **Rego Primitive Type Matching**: Standardizing dynamic JSON Schema types into OPA primitive assertion functions (`is_string`, `is_number`) required mapping routines. These were integrated directly into the `strict` iteration block inside `RegoPolicyCompiler`.

## Conclusion
The `export-policy` enhancement robustly addresses the runtime deployment footprint problem by providing operators automated, zero-touch integrations with external proxy fabrics natively bound to the static fingerprint database.
