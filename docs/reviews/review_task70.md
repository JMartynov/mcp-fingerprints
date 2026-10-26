# EULIS Code Review & Gap Analysis: Task 70 (PHP MCP AST Parser)

## 1. Executive Summary & Verification Findings

The introduction of the `parse_php_mcp_code` parser in `src/mcp_fingerprints/ast_parser.py` provides a foundational static analysis engine for extracting Model Context Protocol (MCP) tool definitions from PHP codebases. By evaluating the AST parser against a dataset of 200 real-world PHP MCP repositories (located in `data/samples/php_mcp_200.json`), we validated the current capabilities of the parser and identified critical gaps in framework-specific patterns, advanced type hinting, and architectural approaches common in the PHP ecosystem.

While the current implementation successfully extracts foundational tool patterns, its lack of support for Symfony/Laravel specific metadata, docblock parameter type inference, and modern PHP type declarations limits its accuracy in production-grade repositories.

## 2. Caught Capabilities vs Missed Tool Definitions in the 200 Real PHP Repos

### Caught Patterns (Current Capabilities)
The existing implementation successfully captures:
1. **Attributes:** Standard `#[McpTool]` and `#[Tool]` attributes on methods and functions, including the extraction of name, description, and basic parameter schemas.
2. **Class-based Tools:** Classes that inherit from standard MCP base classes (e.g., `extends Tool`, `implements McpToolInterface`), extracting `$name` and `$description` properties or `getName()` methods.
3. **Manual Registration:** Procedural registrations using `$server->registerTool('name', ...)` and `$mcp->registerTool('name', ...)`.

### Missed Patterns (Gap Analysis)
Based on an analysis of the 200 real-world PHP MCP repositories (including `laravel/boost`, `php-mcp/server`, `EdouardCourty/mcp-server-bundle`), the parser currently misses several critical patterns:

1. **Symfony/Framework Attributes:** Fails to recognize framework-specific attributes such as `#[AsTool]`, `#[AsMcpTool]`, and `#[AutoconfigureTag]`.
2. **Single-Action Invokable Classes:** Misses tool classes implementing the magic `__invoke(...)` method, often documented with class-level or method-level docblocks.
3. **Docblock Parameter Type Inference:** Fails to extract types and descriptions from docblock annotations (e.g., `/** @param string $query Description */`) when native PHP types are omitted or when additional metadata is provided in comments.
4. **Complex Type Declarations:** Poor handling of union types (e.g., `string|int`, `?string`), intersection types, and complex array element types (e.g., `array<string, mixed>`, `ToolInput[]`).
5. **Request/DTO Schemas:** Fails to resolve parameter schemas defined via Laravel `FormRequest` classes or custom Data Transfer Objects (DTOs) used as tool arguments.

## 3. Actionable List of Proposed Fixes

### High Priority
* **Enhance Attribute Support:** Expand the regex attribute matcher to include `#[AsTool]`, `#[AsMcpTool]`, and `#[AutoconfigureTag]`.
* **Docblock Parser Integration:** Implement docblock parsing to extract `@param` descriptions and types, merging them with native type declarations.
* **Support Single-Action Classes:** Add matching logic for classes using the `__invoke()` method as the primary execution path for tools.

### Medium Priority
* **Complex Type Parsing:** Improve parameter parsing to correctly identify and map PHP union types (`string|int`), intersection types, and array shape definitions (`array<string, mixed>`) to valid JSON schema equivalents.
* **Docblock Fallbacks:** Ensure that if native parameter types are missing, the parser falls back to types defined in docblocks.

### Low Priority
* **DTO/FormRequest Resolution:** Add basic heuristic resolution to identify when a parameter uses a custom request object/DTO and attempt to parse public properties or validation rules from that class to construct the `inputSchema`.

## 4. Proposed Unit Test Fixtures

The following fixtures should be added to `tests/test_ast_php_mcp.py` to cover the missed patterns:

### Fixture 1: Symfony Attributes
```php
<?php
class SymfonyTools {
    #[AsTool(name: 'cache_clear', description: 'Clears the cache')]
    public function clearCache(string $env = 'dev') {}

    #[AsMcpTool('log_analyzer')]
    public function analyzeLogs() {}
}
```

### Fixture 2: Single-Action Invokable Classes
```php
<?php
/**
 * Search the database
 */
class SearchTool implements ToolInterface {
    public function __invoke(string $query, int $limit = 10) {}
}
```

### Fixture 3: Docblock Parameter Inference and Union Types
```php
<?php
class UserTools {
    #[McpTool('get_user')]
    /**
     * @param string|int $identifier The user ID or email
     * @param string[] $relations Related models to load
     */
    public function getUser($identifier, array $relations = []) {}
}
```

### Fixture 4: DTO / FormRequest Schema
```php
<?php
class CreateUserRequest {
    public string $name;
    public string $email;
}

class UserCreationTool {
    #[McpTool('create_user', 'Creates a new user')]
    public function handle(CreateUserRequest $request) {}
}
```
