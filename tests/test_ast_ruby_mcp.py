import pytest
from mcp_fingerprints.ast_parser import parse_ruby_mcp_code, parse_mcp_source_code

def test_ruby_dsl_block_definition():
    code = """
    server.register_tool(:get_weather, description: "Get the current weather") do |args|
      param :city, type: :string, required: true, desc: "The city to get weather for"
      param :unit, type: String, required: false
      
      { weather: "Sunny" }
    end
    """
    tools = parse_ruby_mcp_code(code)
    assert len(tools) == 1
    t = tools[0]
    assert t["name"] == "get_weather"
    assert t["description"] == "Get the current weather"
    assert "city" in t["inputSchema"]["properties"]
    assert t["inputSchema"]["properties"]["city"]["type"] == "string"
    assert t["inputSchema"]["properties"]["city"]["description"] == "The city to get weather for"
    assert "unit" in t["inputSchema"]["properties"]
    assert t["inputSchema"]["properties"]["unit"]["type"] == "string"
    assert t["inputSchema"]["required"] == ["city"]

def test_ruby_class_based_definition():
    code = """
    class QueryDbTool < MCP::Tool
      name "query_db"
      description 'Query the database'
      
      argument :query_string, type: :string, required: true, desc: "SQL query"
      argument :limit, type: Integer, required: false
      
      def execute
        # ...
      end
    end
    """
    tools = parse_ruby_mcp_code(code)
    assert len(tools) == 1
    t = tools[0]
    assert t["name"] == "query_db"
    assert t["description"] == "Query the database"
    assert t["inputSchema"]["properties"]["query_string"]["type"] == "string"
    assert t["inputSchema"]["properties"]["limit"]["type"] == "number"
    assert t["inputSchema"]["required"] == ["query_string"]

def test_ruby_dispatcher_integration():
    code = """
    require "mcp"
    def setup_server
      server.register_tool(:echo, "Echo back") do
        param :message, type: :string, required: true
      end
    end
    """
    tools = parse_mcp_source_code(code) # Should auto-detect ruby
    assert len(tools) == 1
    assert tools[0]["name"] == "echo"
    assert tools[0]["description"] == "Echo back"
    assert tools[0]["inputSchema"]["required"] == ["message"]

def test_ruby_real_world_fixtures():
    code = """
    tool :calculate_sum, description: "Calculate sum of numbers" do
      param :a, type: :float, required: true
      param :b, type: :float, required: true
      a + b
    end
    """
    tools = parse_ruby_mcp_code(code)
    assert len(tools) == 1
    t = tools[0]
    assert t["name"] == "calculate_sum"
    assert t["description"] == "Calculate sum of numbers"
    assert t["inputSchema"]["properties"]["a"]["type"] == "number"
    assert t["inputSchema"]["properties"]["b"]["type"] == "number"
    assert t["inputSchema"]["required"] == ["a", "b"]

def test_ruby_class_tool_no_mcp_prefix():
    code = """
    class SimpleTool < Tool
      @name = "simple"
      @description = "Simple tool"
      argument :flag, type: :boolean, required: false
    end
    """
    tools = parse_ruby_mcp_code(code)
    assert len(tools) == 1
    t = tools[0]
    assert t["name"] == "simple"
    assert t["description"] == "Simple tool"
    assert t["inputSchema"]["properties"]["flag"]["type"] == "boolean"
    assert t["inputSchema"]["required"] == []
