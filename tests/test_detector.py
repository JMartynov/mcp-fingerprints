import json
import pytest
from unittest.mock import patch, MagicMock

from mcp_fingerprints.detector import detect_mcp_stdio, detect_mcp_http, detect_mcp

@patch("subprocess.Popen")
def test_detect_mcp_stdio_success(mock_popen):
    mock_process = MagicMock()
    mock_process.stdout = [
        json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-server", "version": "1.0"}
            }
        }) + "\n"
    ]
    mock_popen.return_value = mock_process
    
    result = detect_mcp_stdio(["dummy"])
    
    assert result["is_mcp"] is True
    assert result["transport"] == "stdio"
    assert result["server_info"]["name"] == "test-server"
    assert "tools" in result["capabilities"]

@patch("urllib.request.urlopen")
def test_detect_mcp_http_success(mock_urlopen):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.read.return_value = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"prompts": {}},
            "serverInfo": {"name": "test-http-server", "version": "2.0"}
        }
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    result = detect_mcp_http("http://localhost:8000")
    
    assert result["is_mcp"] is True
    assert result["transport"] == "http"
    assert result["server_info"]["name"] == "test-http-server"
    assert "prompts" in result["capabilities"]

@patch("subprocess.Popen")
def test_detect_mcp_wrapper(mock_popen):
    mock_process = MagicMock()
    mock_process.stdout = [
        json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "wrapper-server", "version": "1.0"}
            }
        }) + "\n"
    ]
    mock_popen.return_value = mock_process

    result = detect_mcp(["dummy"])
    assert result["is_mcp"] is True

