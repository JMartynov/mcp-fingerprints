# Pillar 3 Audit: Core Toolset Architecture, Runtime Engines & Failure Modes Audit

## Executive Summary
This audit evaluates the resilience, pattern support, and boundary failure modes of the core `mcp-fingerprints` architecture (Pillar 3 of the 360-Degree System Audit). The scope includes AST Parsers, Prober & Transports, Canonicalizer & Matcher, and Scanners & Exporters. 

---

## 1. AST Parsers (`ast_parser.py`, `go_sdk_parser.py`, `openapi_parser.py`, `manifest_parser.py`)

### Supported Patterns
- **Python (`ast_parser.py`)**: `FastMcpAstVisitor` robustly handles `@mcp.tool`, `@action`, `@command`, and `Tool(...)` instantiations. Converts type annotations effectively.
- **TypeScript**: Regex-based balanced brace extraction correctly identifies Zod schemas and `server.setRequestHandler` patterns.
- **Go (`go_sdk_parser.py` & `ast_parser.py`)**: Support for `mark3labs/mcp-go`, composite literals (`mcp.Tool{...}`), and nested `mcp.Required()`.
- **OpenAPI (`openapi_parser.py`)**: Converts OpenAPI 3.x and Swagger 2.0 schemas to MCP tools.
- **Manifests (`manifest_parser.py`)**: Supports both root array and nested `tools` / `tool_definitions` object schemas.

### Unhandled Syntax Constructs & Failure Modes
- **Python**: Deeply nested dynamic class creations or decorators dynamically applied in local scopes (e.g., inside loops) may evade `visit_ClassDef` and `visit_FunctionDef`. `_python_type_to_schema_type` lacks comprehensive handling for recursive type aliases.
- **TypeScript/JavaScript**: Regex-based Zod extraction `_parse_balanced_zod_schema` fails if template literals contain mismatched braces within strings or if AST structure deviates from expected functional declarations (e.g., dynamically built Zod objects spread over multiple variables).
- **Go**: Constant resolution does not fully trace cross-package references. If a tool name or description relies on a const from another imported module, it resolves as unresolved.
- **OpenAPI / Manifests**: Infinite recursion loops possible if OpenAPI schemas contain cyclic `$ref` pointers without depth limits.

### Recommended Update Tasks
- [ ] Implement depth-limited `$ref` resolution in `openapi_parser.py` to prevent recursion bombs.
- [ ] Migrate TypeScript extraction from regex brace matching to a formal AST parser (e.g., via a node-based bridge or tree-sitter) for robust Zod schema extraction.
- [ ] Add cross-module constant resolution capabilities to `go_sdk_parser.py`.

---

## 2. Prober & Transports (`prober.py`, `monorepo_prober.py`, `runtime_sandbox.py`)

### Capabilities & Boundary Checks
- **Transports**: Handles StdIO and HTTP/SSE protocols.
- **Sandboxing (`runtime_sandbox.py`)**: Environment sanitization correctly strips `AWS_`, `GITHUB_TOKEN`, `OPENAI_API_KEY` to prevent credential leakage in child processes.
- **Timeouts**: Applies time budgets to subprocess executions.

### Error Handling & Resilience Bottlenecks
- **Stdio Boundary Checks**: `prober.py` and `runtime_sandbox.py` can hang if child processes ignore `SIGTERM` or block indefinitely on stderr. Lack of strict buffer limits on `stdout`/`stderr` reading can lead to OOM (Out-of-Memory) if a rogue server spews unbounded logs.
- **SSE Transport**: Potential connection leaks if the SSE stream doesn't properly cleanly close on malformed JSON-RPC payloads or underlying socket drops.
- **Malformed Responses**: The parser assumes well-formed JSON-RPC envelopes. If a server interleaves plaintext logs with JSON on stdout (a common bug in custom MCP servers), the JSON parser crashes with `JSONDecodeError` rather than attempting a fuzzy extraction line-by-line.

