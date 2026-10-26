import pytest
from mcp_fingerprints.ast_parser import parse_golang_mcp_code

def test_inline_string_literal():
    code = """
    package main
import "github.com/modelcontextprotocol/go-sdk/mcp"
    func main() {
        server.AddTool(&mcp.Tool{
            Name: "example_tool",
            Description: "A control tool",
        }, handler)
    }
    """
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "example_tool"
    assert tools[0]["description"] == "A control tool"

def test_constant_name_resolution():
    code = """
    package main
import "github.com/modelcontextprotocol/go-sdk/mcp"
    const toolName = "assess_service_grant"
    const desc = "Assess the service grant"
    func main() {
        server.AddTool(&mcp.Tool{
            Name: toolName,
            Description: desc,
        }, handler)
    }
    """
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "assess_service_grant"
    assert tools[0]["description"] == "Assess the service grant"

def test_block_constants():
    code = """
    package main
import "github.com/modelcontextprotocol/go-sdk/mcp"
    const (
        ToolName1 = "first_tool"
        ToolName2 = "second_tool"
        Desc1 = "First description"
    )
    func main() {
        t1 := mcp.Tool{
            Name: ToolName1,
            Description: Desc1,
        }
        t2 := mcp.Tool{
            Name: ToolName2,
        }
        server.AddTool(&t1, h)
        server.AddTool(&t2, h)
    }
    """
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 2
    
    names = {t["name"]: t for t in tools}
    assert "first_tool" in names
    assert names["first_tool"]["description"] == "First description"
    
    assert "second_tool" in names
    # Description fallback to Title or Name. If Title missing, should fall back to Name.
    assert names["second_tool"]["description"] == "second_tool"

def test_kimjooyoon_gooo_go_ports_reproduction():
    code = """
    package main
import "github.com/modelcontextprotocol/go-sdk/mcp"
    const (
        AssessServiceGrant = "assess_service_grant"
        AssessServiceGrantDesc = "Assess the service grant"
        assessServiceGrantChange = "assess_service_grant_change"
    )
    
    func main() {
        server.AddTool(&mcp.Tool{
            Name: AssessServiceGrant,
            Description: AssessServiceGrantDesc,
        }, handler)
        
        server.AddTool(&mcp.Tool{
            Name: assessServiceGrantChange,
            Description: "check the service grant change",
        }, handler)
    }
    """
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 2
    
    assert tools[0]["name"] == "assess_service_grant"
    assert tools[0]["description"] == "Assess the service grant"
    
    assert tools[1]["name"] == "assess_service_grant_change"
    assert tools[1]["description"] == "check the service grant change"

def test_existing_newtool_builder():
    code = """
    package main
import "github.com/modelcontextprotocol/go-sdk/mcp"
    func init() {
        mcp.NewTool("old_tool", mcp.WithDescription("Old description"))
    }
    """
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "old_tool"
    assert tools[0]["description"] == "Old description"

