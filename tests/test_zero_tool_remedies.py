import pytest
from mcp_fingerprints.ast_parser import (
    parse_mcp_source_code,
    parse_python_mcp_ast,
    parse_typescript_mcp_ast
)

def test_json_manifest_parser_root_array():
    code = """
    [
      {
        "name": "seamless_translate",
        "description": "Translate text",
        "inputSchema": {
          "type": "object",
          "properties": {
            "text": {"type": "string"}
          },
          "required": ["text"]
        }
      }
    ]
    """
    tools = parse_mcp_source_code(code, language="json")
    assert len(tools) == 1
    assert tools[0]["name"] == "seamless_translate"

def test_json_manifest_parser_tools_object():
    code = """
    {
      "tools": [
        {
          "name": "another_tool",
          "description": "Another tool",
          "parameters": {
            "type": "object",
            "properties": {
              "param1": {"type": "string"}
            }
          }
        }
      ]
    }
    """
    tools = parse_mcp_source_code(code, language="json")
    assert len(tools) == 1
    assert tools[0]["name"] == "another_tool"

def test_python_alternative_decorators():
    code = """
class MyServer:
    @action(name="mock_security_tool", description="Runs a mock scan")
    def my_scan(self, target: str):
        pass
        
    @command
    def check_status(self):
        \"\"\"Check the status.\"\"\"
        pass
        
    @tool
    def other_tool(self):
        pass
    """
    tools = parse_python_mcp_ast(code)
    # The output is wrapped in AstBundleResult
    tools_list = tools.tools if hasattr(tools, "tools") else tools
    assert len(tools_list) == 3
    names = [t["name"] for t in tools_list]
    assert "mock_security_tool" in names
    assert "check_status" in names
    assert "other_tool" in names

def test_typescript_dynamic_array_resolution():
    code = """
    const DYNAMIC_TOOLS = [
        {
            name: "dynamic_array_tools",
            description: "A tool in a dynamic array",
            inputSchema: {
                type: "object",
                properties: {}
            }
        }
    ];

    server.setRequestHandler(ListToolsRequestSchema, async () => {
        return {
            tools: DYNAMIC_TOOLS
        };
    });
    """
    tools = parse_typescript_mcp_ast(code)
    tools_list = tools.tools if hasattr(tools, "tools") else tools
    assert len(tools_list) == 1
    assert tools_list[0]["name"] == "dynamic_array_tools"
