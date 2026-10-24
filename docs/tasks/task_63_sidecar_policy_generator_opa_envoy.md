# Task Contract: Task 63 — Sidecar Policy Generator (`mcp-fingerprints export-policy`)

## 1. Problem Statement
In the Task 6 ecosystem benchmark ([`docs/reports/task6_runtime_proxies_policy_engines_report.md`](../reports/task6_runtime_proxies_policy_engines_report.md) and [`docs/reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md`](../reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md)), we identified a critical boundary between `mcp-fingerprints` (which excels at offline-first static AST discovery and SHA-256 structural fingerprinting with **zero runtime latency**) and inline runtime proxies (Invariant Labs, Lakera Guard, Cisco AI Agent Gateway, Cloudflare AI Gateway).

Embedding an inline reverse proxy directly into `mcp-fingerprints` would violate its zero-latency, offline-first architecture. However, `mcp-fingerprints` already possesses the exact canonical tool schemas (`ToolContractSignature`), parameter constraints, and MCP protocol safety annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) required by external policy enforcement engines.

**Task 63** bridges this runtime enforcement gap with **zero inline latency overhead** by building the **Sidecar Policy Generator (`mcp-fingerprints export-policy`)**, which compiles canonical MCP passports directly into production-ready **Open Policy Agent (OPA) Rego v1 policies** and **Envoy HTTP/JSON-RPC filter configurations**.

---

## 2. Technical Requirements & Deliverables

### A. Policy Exporter Engine (`src/mcp_fingerprints/policy_exporter.py`)
Create `src/mcp_fingerprints/policy_exporter.py` containing the following classes and data structures:

1. **`PolicyFormat` (`str, Enum`)**:
   - `"rego"` — Open Policy Agent (OPA) Rego v1 policy syntax.
   - `"envoy"` — Envoy HTTP/JSON-RPC filter / RBAC configuration JSON/YAML structure.
   - `"json"` — Canonical JSON policy manifest summarizing allowed tools, parameter constraints, and risk classifications.

2. **`PolicyMode` (`str, Enum`)**:
   - `"strict"` — Enforces tool allowlist, required parameter presence, JSON Schema parameter types, blocks destructive tools unless `input.client_role == "admin"`, and blocks path-traversal (`..`, `/etc/`, `/proc/`) or shell-injection meta-characters (`;`, `$(`, `` ` ``) on high-risk parameters (`path`, `filepath`, `cmd`, `command`, `query`, `sql`, `url`).
   - `"read-only"` — Strictly permits only tools where `annotations.readOnlyHint is True` or (when annotations are absent) whose tool name matches read-only prefixes (`get_`, `list_`, `read_`, `search_`, `describe_`, `fetch_`, `query_`) and has `destructiveHint is not True`. All state-mutating or destructive tools are denied unconditionally.
   - `"allowlist"` — Permits any tool name present in the passport's canonical toolset (`tools` / `tool_signatures`) and denies any unlisted tool (`tool_added` runtime drift protection).

3. **`RegoPolicyCompiler`**:
   - Compiles a `ServerPackageSpec` or `VersionPassport` into a valid OPA Rego v1 policy string (`package mcp.authz` with `import rego.v1`).
   - Includes metadata header comments (`# Package: <name>`, `# Canonical Hash: <hash>`, `# Mode: <mode>`).
   - Emits `default allow := false`.
   - Generates `allow if { ... }` rules for each permitted tool in the passport based on the selected `PolicyMode`:
     - Checks `input.method == "tools/call"` and `input.params.name == "<tool_name>"`.
     - Validates required parameters from `inputSchema.get("required", [])` (`object.get(input.params.arguments, "<req_param>", null) != null`).
     - Validates parameter primitive types from `inputSchema.get("properties", {})` (`is_string`, `is_number`, `is_boolean`, `is_array`, `is_object`).
     - Applies safety hint guards (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) and path/command sanitization guards in `strict` mode.

4. **`EnvoyWasmConfigCompiler`**:
   - Compiles a `ServerPackageSpec` or `VersionPassport` into a structured Envoy HTTP filter configuration dictionary (`envoy.filters.http.rbac` + JSON-RPC payload matching rules) that restricts JSON-RPC `tools/call` invocations to the allowed toolset and enforces mode constraints.

5. **`PolicyExporter`**:
   - High-level orchestrator with `export(passport_or_identifier: str | Path | ServerPackageSpec, fmt: PolicyFormat = PolicyFormat.REGO, mode: PolicyMode = PolicyMode.STRICT, output_path: Optional[Path] = None) -> str`.
   - Resolves `<name_or_path>` either from an explicit JSON file path on disk, from `data/fingerprints/<slug>.json`, or from the catalog/snapshot index.

### B. CLI Subcommand (`src/mcp_fingerprints/cli.py`)
Register the `export-policy` subcommand in `src/mcp_fingerprints/cli.py`:
```bash
mcp-fingerprints export-policy \
  --passport <name_or_path> \
  --format [rego|envoy|json] \
  --mode [strict|read-only|allowlist] \
  [--output <file>]
```
- If `--output <file>` is provided, write the compiled policy to disk and print a confirmation message.
- If `--output` is omitted, print the compiled policy directly to `stdout`.
- Return exit code `0` on success and non-zero (`1` or `2`) if the passport cannot be found or arguments are invalid.

### C. Comprehensive Unit Tests (`tests/test_policy_exporter.py`)
Create `tests/test_policy_exporter.py` covering:
1. **Rego v1 Compilation (`strict`, `read-only`, `allowlist`)**:
   - Verify generated Rego syntax includes `package mcp.authz`, `import rego.v1`, `default allow := false`, and per-tool rules.
   - Verify `read-only` mode excludes tools marked with `destructiveHint=True` or mutating names (`delete_file`, `execute_command`) while permitting `readOnlyHint=True` (`read_file`, `list_directory`).
   - Verify `strict` mode emits required parameter checks, type checks, and path-traversal guards (`not contains(..., "..")`) for path/command parameters.
2. **Envoy Filter Config Compilation**:
   - Verify `EnvoyWasmConfigCompiler` produces valid JSON/dict structures containing `envoy.filters.http.rbac` permissions for permitted tools and blocks unauthorized tools.
3. **CLI Integration**:
   - Verify `mcp-fingerprints export-policy --passport <fixture_path> --format rego --mode strict` outputs valid Rego to stdout and `--output` writes to a file cleanly.
4. **Domain Isolation Preservation**:
   - Verify `ServerPackageSpec` and `VersionPassport` models remain completely unmodified by policy compilation.

---

## 3. Non-Interactive Completion Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement all specified modules, CLI wiring, and unit tests autonomously. Run `pytest tests/test_policy_exporter.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
