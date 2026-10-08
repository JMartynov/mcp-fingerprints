import pytest
from mcp_fingerprints.config_exporter import export_client_config

def test_export_claude_stdio():
    passport = {
        "package_name": "@namespace/test-pkg",
        "ecosystem": "npm",
        "versions": [
            {
                "connections": [
                    {
                        "type": "stdio",
                        "command": "node",
                        "args": ["dist/index.js"],
                        "env": {"API_KEY": "test"}
                    }
                ]
            }
        ]
    }
    
    config = export_client_config(passport, client="claude")
    assert "mcpServers" in config
    assert "namespace-test-pkg" in config["mcpServers"]
    
    server_conf = config["mcpServers"]["namespace-test-pkg"]
    assert server_conf["command"] == "node"
    assert server_conf["args"] == ["dist/index.js"]
    assert server_conf["env"] == {"API_KEY": "test"}

def test_export_cursor_sse():
    passport = {
        "package_name": "remote-pkg",
        "ecosystem": "generic",
        "versions": [
            {
                "connections": [
                    {
                        "type": "sse",
                        "url": "https://example.com/sse"
                    }
                ]
            }
        ]
    }
    
    config = export_client_config(passport, client="cursor")
    assert "mcpServers" in config
    assert "remote-pkg" in config["mcpServers"]
    
    server_conf = config["mcpServers"]["remote-pkg"]
    assert server_conf["type"] == "sse"
    assert server_conf["url"] == "https://example.com/sse"

def test_export_npm_fallback():
    passport = {
        "package_name": "simple-npm-pkg",
        "ecosystem": "npm",
        "versions": [
            {
                "connections": [
                    {
                        "type": "stdio"
                    }
                ]
            }
        ]
    }
    
    config = export_client_config(passport)
    server_conf = config["mcpServers"]["simple-npm-pkg"]
    assert server_conf["command"] == "npx"
    assert server_conf["args"] == ["-y", "simple-npm-pkg"]

def test_export_pypi_fallback():
    passport = {
        "package_name": "simple-pypi-pkg",
        "ecosystem": "pypi",
        "versions": [
            {
                "connections": [
                    {
                        "type": "stdio"
                    }
                ]
            }
        ]
    }
    
    config = export_client_config(passport)
    server_conf = config["mcpServers"]["simple-pypi-pkg"]
    assert server_conf["command"] == "uvx"
    assert server_conf["args"] == ["simple-pypi-pkg"]

def test_export_invalid_client():
    with pytest.raises(ValueError, match="Unsupported client"):
        export_client_config({"package_name": "x", "versions": [{"connections": [{"type": "stdio"}]}]}, client="unknown")
        
def test_export_no_versions():
    with pytest.raises(ValueError, match="Passport has no versions"):
        export_client_config({"package_name": "x", "versions": []})
