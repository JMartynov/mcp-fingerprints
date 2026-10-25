import pytest
from mcp_fingerprints.ast_parser import parse_kotlin_mcp_code, parse_mcp_source_code

def test_annotation_basic():
    code = """
    @Tool(name = "hello", description = "Says hello")
    fun sayHello(name: String, age: Int? = null) { }
    """
    res = parse_kotlin_mcp_code(code)
    assert len(res) == 1
    assert res[0]["name"] == "hello"
    assert res[0]["description"] == "Says hello"
    assert res[0]["inputSchema"]["properties"]["name"]["type"] == "string"
    assert res[0]["inputSchema"]["properties"]["age"]["type"] == "integer"
    assert "name" in res[0]["inputSchema"]["required"]
    assert "age" not in res[0]["inputSchema"]["required"]

def test_dsl():
    code = """
    mcpServer {
        tool("my_tool") {
            description = "My Tool Desc"
        }
    }
    """
    res = parse_kotlin_mcp_code(code)
    assert len(res) == 1
    assert res[0]["name"] == "my_tool"
    assert res[0]["description"] == "My Tool Desc"

def test_class():
    code = """
    class MyCustomTool(
        override val name: String = "custom_tool"
    ) : McpTool {
        override val description: String = "A custom tool"
    }
    """
    res = parse_kotlin_mcp_code(code)
    assert len(res) == 1
    assert res[0]["name"] == "custom_tool"
    assert res[0]["description"] == "A custom tool"

if __name__ == "__main__":
    pytest.main(["-v", "test_parse_kotlin_mcp.py"])

def test_parse_mcp_source_code_dispatcher():
    code = """
    @Tool(name = "hello", description = "Says hello")
    fun sayHello(name: String, age: Int? = null) { }
    """
    res_kt = parse_mcp_source_code(code, language="kotlin")
    assert len(res_kt) == 1
    assert res_kt[0]["name"] == "hello"

    res_auto = parse_mcp_source_code(code)
    assert len(res_auto) == 1
    assert res_auto[0]["name"] == "hello"
