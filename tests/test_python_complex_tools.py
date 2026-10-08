import pytest
from mcp_fingerprints.ast_parser import parse_python_mcp_ast

def test_extract_basetool_class():
    code = """
from pydantic import BaseModel

class WeatherInput(BaseModel):
    location: str
    unit: str = "celsius"

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get the current weather in a given location"
    args_schema = WeatherInput

    def _run(self, location: str, unit: str):
        pass
"""
    tools = parse_python_mcp_ast(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "get_weather"
    assert tools[0]["description"] == "Get the current weather in a given location"
    assert "location" in tools[0]["inputSchema"]["properties"]
    assert "unit" in tools[0]["inputSchema"]["properties"]
    assert "location" in tools[0]["inputSchema"]["required"]

def test_extract_tool_decorator():
    code = """
@tool
def simple_tool():
    pass

@tool()
def another_tool():
    pass

@tool(name="custom", description="custom desc")
def third_tool():
    pass
"""
    tools = parse_python_mcp_ast(code)
    assert len(tools) == 3
    assert tools[0]["name"] == "simple_tool"
    assert tools[1]["name"] == "another_tool"
    assert tools[2]["name"] == "custom"
    assert tools[2]["description"] == "custom desc"

def test_extract_tool_manager_register():
    code = """
@tool_manager.register("some_tool", description="A tool")
def my_tool(x: int):
    pass
"""
    tools = parse_python_mcp_ast(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "some_tool"
    assert tools[0]["description"] == "A tool"
    assert "x" in tools[0]["inputSchema"]["properties"]
    assert "x" in tools[0]["inputSchema"]["required"]

def test_extract_tool_class_without_args_schema():
    code = """
class SimpleTool(Tool):
    name = "simple"
    description = "A simple tool"
"""
    tools = parse_python_mcp_ast(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "simple"
    assert tools[0]["description"] == "A simple tool"
    assert tools[0]["inputSchema"]["properties"] == {}

def test_extract_tool_class_with_annassign():
    code = """
class AnnAssignTool(BaseTool):
    name: str = "ann_assign"
    description: str = "ann assign tool"
"""
    tools = parse_python_mcp_ast(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "ann_assign"
    assert tools[0]["description"] == "ann assign tool"
