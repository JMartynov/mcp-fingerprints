import pytest
from scripts.normalize_catalog_tools import normalize_server_item

def test_normalize_server_item_with_tool_signatures_in_version():
    item = {
        "name": "test-server",
        "versions": [
            {
                "version": "1.0.0",
                "tool_signatures": [
                    {
                        "name": "tool1",
                        "parameters": [
                            {"name": "param1", "type": "string"}
                        ]
                    }
                ]
            }
        ]
    }
    result = normalize_server_item(item)
    assert result["latest_version"] == "1.0.0"
    assert result["tool_count"] == 1
    assert result["tools"][0]["name"] == "tool1"
    assert result["tools"][0]["parameters"][0]["name"] == "param1"

def test_normalize_server_item_fallback_to_tools():
    item = {
        "name": "test-server",
        "version": "2.0.0",
        "tools": [
            {"name": "tool_a"},
            {"name": "tool_b"}
        ]
    }
    result = normalize_server_item(item)
    assert result["latest_version"] == "2.0.0"
    assert result["tool_count"] == 2
    assert result["tools"][0]["name"] == "tool_a"

def test_normalize_server_item_with_empty_tools():
    item = {
        "name": "empty-server",
        "version": "1.0.0",
    }
    result = normalize_server_item(item)
    assert result["tool_count"] == 0
    assert result["tools"] == []

def test_normalize_server_item_tool_signatures_override_tools():
    item = {
        "name": "override-server",
        "tool_signatures": [{"name": "sig1"}],
        "tools": [{"name": "tool1"}, {"name": "tool2"}]
    }
    result = normalize_server_item(item)
    assert result["tool_count"] == 1
    assert result["tools"][0]["name"] == "sig1"

