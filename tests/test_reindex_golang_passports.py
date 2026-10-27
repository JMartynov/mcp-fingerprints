#!/usr/bin/env python3
"""
Unit tests for reindex_golang_passports.py
"""

import json
import pytest
from pathlib import Path
from src.mcp_fingerprints.go_sdk_parser import parse_official_go_tools

def test_parse_official_go_tools_composite_and_constants():
    code = '''
    package main
    import "github.com/modelcontextprotocol/go-sdk/mcp"

    const myToolName = "calculate_sum"

    func main() {
        server.AddTool(&mcp.Tool{
            Name: myToolName,
            Description: "Calculate sum of numbers",
        }, handler)
    }
    '''
    tools = parse_official_go_tools(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "calculate_sum"
    assert tools[0]["description"] == "Calculate sum of numbers"
