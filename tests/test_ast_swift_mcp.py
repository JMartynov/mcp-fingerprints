import pytest
from mcp_fingerprints.ast_parser import parse_swift_mcp_code, parse_mcp_source_code

def test_swift_struct_mcp_tool():
    code = """
import Foundation
import MCP

struct WeatherTool: MCPTool {
    let name = "get_weather"
    var description: String { "Get current weather for a location." }

    struct Arguments: Codable {
        let location: String
        var unit: String?
        let limit: Int
        let options: [String: Any]?
    }
}
"""
    tools = parse_swift_mcp_code(code)
    assert len(tools) == 1
    tool = tools[0]
    assert tool["name"] == "get_weather"
    assert tool["description"] == "Get current weather for a location."
    schema = tool["inputSchema"]
    assert schema["type"] == "object"
    assert "location" in schema["properties"]
    assert schema["properties"]["location"]["type"] == "string"
    assert "unit" in schema["properties"]
    assert schema["properties"]["unit"]["type"] == "string"
    assert "limit" in schema["properties"]
    assert schema["properties"]["limit"]["type"] == "integer"
    assert "options" in schema["properties"]
    assert schema["properties"]["options"]["type"] == "object"
    
    assert set(schema["required"]) == {"location", "limit"}

def test_swift_macro_mcp_tool():
    code = """
import Foundation

@McpTool(name: "search_db", description: "Search the database")
public func searchDatabase(
    _ query: String,
    limit: Int32 = 10,
    filters: [String]?,
    dryRun: Bool
) -> String {
    return "results"
}

@Tool
func basicTask(val: Double) { }
"""
    tools = parse_swift_mcp_code(code)
    assert len(tools) == 2
    
    t1 = tools[0]
    assert t1["name"] == "search_db"
    assert t1["description"] == "Search the database"
    s1 = t1["inputSchema"]
    assert s1["properties"]["query"]["type"] == "string"
    assert s1["properties"]["limit"]["type"] == "integer"
    assert s1["properties"]["filters"]["type"] == "array"
    assert s1["properties"]["dryRun"]["type"] == "boolean"
    # limit has a default value so it's considered optional by the heuristic (contains =)
    # query and dryRun are required
    assert set(s1["required"]) == {"query", "dryRun"}
    
    t2 = tools[1]
    assert t2["name"] == "basicTask"
    assert t2["description"] == "basicTask"
    assert t2["inputSchema"]["properties"]["val"]["type"] == "number"
    assert set(t2["inputSchema"]["required"]) == {"val"}

def test_swift_register_tool():
    code = """
import Foundation

func setup(server: MCPServer) {
    server.registerTool("math_add", description: "Adds two numbers together") { req in 
        // ...
    }
}
"""
    tools = parse_swift_mcp_code(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "math_add"
    assert tools[0]["description"] == "Adds two numbers together"
    assert tools[0]["inputSchema"] == {"type": "object", "properties": {}, "required": []}

def test_dispatcher_integration():
    code = """
import Foundation

struct FetchTool: ToolDefinition {
    let name = "fetch"
    let description = "Fetch data"
    
    struct Input: Decodable {
        let url: String
    }
}
"""
    # Using explicit language
    tools1 = parse_mcp_source_code(code, language="swift")
    assert len(tools1) == 1
    assert tools1[0]["name"] == "fetch"
    
    # Using auto-detection
    tools2 = parse_mcp_source_code(code)
    assert len(tools2) == 1
    assert tools2[0]["name"] == "fetch"

