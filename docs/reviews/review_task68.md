# EULIS Code Review & Gap Analysis: Task 68 (Ruby MCP AST Parser)

## 1. Executive Summary & Verification Findings
The implementation of `parse_ruby_mcp_code` in `src/mcp_fingerprints/ast_parser.py` provides a foundational static analysis capability for extracting Model Context Protocol (MCP) tool definitions from Ruby source code. It successfully parses common DSL block registrations (e.g., `server.register_tool`) and basic class-based definitions inheriting from `Tool` or `MCP::Tool`. 

However, a review of the 200 real-world Ruby MCP repositories collected in `data/samples/ruby_mcp_200.json` (such as `rails-mcp-server`, `tidewave_rails`, `mcp-rb`, `sketchup-mcp2`, etc.) reveals several gaps in pattern recognition. Modern Ruby and Rails idioms, advanced type systems like Dry-types, and alternative DSLs like FastMCP are not fully supported, leading to missed tool definitions and incomplete input schemas.

## 2. Caught Capabilities vs Missed Tool Definitions

### What is Currently Caught
- **DSL Registrations:** `server.register_tool(:name) do ... end` and `tool :name do ... end`.
- **Parameter Extraction:** Recognizes `param` and `argument` keywords within DSL blocks or class definitions.
- **Type Mapping:** Basic mapping of raw Ruby types (e.g., `Integer`, `String`, `:boolean`) to JSON Schema equivalents (`number`, `string`, `boolean`, `array`, `object`).
- **Class-Based Tools:** Identifies classes inheriting from `Tool` (e.g., `class MyTool < MCP::Tool`) and extracts standard attributes like `@name` or `name "..."`.

### What is Missed (Real-World Repositories)
1. **Block Keyword Arguments:** Inline parameter definitions within Ruby blocks, such as `tool(:name) { |param1:, param2: "default"| ... }`.
2. **Dry-Types / Attribute Declarations:** Class-based tools using typed attributes (e.g., `attribute :foo, Types::String` or `attribute? :bar, Types::Integer.optional`).
3. **Docstrings and `desc` Declarations:** Tool descriptions provided via preceding comment docstrings (`# This tool does X`) or explicit `desc "..."` declarations above method/class definitions.
4. **Heredoc Descriptions:** Multiline strings used for detailed descriptions via `<<~DESC` or `<<-EOF`.
5. **FastMCP Ruby Syntax:** Methods exposed automatically as tools using FastMCP-like decorators or routing setups, which don't explicitly use `server.register_tool` or `class < Tool`.
6. **Block Braces `{ ... }`:** The regex strictly requires `do`, missing tools defined with `{ ... }` syntax.

## 3. Actionable List of Proposed Fixes

### High Priority
- **Support Curly Brace Blocks:** Update `dsl_regex` to match `do` OR `{` blocks, as single-line tools often use `{ ... }`.
- **Block Keyword Arguments Extraction:** Parse block parameters enclosed in `|...|` to extract input schemas for DSL definitions (e.g., `|param1:, param2: "default"|`).
- **Heredoc Support:** Enhance description parsing to handle `<<~`, `<<-`, and `<<` heredocs, which are heavily used in real Ruby MCP servers for prompt/tool instructions.

### Medium Priority
- **Attribute Declarations (Dry-types):** Add regex patterns to capture `attribute` and `attribute?` declarations in class-based tools, mapping `Types::String`, `Types::Integer`, etc., to JSON Schema.
- **Support `desc` Declarations:** Capture `desc "..."` statements that may precede tool definitions or be used inside class bodies instead of `description`.

### Low Priority
- **Docstring Parsing:** Extract `#` comments immediately preceding `tool` or `def` statements to use as fallback descriptions.
- **FastMCP Syntax Variations:** Investigate and support specific FastMCP routing/decoration patterns used in Ruby.

## 4. Proposed Unit Test Fixtures

To ensure these gaps are addressed, the following test fixtures should be added to `tests/test_ast_ruby_mcp.py`:

```python
def test_ruby_block_keyword_arguments():
    code = """
    tool(:greet) { |name:, title: "Mr."| 
      "Hello #{title} #{name}"
    }
    """
    tools = parse_ruby_mcp_code(code)
    assert len(tools) == 1
    assert "name" in tools[0]["inputSchema"]["properties"]
    assert "title" in tools[0]["inputSchema"]["properties"]

def test_ruby_dry_types_attributes():
    code = """
    class SearchTool < MCP::Tool
      name "search"
      desc "Search the database"
      
      attribute :query, Types::String
      attribute? :limit, Types::Integer.default(10)
    end
    """
    tools = parse_ruby_mcp_code(code)
    assert len(tools) == 1
    props = tools[0]["inputSchema"]["properties"]
    assert props["query"]["type"] == "string"
    assert props["limit"]["type"] == "number"
    assert "query" in tools[0]["inputSchema"]["required"]
    assert "limit" not in tools[0]["inputSchema"]["required"]

def test_ruby_heredoc_description():
    code = """
    server.register_tool(:complex_task) do
      description <<~DESC
        This is a multi-line
        description for a complex task.
      DESC
      param :input, type: String
    end
    """
    tools = parse_ruby_mcp_code(code)
    assert len(tools) == 1
    assert "multi-line" in tools[0]["description"]
```
