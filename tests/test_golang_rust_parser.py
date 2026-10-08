import pytest
from mcp_fingerprints.ast_parser import parse_golang_mcp_code, parse_rust_mcp_code, parse_mcp_source_code

def test_parse_golang_mcp_code():
    code = """
package main

import (
	"context"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	s := server.NewMCPServer(
		"Test Server",
		"1.0.0",
		server.WithToolCapabilities(true),
	)

	tool := mcp.NewTool("example_tool",
		mcp.WithDescription("An example tool that does something."),
		mcp.WithString("input_text", mcp.Required(), mcp.Description("Some text input")),
		mcp.WithNumber("count", mcp.Description("Number of times")),
		mcp.WithBoolean("is_active"),
	)
	s.AddTool(tool, func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return &mcp.CallToolResult{}, nil
	})

    s.AddTool(mcp.NewTool("another_tool", mcp.WithDescription("simple description")), handler)
}
"""
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 2
    
    t1 = next(t for t in tools if t["name"] == "example_tool")
    assert t1["description"] == "An example tool that does something."
    assert t1["inputSchema"]["type"] == "object"
    assert "input_text" in t1["inputSchema"]["properties"]
    assert t1["inputSchema"]["properties"]["input_text"]["type"] == "string"
    assert t1["inputSchema"]["properties"]["count"]["type"] == "number"
    assert t1["inputSchema"]["properties"]["is_active"]["type"] == "boolean"
    assert t1["inputSchema"]["required"] == ["input_text"]

    t2 = next(t for t in tools if t["name"] == "another_tool")
    assert t2["description"] == "simple description"
    assert t2["inputSchema"]["type"] == "object"
    assert t2["inputSchema"]["properties"] == {}
    assert t2["inputSchema"]["required"] == []


def test_parse_rust_mcp_code():
    code = """
use rmcp::tool;

#[mcp_tool(name = "hello_world", description = "Says hello to the world")]
fn hello_world() -> Result<String, String> {
    Ok("Hello World".to_string())
}

#[mcp_tool(name="no_desc")]
fn no_desc() {}

define_tool!("macro_tool", "Macro description");

fn setup() {
    let t1 = Tool {
        name: "struct_tool".into(),
        description: "Struct description".into(),
    };
    
    let t2 = Tool {
        description: "reverse struct desc".to_string(),
        name: "reverse_struct".to_string(),
    };
}
"""
    tools = parse_rust_mcp_code(code)
    assert len(tools) == 5
    
    assert any(t["name"] == "hello_world" and t["description"] == "Says hello to the world" for t in tools)
    assert any(t["name"] == "no_desc" and t["description"] == "no_desc" for t in tools)
    assert any(t["name"] == "macro_tool" and t["description"] == "Macro description" for t in tools)
    assert any(t["name"] == "struct_tool" and t["description"] == "Struct description" for t in tools)
    assert any(t["name"] == "reverse_struct" and t["description"] == "reverse struct desc" for t in tools)


def test_parse_mcp_source_code_dispatch():
    go_code = """
    package main
    mcp.NewTool("dispatched_go", mcp.WithDescription("test go dispatch"))
    """
    
    rust_code = """
    fn main() {
        let t = Tool { name: "dispatched_rust".into(), description: "test rust dispatch".into() };
    }
    """
    
    res1 = parse_mcp_source_code(go_code, language="go")
    assert len(res1) == 1
    assert res1[0]["name"] == "dispatched_go"
    
    res2 = parse_mcp_source_code(rust_code, language="rust")
    assert len(res2) == 1
    assert res2[0]["name"] == "dispatched_rust"

    # Test heuristics fallback
    res3 = parse_mcp_source_code(go_code, language=None)
    assert len(res3) == 1
    assert res3[0]["name"] == "dispatched_go"

    res4 = parse_mcp_source_code(rust_code, language=None)
    assert len(res4) == 1
    assert res4[0]["name"] == "dispatched_rust"
