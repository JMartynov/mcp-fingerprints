import json
import pytest
from pathlib import Path
from mcp_fingerprints.config_scanner import ClientConfigLocator, ConfigScanner, LocalInventoryReport

@pytest.fixture
def mock_configs_dir(tmp_path):
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    
    # Claude config
    claude_config = configs_dir / "claude_desktop_config.json"
    claude_config.write_text(json.dumps({
        "mcpServers": {
            "test-server": {
                "command": "node",
                "args": ["server.js"],
                "env": {"API_KEY": "test"}
            }
        }
    }))
    
    # Cursor config
    cursor_dir = tmp_path / ".cursor"
    cursor_dir.mkdir()
    cursor_config = cursor_dir / "mcp.json"
    cursor_config.write_text(json.dumps({
        "mcpServers": {
            "cursor-server": {
                "command": "python",
                "args": ["-m", "test"],
                "env": {}
            }
        }
    }))
    
    # JSONC with comments
    jsonc_config = configs_dir / "with_comments.json"
    jsonc_config.write_text("""{
        // This is a comment
        "mcpServers": {
            // Another comment
            "jsonc-server": {
                "command": "echo",
                "args": ["hello"]
            }
        }
    }""")
    
    return {
        "claude": claude_config,
        "cursor": cursor_config,
        "jsonc": jsonc_config,
        "cursor_dir": tmp_path
    }

def test_extract_servers_from_config(mock_configs_dir):
    scanner = ConfigScanner()
    report = scanner.scan_file(mock_configs_dir["claude"], probe_live=False)
    
    assert len(report.servers) == 1
    server = report.servers[0]
    assert server["name"] == "test-server"
    assert server["command"] == "node"
    assert server["args"] == ["server.js"]
    assert server["env"] == {"API_KEY": "test"}

def test_jsonc_parsing(mock_configs_dir):
    scanner = ConfigScanner()
    report = scanner.scan_file(mock_configs_dir["jsonc"], probe_live=False)
    
    assert len(report.servers) == 1
    server = report.servers[0]
    assert server["name"] == "jsonc-server"
    assert server["command"] == "echo"
    assert server["args"] == ["hello"]

def test_scan_multiple_paths(mock_configs_dir):
    scanner = ConfigScanner()
    paths = [mock_configs_dir["claude"], mock_configs_dir["cursor"]]
    report = scanner.scan(paths=paths, probe_live=False)
    
    assert len(report.servers) == 2
    names = [s["name"] for s in report.servers]
    assert "test-server" in names
    assert "cursor-server" in names

def test_scan_directory(mock_configs_dir):
    scanner = ConfigScanner()
    paths = [mock_configs_dir["cursor_dir"]]
    report = scanner.scan(paths=paths, probe_live=False)
    
    assert len(report.servers) == 1
    assert report.servers[0]["name"] == "cursor-server"

def test_standard_paths():
    paths = ClientConfigLocator.get_standard_paths()
    assert isinstance(paths, list)
    # We can't assert the content size since it depends on the testing environment, 
    # but we can check if the types are Path objects.
    for p in paths:
        assert isinstance(p, Path)

