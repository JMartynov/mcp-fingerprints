# Task Contract: Task 70 — Polyglot Static Code Extraction: PHP MCP Parser (`parse_php_mcp_code`)

## 1. Problem Statement
The PHP ecosystem has over 776+ active Model Context Protocol repositories on GitHub, including the official PHP Foundation SDK (`modelcontextprotocol/php-sdk`), Laravel integrations (`laravel/boost`, `laravel/mcp`, `php-mcp/laravel`), Symfony bundles (`php-llm/mcp-bundle`), and WordPress MCP servers. `src/mcp_fingerprints/ast_parser.py` lacks a native PHP code extractor.

To extract MCP passports statically from PHP source code without requiring a PHP interpreter, Composer, or vendor dependencies, **Task 70** implements `parse_php_mcp_code` and validates it against live patterns harvested from 200 real PHP MCP repositories (`data/samples/php_mcp_200.json`).

## 2. Technical Requirements & Deliverables

### A. PHP MCP Parser (`src/mcp_fingerprints/ast_parser.py`)
Implement `parse_php_mcp_code(code: str) -> list[dict[str, Any]]`:
1. **Tool Definition Patterns**:
   - PHP 8.2+ Attributes:
     - `#[McpTool(name: '...', description: '...')]` or `#[Tool('...')]`
     - Extract tool function parameters, types (`string`, `int`, `float`, `bool`, `array`), and default values (determines optionality).
   - Class-based Tool Implementations (Laravel/Symfony):
     - `class .*Tool extends Tool` or implements `McpToolInterface`
     - Extract `protected string $name = '...'` or `public function getName(): string`
     - Extract `protected string $description = '...'` or docblocks
     - Extract `public function schema(): array` properties
   - Method registration calls:
     - `$server->registerTool('name', ...)`
2. **Schema & Argument Extraction**:
   - Map PHP types to JSON Schema types (`string`, `int` -> `integer`, `float` -> `number`, `bool` -> `boolean`, `array` -> `array`/`object`).
   - Extract required parameters (parameters without default values).
   - Build valid `inputSchema`.
3. **Dispatcher Integration**:
   - Update `parse_mcp_source_code` in `ast_parser.py` to route `language="php"` and auto-detect PHP syntax (`<?php`, `namespace `, `public function `, `#[McpTool]`).

### B. Invariant & Recall Unit Tests (`tests/test_ast_php_mcp.py`)
1. Test PHP 8.2+ attribute definitions (`#[McpTool]`).
2. Test Laravel/Symfony class-based tool implementations (`class WeatherTool extends Tool`).
3. Test `$server->registerTool(...)` invocations.
4. Test real fixtures from `laravel/mcp` and `php-mcp/server`.
5. Ensure 100% test pass rate with zero regression across all existing suites.

## 3. Non-Interactive Execution Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement `parse_php_mcp_code` in `src/mcp_fingerprints/ast_parser.py`, wire it to `parse_mcp_source_code`, write comprehensive unit tests in `tests/test_ast_php_mcp.py`, run `pytest tests/test_ast_php_mcp.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
