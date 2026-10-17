import json
import pytest
from mcp_fingerprints.config_scanner import ConfigScanner

@pytest.fixture
def mock_configs_dir_http(tmp_path):
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    
    http_config = configs_dir / "http_config.json"
    http_config.write_text(json.dumps({
        "mcpServers": {
            "test-http-server": {
                "url": "http://localhost:8000/sse",
                "headers": {"Authorization": "Bearer token"}
            }
        }
    }))
    
    return {"http": http_config}

def test_extract_http_servers_from_config(mock_configs_dir_http):
    scanner = ConfigScanner()
    report = scanner.scan_file(mock_configs_dir_http["http"], probe_live=False)
    
    assert len(report.servers) == 1
    server = report.servers[0]
    assert server["name"] == "test-http-server"
    assert server["url"] == "http://localhost:8000/sse"
    assert server["headers"] == {"Authorization": "Bearer token"}
