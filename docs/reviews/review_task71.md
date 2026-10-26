# EULIS Code Review & Gap Analysis: Task 71 (Kotlin MCP AST Parser)

## 1. Executive Summary & Verification Findings
Task 71 introduced the `parse_kotlin_mcp_code` function in `src/mcp_fingerprints/ast_parser.py` to statically extract tool definitions from Kotlin source code. 
An initial review of the implementation reveals a solid foundational parser that utilizes regex-based extraction. It supports standard `@Tool`/`@McpFunction` annotations, basic Ktor DSL `mcpServer { tool("name") { ... } }`, and class-based inheritances like `class XTool : McpTool`. 

However, Kotlin's expressive syntax and rich ecosystem (e.g., Spring Boot, Ktor) mean that real-world MCP servers use a wider variety of patterns. By evaluating the AST parser against a sample of 200 real Kotlin MCP repositories (e.g., `PortSwigger/mcp-server`, `JetBrains/mcp-server-plugin`, `vctrl/ktor-server-mcp`, etc.), several critical gaps were identified, especially around enterprise frameworks (Spring AI) and advanced Kotlin language features (Suspend functions, Data classes, Parameter annotations).

## 2. Caught Capabilities vs Missed Tool Definitions

### 2.1. Patterns Currently Caught (Capabilities)
The parser successfully handles the following patterns:
*   **Basic Annotation-based Tools**: Functions annotated with `@Tool` or `@McpFunction`, extracting the tool name from the function name or `name` attribute, and description from the `description` attribute.
*   **Primitive Parameter Parsing**: Basic parsing of primitive types (`Int`, `String`, `Boolean`) and lists (`List<...>`, `Array<...>`), successfully translating them to JSON Schema types (`integer`, `string`, `boolean`, `array`).
*   **Ktor/DSL-based Registration (Basic)**: Simple occurrences of `tool("name") { description = "..." }` within `mcpServer` blocks.
*   **Class-based Tool Implementations**: Classes extending `McpTool` (e.g., `class MyTool : McpTool`) where `name` and `description` are defined as overridden properties.
*   **Basic Nullable and Default Types**: It identifies `?` for nullable types and basic default arguments (e.g., `= null`), modifying the `required` JSON Schema array accordingly.

### 2.2. Patterns Missed (Gap Analysis from Real Repositories)
Based on the dataset of 200 real Kotlin MCP repositories, the following prominent patterns are currently missed or incorrectly parsed:

1.  **Spring AI `@Tool` Annotations on Beans**:
    *   Many enterprise Kotlin apps use Spring AI. The parser looks for standalone functions or doesn't account for complex `@Service`/`@Component` wrapping.
2.  **`@Description` Annotations on Parameters**:
    *   Kotlin code often uses `@Description("...")` on function parameters to document arguments for the LLM. The current regex strips these or fails to parse the parameter entirely if the annotation precedes the parameter name.
3.  **Suspend Functions**:
    *   Kotlin heavily relies on coroutines. While `suspend` is somewhat present in the regex `(?:suspend)?`, complex whitespace, generic bounds, or annotations before `suspend fun` often break the match.
4.  **Ktor Route Handlers & WebSocket/SSE Dispatchers**:
    *   Real servers (like `vctrl/ktor-server-mcp`) might map tools directly via custom Ktor routes (e.g., `post("/tools/{name}")` with internal logic) or WebSocket handlers, which are missed by the simple `tool("name")` DSL regex.
5.  **Data Class Parameter Models (Composite Objects)**:
    *   Instead of flat parameters (e.g., `fun(a: Int, b: String)`), robust Kotlin apps use Data Classes: `fun myTool(input: ToolInput)`. The parser maps `ToolInput` to `string` (fallback), completely missing the unpacked properties of the data class.
6.  **Complex Nullable/Default Types**:
    *   Default arguments with complex expressions (e.g., `= listOf()`, `= System.getenv(...)`) break the simple comma-split parser logic, leading to malformed schema properties.

## 3. Actionable List of Proposed Fixes

Here is a prioritized list of fixes to improve `parse_kotlin_mcp_code`:

### High Priority
1.  **Support `@Description` on Parameters**:
    *   *Fix*: Update the `parse_parameters` regex to safely strip or extract `@Description(...)` annotations from parameter declarations before parsing the name and type. Inject the extracted description into the parameter's JSON schema under the `description` key.
2.  **Fix Data Class Parameter Unpacking (Basic Level)**:
    *   *Fix*: If a parameter type doesn't map to a primitive, instead of falling back to `"type": "string"`, attempt to locate a `data class {TypeName}` definition in the code. If found, parse its properties and expand the JSON schema into a nested object schema.
3.  **Improve Spring AI/Component Recognition**:
    *   *Fix*: Broaden the annotation regex. Ensure that `@Tool` works reliably even when the class has Spring annotations like `@Component` or `@Service`, and handle Spring's parameter annotations.

### Medium Priority
4.  **Enhance Suspend Function Regex**:
    *   *Fix*: Make the function regex more robust against annotations preceding `suspend fun` (e.g., `@OptIn(...) suspend fun`) and generic type parameters with complex bounds.
5.  **Robust Default Argument Parsing**:
    *   *Fix*: Instead of purely regex-based comma splitting, implement a bracket-aware (parentheses, braces, generics) split to handle complex default values like `name: String = getFallbackName("default, value")`.

### Low Priority
6.  **Ktor Advanced DSL / Routes**:
    *   *Fix*: Expand DSL parsing to support Ktor route bindings if they map directly to tool names (e.g., `route("/tool/...")`).

## 4. Proposed Unit Test Fixtures

Add the following fixtures to `tests/test_ast_kotlin_mcp.py` to drive development:

```python
def test_parameter_description_annotation():
    code = \"\"\"
    @Tool(name = "search")
    fun search(
        @Description("The query string") query: String,
        @Description("Max results") limit: Int = 10
    ) {}
    \"\"\"
    # Expect: parameters 'query' and 'limit' exist, with 'description' fields in the schema.

def test_data_class_parameters():
    code = \"\"\"
    data class SearchRequest(val query: String, val limit: Int = 10)
    
    @Tool(name = "search_data")
    fun searchData(request: SearchRequest) {}
    \"\"\"
    # Expect: schema maps 'request' to an object with properties 'query' (string) and 'limit' (integer).

def test_suspend_function_with_complex_annotations():
    code = \"\"\"
    @OptIn(ExperimentalCoroutinesApi::class)
    @Tool(name = "async_fetch", description = "Fetches data asynchronously")
    suspend fun fetch(url: String): String { ... }
    \"\"\"
    # Expect: Tool "async_fetch" is correctly parsed.
```
