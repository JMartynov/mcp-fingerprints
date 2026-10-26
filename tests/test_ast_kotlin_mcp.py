import pytest
from mcp_fingerprints.ast_parser import parse_kotlin_mcp_code

def test_spring_ai_bean():
    code = """
    @Service
    class MyAiService {
        @Tool(name = "get_weather", description = "Get current weather")
        fun getWeather(location: String): String { return "sunny" }
    }
    """
    res = parse_kotlin_mcp_code(code)
    assert len(res) == 1
    assert res[0]["name"] == "get_weather"
    assert res[0]["inputSchema"]["properties"]["location"]["type"] == "string"

def test_param_description():
    code = """
    @Tool
    fun getWeather(
        @Description("The city name") location: String
    ): String { return "sunny" }
    """
    res = parse_kotlin_mcp_code(code)
    assert len(res) == 1
    assert res[0]["name"] == "getWeather"
    assert "description" in res[0]["inputSchema"]["properties"]["location"]
    assert res[0]["inputSchema"]["properties"]["location"]["description"] == "The city name"

def test_data_class():
    code = """
    data class WeatherRequest(
        @Description("City name") val city: String,
        val days: Int = 1
    )

    @Tool
    fun getWeather(req: WeatherRequest): String { return "sunny" }
    """
    res = parse_kotlin_mcp_code(code)
    assert len(res) == 1
    assert res[0]["name"] == "getWeather"
    assert res[0]["inputSchema"]["properties"]["req"]["type"] == "object"
    assert "properties" in res[0]["inputSchema"]["properties"]["req"]
    assert "city" in res[0]["inputSchema"]["properties"]["req"]["properties"]
    assert res[0]["inputSchema"]["properties"]["req"]["properties"]["city"]["type"] == "string"
    assert res[0]["inputSchema"]["properties"]["req"]["properties"]["city"]["description"] == "City name"

def test_suspend_complex():
    code = """
    @Tool(name="complex_tool")
    override suspend fun complexTool(
        config: Map<String, List<Int>>,
        options: String = "default, with, commas"
    ) { }
    """
    res = parse_kotlin_mcp_code(code)
    assert len(res) == 1
    assert res[0]["name"] == "complex_tool"
    assert res[0]["inputSchema"]["properties"]["config"]["type"] == "object"
    assert res[0]["inputSchema"]["properties"]["options"]["type"] == "string"
    assert "options" not in res[0]["inputSchema"]["required"]
    assert "config" in res[0]["inputSchema"]["required"]

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

from mcp_fingerprints.ast_parser import parse_mcp_source_code

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
