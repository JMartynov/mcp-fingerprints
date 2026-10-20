import pytest
import json
from pathlib import Path

from mcp_fingerprints.ast_parser import parse_golang_mcp_code
from mcp_fingerprints.monorepo_prober import match_monorepo_subpackage_dir
from mcp_fingerprints.schema_validator import PassportSchemaValidator

def test_mark3labs_mcp_go_parsing():
    """Test 1: Real mark3labs/mcp-go code snippet parsing."""
    code = """
package main

import (
	"context"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
    s := server.NewMCPServer("test", "1.0.0")
    
    tool := mcp.NewTool("test_tool",
        mcp.WithDescription("Tool description"),
        mcp.WithString("param1", mcp.Required(), mcp.Description("Param desc")),
    )
    s.AddTool(tool, handler)

    s.AddTool(mcp.NewTool("inline_tool",
        mcp.WithDescription("Inline description"),
        mcp.WithNumber("count", mcp.Required()),
    ), handler)
}
"""
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 2
    
    t1 = next(t for t in tools if t["name"] == "test_tool")
    assert t1["description"] == "Tool description"
    assert t1["inputSchema"]["type"] == "object"
    assert "param1" in t1["inputSchema"]["properties"]
    assert t1["inputSchema"]["required"] == ["param1"]

    t2 = next(t for t in tools if t["name"] == "inline_tool")
    assert t2["description"] == "Inline description"
    assert "count" in t2["inputSchema"]["properties"]
    assert t2["inputSchema"]["required"] == ["count"]

def test_nested_cmd_monorepo_discovery():
    """Test 2: Nested /cmd/server monorepo path discovery test."""
    tree_paths = [
        "README.md",
        "go.mod",
        "go.sum",
        "cmd/docker-mcp/main.go",
        "cmd/docker-mcp/server.go",
        "pkg/utils/utils.go"
    ]
    matched = match_monorepo_subpackage_dir("docker-mcp", tree_paths)
    assert matched == "cmd/docker-mcp/"

def test_conformance_validation_go_passport():
    """Test 3: Conformance validation of the representative Go MCP passport."""
    passport_path = Path("data/fingerprints/golang/d/docker-mcp.json")
    assert passport_path.is_file(), "Passport file missing"
    
    with open(passport_path, "r") as f:
        data = json.load(f)
        
    is_valid, errors = PassportSchemaValidator.validate_passport_dict(data)
    assert is_valid, f"Validation failed: {errors}"