### Recommended Update Tasks
- [ ] Enforce strict byte-size limits on stdout/stderr buffers in `runtime_sandbox.py`.
- [ ] Add a fuzzy JSON-RPC extractor in `prober.py` that can ignore non-JSON prefix/suffix logs on stdout.
- [ ] Implement `SIGKILL` escalation for child processes that fail to exit within the grace period.

---

## 3. Canonicalizer & Matcher (`canonicalizer.py`, `matcher.py`, `distance.py`)

### Architecture & Stability
- **Canonicalizer (`canonicalizer.py`)**: Enforces deterministic JSON serialization via sorted keys and compact separators. Crucial for stable `SHA-256` hashing.
- **Matcher (`matcher.py` & `distance.py`)**: Tri-Layer architecture (O(1) hash, Jaccard distance, Composite capability matching).

### Hash Collision Resistance & Validation
- **Hash Invariants**: SHA-256 is highly collision-resistant, but `canonicalize_json` can produce identical hashes for structurally equivalent but semantically different schemas if default values or optional fields are normalized aggressively.
- **Jaccard Stability**: The Jaccard distance calculation in `distance.py` relies on tokenized sets. If a schema contains highly generic terms (e.g., `id`, `name`), the Jaccard distance may incorrectly threshold above 0.65 for unrelated tools.
- **Schema Validation**: Missing strict type boundary checks before hashing can lead to Python-specific data types leaking into canonical forms (e.g., tuple vs list).

### Recommended Update Tasks
- [ ] Enhance tokenization in `distance.py` to weight structural keys higher than generic parameter names to prevent false positive Jaccard matches.
- [ ] Ensure `canonicalize_json` strictly rejects or coerces non-JSON-compliant types before serialization to prevent cross-language hashing drift.

---

## 4. Scanners & Exporters (`config_scanner.py`, `drift_detector.py`, `config_exporter.py`, `sbom_exporter.py`)

### Formatting & Standards Compliance
- **Scanner**: Discovers configurations across multiple IDE clients (Zed, Cline, Windsurf).
- **Drift Detector (`drift_detector.py`)**: Classifies silent tool additions as HIGH and hash mutations as CRITICAL.
- **SBOM Exporter (`sbom_exporter.py`)**: Exports CycloneDX 1.6 and SPDX 2.3 formats out-of-band.

### Configuration Alerts & Drift Scenarios
- **Drift Alerts**: The `drift_detector.py` correctly exempts the empty SHA-256 hash. However, it lacks a mechanism to distinguish between backwards-compatible schema additions (e.g., adding an optional parameter) and breaking changes (e.g., changing a required parameter type), flagging both as CRITICAL hash mutations.
- **Config Exporter (`config_exporter.py`)**: Uses regex-based string injection for JSONC. Complex nested structures or multi-line comments surrounding injection points may break the regex, resulting in corrupted IDE configs.
- **SBOM Compliance**: `sbom_exporter.py` generates valid formats, but relies on accurate purl components. If a repository has an unconventional ecosystem, the purl generation might fail strict SPDX validation.

### Recommended Update Tasks
- [ ] Refine `drift_detector.py` to perform semantic schema diffing to classify backwards-compatible changes as MEDIUM severity rather than CRITICAL.
- [ ] Replace regex JSONC patching in `config_exporter.py` with a robust JSONC AST parser (e.g., `ruamel.yaml` or a dedicated jsonc library) to guarantee config integrity.
- [ ] Add purl ecosystem validation before generating SBOM artifacts to ensure strict SPDX compliance.

---

## Conclusion
The Pillar 3 audit reveals a generally robust core architecture. However, resilience hardening is required for standard I/O buffer management, semantic schema diffing for drift detection, and avoiding regex-based manipulation for TS ASTs and JSONC configs. Addressing these bottlenecks will ensure enterprise-grade stability and zero-trust execution safety.
