# Task Contract: Task 71 — Polyglot Static Code Extraction: Kotlin MCP Parser (`parse_kotlin_mcp_code`)

## 1. Problem Statement
The Kotlin ecosystem features over 470+ active Model Context Protocol repositories on GitHub, including official JetBrains integrations (`JetBrains/mcp-server-plugin`), Ktor server DSLs, desktop agents (`CrossPaste/crosspaste-desktop`), and enterprise tools (`PortSwigger/mcp-server`). While `ast_parser.py` includes a basic Java JVM parser, it does not support idiomatic Kotlin constructs (data classes, default parameters, nullable types, Ktor DSLs, and `@Tool` annotations).

To extract MCP passports statically from Kotlin source code without requiring Gradle, JDK, or JVM execution, **Task 71** implements `parse_kotlin_mcp_code` and validates it against live patterns harvested from 200 real Kotlin MCP repositories (`data/samples/kotlin_mcp_200.json`).

## 2. Technical Requirements & Deliverables

### A. Kotlin MCP Parser (`src/mcp_fingerprints/ast_parser.py`)
Implement `parse_kotlin_mcp_code(code: str) -> list[dict[str, Any]]`:
1. **Tool Definition Patterns**:
   - Annotation-based:
     - `@Tool(name = "...", description = "...")` or `@Tool("...")`
     - Extract function signature: `fun name(param: Type = default): ReturnType`
   - Ktor / DSL-based:
     - `mcpServer { tool("name") { description = "..."; parameter(...) } }`
   - Class-based / Interface implementations:
     - `class .*Tool : McpTool` or `class .*Tool(override val name: String = "...")`
2. **Schema & Argument Extraction**:
   - Map Kotlin types (`String`, `Int`, `Long`, `Double`, `Boolean`, `List<T>`, `Map<K, V>`) to JSON Schema types (`string`, `integer`, `number`, `boolean`, `array`, `object`).
   - Extract nullable types (`String?` -> optional, `String` -> required unless default value provided).
   - Build standard `inputSchema`.
3. **Dispatcher Integration**:
   - Update `parse_mcp_source_code` in `ast_parser.py` to route `language="kotlin"` and auto-detect Kotlin syntax (`package `, `fun `, `val `, `var `, `data class `, `@Tool`).

### B. Invariant & Recall Unit Tests (`tests/test_ast_kotlin_mcp.py`)
1. Test `@Tool` annotation on functions with Kotlin parameter types and default arguments.
2. Test Ktor server DSL tool blocks.
3. Test class-based tool implementations inheriting `McpTool`.
4. Test real fixtures from `PortSwigger/mcp-server` and `JetBrains/mcp-server-plugin`.
5. Ensure 100% test pass rate with zero regression across all existing suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement `parse_kotlin_mcp_code` in `src/mcp_fingerprints/ast_parser.py`, wire it to `parse_mcp_source_code`, write comprehensive unit tests in `tests/test_ast_kotlin_mcp.py`, run `pytest tests/test_ast_kotlin_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
