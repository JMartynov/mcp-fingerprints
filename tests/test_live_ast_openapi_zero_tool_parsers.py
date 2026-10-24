import pytest
from mcp_fingerprints.ast_parser import parse_mcp_source_code
from mcp_fingerprints.openapi_parser import parse_openapi_spec
from mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from mcp_fingerprints.sanitizer import sanitize_unicode_text

def get_tools(result):
    return getattr(result, "tools", result)

def test_ast_python_fastmcp():
    code = """
from mcp.server.fastmcp import FastMCP
mcp = FastMCP()
@mcp.tool()
def get_weather(location: str):
    '''Get the weather for a location'''
    pass
"""
    tools = get_tools(parse_mcp_source_code(code, "python"))
    assert len(tools) == 1
    assert tools[0]["name"] == "get_weather"

def test_ast_typescript_zod():
    code = """
import { z } from "zod";
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "calculate_sum") {
    // ...
  }
});
const sumSchema = z.object({ a: z.number(), b: z.number() });
"""
    tools = get_tools(parse_mcp_source_code(code, "typescript"))
    assert len(tools) == 1
    assert tools[0]["name"] == "calculate_sum"

def test_ast_go_mcp():
    code = """
package main
import "github.com/mark3labs/mcp-go/mcp"
func main() {
    tool := mcp.NewTool("fetch_data",
        mcp.WithDescription("Fetches data"),
        mcp.WithString("url", mcp.Required(), mcp.Description("The URL")),
    )
}
"""
    tools = get_tools(parse_mcp_source_code(code, "go"))
    assert len(tools) == 1
    assert tools[0]["name"] == "fetch_data"
    assert tools[0]["description"] == "Fetches data"

def test_ast_rust_mcp():
    code = """
use rmcp::tool;
#[tool]
fn process_text(input: String) -> String {
    input
}
"""
    tools = get_tools(parse_mcp_source_code(code, "rust"))
    assert len(tools) == 1
    assert tools[0]["name"] == "process_text"

def test_ast_jvm_mcp():
    code = """
import org.springframework.ai.tool.annotation.Tool;
public class MyTools {
    @Tool(description = "Calculates something")
    public int calculate(int a) {
        return a;
    }
}
"""
    tools = get_tools(parse_mcp_source_code(code, "java"))
    assert len(tools) == 1
    assert tools[0]["name"] == "calculate"

def test_ast_dotnet_mcp():
    code = """
public class MyPlugin {
    [McpServerTool("GetData", "Gets the data")]
    public string GetData(string id) {
        return id;
    }
}
"""
    tools = get_tools(parse_mcp_source_code(code, "csharp"))
    assert len(tools) == 1
    assert tools[0]["name"] == "GetData"

def test_openapi_parser():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0"},
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get items",
                    "operationId": "getItems",
                    "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}]
                }
            }
        }
    }
    tools = parse_openapi_spec(spec)
    assert len(tools) == 1
    assert tools[0]["name"] == "getItems"

def test_markdown_doc_parser():
    md = """
# Available Tools
| Tool | Description | Arguments |
|---|---|---|
| `search` | Searches the web | `query` |
"""
    tools = parse_markdown_tool_docs(md)
    assert len(tools) == 1
    assert tools[0]["name"] == "search"

def test_unicode_sanitization_invariants():
    text = "Hello\x00World\x1F! 你好，世界！🌍 ✨ \x0B\x0C Café résumé Русский текст"
    sanitized = sanitize_unicode_text(text)
    assert "\x00" not in sanitized
    assert "\x1F" not in sanitized
    assert "\x0B" not in sanitized
    assert "\x0C" not in sanitized
    assert "你好，世界！" in sanitized
    assert "🌍" in sanitized
    assert "Café résumé" in sanitized
    assert "Русский текст" in sanitized

