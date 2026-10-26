# Task Contract: Task 83 — Official Go SDK Composite Literals, Constant Names & Unresolved Toolset Distinction

## 1. Problem Statement & Motivation
In issue feedback regarding the listed `kimjooyoon/gooo-go-ports` server, a concrete gap in the Golang MCP AST parser was identified:
- `parse_golang_mcp_code` in `src/mcp_fingerprints/ast_parser.py` only extracts tools defined with builder methods `mcp.NewTool(...)` or `mcp.NewToolWithRawSchema(...)`.
- The official Go SDK (`github.com/modelcontextprotocol/go-sdk/mcp`) frequently registers tools via composite struct literals passed to `Server.AddTool(&mcp.Tool{ ... }, handler)`.
- Furthermore, `Name` is often passed as a declared constant (e.g. `const toolName = "assess_service_grant"` or inside block `const (...)`) rather than an inline string literal.
- Currently, servers using this pattern yield 0 extracted tools, resulting in `capabilities.tools: false` in passports (such as `data/fingerprints/kimjooyoon_gooo-go-ports.json`).
- Additionally, there is no semantic distinction in passports and audit reports between a **confirmed empty toolset** (gateways, pure resource/prompt servers) and an **unresolved extraction** (server code calls tool registration APIs or imports MCP tool packages, but static AST analysis failed to resolve the schema/names).

---

## 2. Technical Scope & Implementation Plan

### A. Golang AST Parser Enhancements (`src/mcp_fingerprints/ast_parser.py`)
1. **Constant Definition Table**:
   - Parse Go constants (`const name = "val"` and multi-line `const ( ... )`).
   - Map constant identifiers to their string values in the file scope.

2. **Official Go SDK Composite Literal Pattern Support**:
   - Match `server.AddTool(&mcp.Tool{ ... }, ...)` and `mcp.Tool{ ... }` struct literals.
   - Extract:
     - `Name`: String literal or resolved constant name.
     - `Description`: String literal or resolved constant description.
     - `Title`: If present and description is empty/short, use title or fallback to name.
     - `InputSchema`: Detect schema generator calls or inline maps, returning standard JSONSchema object with basic properties or closed object.

3. **Retain Existing Builder Support**:
   - Ensure `mcp.NewTool(...)` and `mcp.NewToolWithRawSchema(...)` continue to function without regressions.

---

### B. Unresolved Extraction vs Confirmed Zero-Tool Distinction
1. In `src/mcp_fingerprints/deep_zero_tool_auditor.py` and passport generation:
   - Introduce an `extraction_status` indicator:
     - `CONFIRMED_ZERO_TOOLS`: Verified toolless (pure client SDK, gateway, prompt/resource only).
     - `UNRESOLVED_EXTRACTION`: Repository exhibits explicit tool indicators (calls `AddTool`, imports tool registries, defines tool schemas), but tool name or schema could not be statically resolved.

---

### C. Live Acceptance & Passport Update
1. Update `data/fingerprints/kimjooyoon_gooo-go-ports.json`:
   - Re-parse with enhanced Go parser to recover `assess_service_grant` (and `assess_service_grant_change` if enabled).
   - Set `capabilities.tools: true` and populate `tool_signatures`.
2. Update web catalog representations (`web/catalog.json`) if regenerated.

---

### D. Unit Tests (`tests/test_ast_golang_official_sdk.py`)
Add unit tests verifying:
1. `server.AddTool(&mcp.Tool{Name: "example", Description: "control"}, handler)` extracts 1 tool.
2. Constant name resolution: `const toolName = "assess_service_grant"` used in `Name: toolName`.
3. Block constants: `const ( toolName = "foo"; other = "bar" )`.
4. Reproduction test with the exact snippet from `kimjooyoon/gooo-go-ports` `examples/service-grant-mcp/main.go`.
5. Compatibility test ensuring existing `mcp.NewTool` tests continue passing.

---

## 3. Strict Safety & Publication Gates
- **Domain Constraint**: Pure metadata, AST parsing, and passport cataloging. Zero security or offensive features.
- **Report-Only Publishing Invariant**: Clean up any temporary scratch files created during testing.
- **Verification**: Run `pytest tests/test_ast_golang_official_sdk.py` and full suite `pytest -q tests/`.
