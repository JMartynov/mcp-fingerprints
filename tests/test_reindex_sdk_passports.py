import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.mcp_fingerprints.reindex_sdk_passports import (
    get_repo_owner_name,
    extract_tools_from_repo,
    update_passport_tools
)

def test_get_repo_owner_name():
    owner, repo = get_repo_owner_name("https://github.com/soil-dev/capsulemcp")
    assert owner == "soil-dev"
    assert repo == "capsulemcp"
    
    owner, repo = get_repo_owner_name("https://github.com/awkoy/notion-mcp-server.git")
    assert owner == "awkoy"
    assert repo == "notion-mcp-server"

@patch("src.mcp_fingerprints.reindex_sdk_passports._request_with_backoff")
@patch("src.mcp_fingerprints.reindex_sdk_passports.fetch_raw_file")
def test_extract_tools_from_repo(mock_fetch_raw, mock_request):
    mock_request.side_effect = [
        {"default_branch": "main"},  # Repo fetch
        {"tree": [{"path": "index.ts", "type": "blob"}]} # Tree fetch
    ]
    mock_fetch_raw.return_value = """
        server.tool("test_tool", "A test tool", {
            name: z.string()
        }, async ({ name }) => { return name; });
    """
    
    tools = extract_tools_from_repo("test-owner", "test-repo")
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert "description" in tools[0]

def test_update_passport_tools():
    dummy_passport = {
        "versions": [{
            "version": "1.0.0",
            "tool_signatures": [],
            "capabilities": {"tools": False}
        }]
    }
    
    dummy_tools = [{
        "name": "extracted_tool",
        "description": "desc",
        "inputSchema": {"type": "object"}
    }]
    
    with patch("builtins.open", mock_open(read_data=json.dumps(dummy_passport))) as m:
        with patch("json.dump") as mock_dump:
            res = update_passport_tools(Path("dummy.json"), dummy_tools)
            assert res is True
            # Check what was dumped
            args, kwargs = mock_dump.call_args
            updated_data = args[0]
            assert len(updated_data["versions"][0]["tool_signatures"]) == 1
            assert updated_data["versions"][0]["tool_signatures"][0]["name"] == "extracted_tool"
            assert updated_data["versions"][0]["capabilities"]["tools"] is True
            assert "canonical_hash" in updated_data["versions"][0]["tool_signatures"][0]


@patch("src.mcp_fingerprints.reindex_sdk_passports._request_with_backoff")
@patch("src.mcp_fingerprints.reindex_sdk_passports.fetch_raw_file")
def test_extract_tools_from_repo_python(mock_fetch_raw, mock_request):
    mock_request.side_effect = [
        {"default_branch": "main"},  # Repo fetch
        {"tree": [{"path": "main.py", "type": "blob"}]} # Tree fetch
    ]
    mock_fetch_raw.return_value = """
from mcp import Tool
def get_tools():
    return [
        Tool(name="python_tool", description="A python test tool", inputSchema={"type": "object"})
    ]
"""
    
    tools = extract_tools_from_repo("test-owner", "test-repo")
    assert len(tools) == 1
    assert tools[0]["name"] == "python_tool"
    assert "description" in tools[0]

@patch("src.mcp_fingerprints.reindex_sdk_passports._request_with_backoff")
@patch("src.mcp_fingerprints.reindex_sdk_passports.fetch_raw_file")
def test_extract_tools_from_repo_go(mock_fetch_raw, mock_request):
    mock_request.side_effect = [
        {"default_branch": "main"},  # Repo fetch
        {"tree": [{"path": "main.go", "type": "blob"}]} # Tree fetch
    ]
    mock_fetch_raw.return_value = '''
        package main
        
        var tool = mcp.NewTool("go_tool",
            mcp.WithDescription("A go test tool"),
        )
    '''
    
    tools = extract_tools_from_repo("test-owner", "test-repo")
    assert len(tools) == 1
    assert tools[0]["name"] == "go_tool"
    assert "description" in tools[0]

@patch("src.mcp_fingerprints.reindex_sdk_passports._request_with_backoff")
@patch("src.mcp_fingerprints.reindex_sdk_passports.fetch_raw_file")
def test_extract_tools_from_repo_markdown(mock_fetch_raw, mock_request):
    mock_request.side_effect = [
        {"default_branch": "main"},  # Repo fetch
        {"tree": [{"path": "README.md", "type": "blob"}]} # Tree fetch
    ]
    mock_fetch_raw.return_value = '''
        # Tools
        
        | Name | Description | Parameters |
        | --- | --- | --- |
        | md_tool | A markdown test tool | param1: string |
    '''
    
    tools = extract_tools_from_repo("test-owner", "test-repo")
    assert len(tools) == 1
    assert tools[0]["name"] == "md_tool"
    assert "description" in tools[0]
