# Task Contract: Task 61 — Deep Research and Audit of Zero-Tool Servers (Missing Tool Definitions, Unexpected Formats & Remedies)

## 1. Problem Statement & User Mandate
Over 2,900 servers in `web/catalog.json` advertise 0 callable tools (`tool_count: 0`), displaying the *"No static tools declared (Remote Endpoint / Gateway)"* badge.

While some servers are genuinely toolless (such as remote HTTP/SSE endpoints, pure prompt templates, resource-only repositories, or client SDK libraries), many servers actually implement MCP tools that our existing AST parsers missed due to **unexpected formats**, non-standard architectures, or alternative file configurations.

The user mandates a strict, exhaustive deep research audit:
1. **Each repository must be researched separately.**
2. **Re-inspect everything we probably missed** due to unexpected formats. Inspect all available files (code, manifests, YAML configs, OpenAPI schemas, README documentation tables) to identify missed tool definitions.
3. **Maintain a structured inventory** of all such servers in `data/zero_tools_audit_manifest.json`.
4. **Produce a comprehensive audit report** at `docs/reports/audit_zero_tools_deep_research.md` with an `[x]` checkbox against each checked server, documenting:
   - Whether tools were discovered in the repository (`TOOLS_FOUND_MISSED_BY_PARSER`).
   - The file path and line number where tools are defined.
   - The unexpected format / pattern encountered.
   - The concrete remedy required (AST pattern, schema parser, doc table reader).
   - Or, confirm genuine zero-tool status (`CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY`, `CLIENT_SDK`, `RESOURCE_ONLY`, `PROMPT_ONLY`, `DEAD_REPO`).
5. **Formulate concrete remedies** to enable an automated implementation task (Task 62).

---

## 2. Technical Scope & Architecture

### A. Deep Zero-Tool Inspection Engine (`src/mcp_fingerprints/deep_zero_tool_auditor.py`)
Build an automated, resilient deep inspector capable of inspecting source files, repository trees, and tarballs to identify tool definitions across all unexpected formats:

1. **Dynamic Registration & Iteration Patterns**:
   - `for tool in tools: server.add_tool(tool)`
   - `TOOLS.forEach(t => server.tool(t.name, ...))`
   - Dictionary dispatchers: `HANDLERS = { "tool_a": ..., "tool_b": ... }`
   - Array literals mapped to `ListToolsResult`.

2. **Configuration & Schema Manifests**:
   - Static tool declarations in JSON / YAML / TOML files:
     - `tools.json`, `mcp.json`, `mcp-config.json`, `mcp.yaml`, `manifest.json`.
   - OpenAPI / Swagger definitions (`openapi.json`, `openapi.yaml`) used with dynamic tool adapters (`fastmcp.from_openapi(...)`, `swagger-mcp`).

3. **Multi-File Trees & Deep Subdirectories**:
   - Handlers residing in `src/handlers/`, `src/tools/`, `lib/tools/`, `pkg/plugins/`, `tools/` that were missed if previous AST traversals only inspected entrypoint files.
   - Re-exported tool definitions across TypeScript / JavaScript ES modules (`export * from './tools'`).

4. **Class-Based & Custom Decorator Formats**:
   - Class methods decorated with `@tool`, `@action`, `@mcp_tool`, `@command`.
   - Python Pydantic / dataclass action registries.
   - Go struct methods implementing tool interfaces.

5. **Markdown Documentation Tables**:
   - When source code is compiled, bundled, or closed-source, parse markdown tables in `README.md` or `docs/tools.md` matching tool signatures (`| Tool | Description | Arguments |`).

6. **Genuine Zero-Tool Classification**:
   - Clearly identify and tag:
     - `REMOTE_HTTP_GATEWAY`: Pure URL endpoints without static repo schemas.
     - `CLIENT_SDK_LIBRARY`: AI routers, gateways, or client drivers (e.g. `@juspay/neurolink`).
     - `RESOURCE_OR_PROMPT_ONLY`: Servers providing resources or prompt templates only.
     - `DEAD_OR_PRIVATE`: Unreachable (404/auth required) repositories.

---

### B. Execution & Reporting

1. **Inventory File (`data/zero_tools_audit_manifest.json`)**:
   - Contains all zero-tool servers with metadata (`name`, `ecosystem`, `repository_url`, `version`, `checked`, `status`, `tools_found_count`, `tools_found`, `unexpected_format`, `remedy`).
   - Updated with inspection results.

2. **Master Audit Report (`docs/reports/audit_zero_tools_deep_research.md`)**:
   - Executive Summary with breakdown counts.
   - Comprehensive `[x]` checklist for all checked servers:
     - Format:
       ```markdown
       - [x] **`@scope/pkg-name`** (`ecosystem`) — `https://github.com/...`
         - **Status**: `TOOLS_FOUND_MISSED_BY_PARSER` | `CONFIRMED_ZERO_TOOLS`
         - **Tools Found**: `tool_a`, `tool_b`, ... (N tools)
         - **Location**: `src/tools/definitions.ts:42`
         - **Unexpected Format**: Dynamic array mapped into `ListToolsRequestSchema`
         - **Remedy**: Extend TS AST parser to evaluate identifier references in `tools` array.
       ```
   - Categorized summary of unexpected formats discovered.
   - Concrete Actionable Remedies & Roadmap for Task 62.

3. **Automated Unit Tests (`tests/test_deep_zero_tool_auditor.py`)**:
   - Test fixture verification covering each unexpected format (dynamic arrays, JSON manifests, OpenAPI specs, nested subdirectories, README tables).
   - Ensure all tests pass (`pytest -q tests/test_deep_zero_tool_auditor.py`).

---

## 3. Non-Interactive Completion Directive
This task is dispatched to Google Jules (EULIS) for non-interactive execution.
Implement the deep inspection engine, verify unexpected formats with unit test fixtures, execute the audit across zero-tool servers, author `docs/reports/audit_zero_tools_deep_research.md` with `[x]` checklist against each server, update `data/zero_tools_audit_manifest.json`, and commit all artifacts. Conclude directly with complete patch.
