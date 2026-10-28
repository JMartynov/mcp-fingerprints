import pytest
from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor

def test_json_manifest():
    auditor = DeepZeroToolAuditor()
    content = '{"tools": [{"name": "my_tool", "description": "test"}]}'
    tools = auditor.inspect_file("mcp.json", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "my_tool"
    assert tools[0]["format"] == "JSON Config"

def test_openapi_spec():
    auditor = DeepZeroToolAuditor()
    content = '{"openapi": "3.0.0", "paths": {"/test": {"get": {"operationId": "test_op"}}}}'
    tools = auditor.inspect_file("openapi.json", content)
    assert len(tools) == 1
    assert tools[0]["format"] == "OpenAPI / Swagger Spec"
    assert tools[0]["name"] == "test_op"

def test_markdown_table():
    auditor = DeepZeroToolAuditor()
    content = """
# Tools
| Tool | Description | Arguments |
|---|---|---|
| search | Search data | query |
| read | Read data | id |
    """
    tools = auditor.inspect_file("README.md", content)
    assert len(tools) == 2
    assert tools[0]["name"] == "search"
    assert tools[1]["name"] == "read"
    assert tools[0]["format"] == "Markdown Table"

def test_ts_dynamic_array():
    auditor = DeepZeroToolAuditor()
    content = """
    const TOOLS = [{name: "test"}];
    TOOLS.forEach(t => server.tool(t.name, ...));
    """
    tools = auditor.inspect_file("index.ts", content)
    assert len(tools) == 1
    assert tools[0]["format"] == "Dynamic Array Iteration"

def test_py_custom_decorator():
    auditor = DeepZeroToolAuditor()
    content = """
@action(description="test")
def my_custom_tool():
    pass
    """
    tools = auditor.inspect_file("tools.py", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "my_custom_tool"
    assert tools[0]["format"] == "Custom Decorators"

def test_ts_register_tool():
    auditor = DeepZeroToolAuditor()
    content = """
    server.registerTool("myTsTool", "test", ...);
    """
    tools = auditor.inspect_file("index.ts", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "myTsTool"
    assert tools[0]["format"] == "Explicit Tool Registration"

def test_ts_server_tool():
    auditor = DeepZeroToolAuditor()
    content = """
    server.tool('myOtherTsTool', ...);
    """
    tools = auditor.inspect_file("index.ts", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "myOtherTsTool"
    assert tools[0]["format"] == "Explicit Tool Registration"

def test_py_explicit_tool():
    auditor = DeepZeroToolAuditor()
    content = """
    t = Tool(name="myPyTool", description="test")
    """
    tools = auditor.inspect_file("tools.py", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "myPyTool"
    assert tools[0]["format"] == "Explicit Tool Instantiation"
