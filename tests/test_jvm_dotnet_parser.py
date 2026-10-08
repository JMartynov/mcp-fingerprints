import pytest
from mcp_fingerprints.ast_parser import parse_jvm_mcp_code, parse_dotnet_mcp_code, parse_mcp_source_code


def test_parse_jvm_mcp_code():
    code = """
public class MyTools {
    @Tool(name = "my_tool", description = "my tool description")
    public String myTool(String paramName, int count) {
        return "ok";
    }
}

class KotlinTools {
    @Tool("kotlin tool desc")
    fun kotlinTool(name: String, count: Int, items: List<String>): String {
        return "ok"
    }
}

public class McpTools {
    @McpFunction(name = "mcp_tool")
    public void mcpTool(@Valid Map<String, Integer> data, int limit = 10) {}
}
"""
    tools = parse_jvm_mcp_code(code)
    assert len(tools) == 3
    
    t1 = next(t for t in tools if t["name"] == "my_tool")
    assert t1["description"] == "my tool description"
    assert t1["inputSchema"]["properties"]["paramName"]["type"] == "string"
    assert t1["inputSchema"]["properties"]["count"]["type"] == "number"
    assert t1["inputSchema"]["required"] == sorted(["paramName", "count"])

    t2 = next(t for t in tools if t["name"] == "kotlinTool")
    assert t2["description"] == "kotlin tool desc"
    assert t2["inputSchema"]["properties"]["name"]["type"] == "string"
    assert t2["inputSchema"]["properties"]["count"]["type"] == "number"
    assert t2["inputSchema"]["properties"]["items"]["type"] == "array"
    assert t2["inputSchema"]["required"] == sorted(["name", "count", "items"])

    t3 = next(t for t in tools if t["name"] == "mcp_tool")
    assert t3["description"] == "mcp_tool"
    assert t3["inputSchema"]["properties"]["data"]["type"] == "object"
    assert t3["inputSchema"]["properties"]["limit"]["type"] == "number"
    assert t3["inputSchema"]["required"] == sorted(["data", "limit"])


def test_parse_dotnet_mcp_code():
    code = """
public class MyServer {
    [McpTool("csharp_tool", "csharp desc")]
    public string MyCSharpTool(string name, int count = 0, List<string> items) {
        return "ok";
    }
}

[McpFunction("func_tool")]
[Description("func desc")]
public async Task<string> FuncTool(bool flag, Dictionary<string, string>? mapping) {
}

server.AddTool("added_tool", "added desc", (req) => {});
var t = new McpTool("new_tool", "new desc");
"""
    tools = parse_dotnet_mcp_code(code)
    assert len(tools) == 4
    
    t1 = next(t for t in tools if t["name"] == "csharp_tool")
    assert t1["description"] == "csharp desc"
    assert t1["inputSchema"]["properties"]["name"]["type"] == "string"
    assert t1["inputSchema"]["properties"]["count"]["type"] == "number"
    assert t1["inputSchema"]["properties"]["items"]["type"] == "array"
    assert t1["inputSchema"]["required"] == sorted(["name", "items"])

    t2 = next(t for t in tools if t["name"] == "func_tool")
    assert t2["description"] == "func desc"
    assert t2["inputSchema"]["properties"]["flag"]["type"] == "boolean"
    assert t2["inputSchema"]["properties"]["mapping"]["type"] == "object"
    assert t2["inputSchema"]["required"] == sorted(["flag"])

    t3 = next(t for t in tools if t["name"] == "added_tool")
    assert t3["description"] == "added desc"
    assert t3["inputSchema"]["properties"] == {}

    t4 = next(t for t in tools if t["name"] == "new_tool")
    assert t4["description"] == "new desc"
    assert t4["inputSchema"]["properties"] == {}


def test_parse_mcp_source_code_jvm_dotnet():
    java_code = """
    package com.example;
    public class MyTools {
        @Tool(name = "dispatched_java", description = "test java dispatch")
        public void dispatchedJava() {}
    }
    """
    
    csharp_code = """
    using ModelContextProtocol;
    namespace MyCompany {
        public class MyTools {
            [McpTool("dispatched_csharp", "test csharp dispatch")]
            public void DispatchedCSharp() {}
        }
    }
    """
    
    res1 = parse_mcp_source_code(java_code, language="java")
    assert len(res1) == 1
    assert res1[0]["name"] == "dispatched_java"
    
    res2 = parse_mcp_source_code(csharp_code, language="cs")
    assert len(res2) == 1
    assert res2[0]["name"] == "dispatched_csharp"

    # Test heuristics fallback
    res3 = parse_mcp_source_code(java_code, language=None)
    assert len(res3) == 1
    assert res3[0]["name"] == "dispatched_java"

    res4 = parse_mcp_source_code(csharp_code, language=None)
    assert len(res4) == 1
    assert res4[0]["name"] == "dispatched_csharp"
