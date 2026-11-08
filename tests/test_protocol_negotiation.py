import pytest
from mcp_fingerprints.protocol_validator import (
    SUPPORTED_PROTOCOL_VERSIONS,
    LATEST_PROTOCOL_VERSION,
    LEGACY_PROTOCOL_VERSION,
    build_discover_request,
    build_initialize_request,
    is_discover_unsupported_error,
    validate_mcp_handshake,
    ProtocolViolationError,
)
from mcp_fingerprints.prober import McpStdioProber, McpHttpProber
from mcp_fingerprints.detector import detect_mcp_stdio, detect_mcp_http
from mcp_fingerprints.runtime_sandbox import probe_mcp_server_stdio
from mcp_fingerprints.cli import main as cli_main
from unittest.mock import patch, MagicMock
import sys
import json
import subprocess
import io
import urllib.request


def test_constants():
    assert LATEST_PROTOCOL_VERSION == "2026-07-28"
    assert LEGACY_PROTOCOL_VERSION == "2024-11-05"
    assert "2026-07-28" in SUPPORTED_PROTOCOL_VERSIONS


def test_build_requests():
    disc = build_discover_request(req_id=10, client_name="test")
    assert disc["method"] == "server/discover"
    assert disc["id"] == 10
    assert disc["params"]["protocolVersion"] == LATEST_PROTOCOL_VERSION

    init = build_initialize_request(req_id=20, protocol_version="123", client_name="test")
    assert init["method"] == "initialize"
    assert init["id"] == 20
    assert init["params"]["protocolVersion"] == "123"


def test_is_discover_unsupported_error():
    assert is_discover_unsupported_error({"error": {"code": -32601}}) is True
    assert is_discover_unsupported_error({"error": {"code": -32602}}) is True
    assert is_discover_unsupported_error({"error": {"code": 123}}) is False
    assert is_discover_unsupported_error({}) is False


def test_validate_mcp_handshake_discover():
    req = build_discover_request()
    resp = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": LATEST_PROTOCOL_VERSION,
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"},
        },
    }
    validate_mcp_handshake([req, resp])

    # Error case
    with pytest.raises(ProtocolViolationError):
        validate_mcp_handshake([req])


def test_validate_mcp_handshake_initialize():
    req = build_initialize_request()
    resp = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "protocolVersion": LEGACY_PROTOCOL_VERSION,
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"},
        },
    }
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    validate_mcp_handshake([req, resp, notif])


MOCK_SERVER_DISCOVER = """
import sys, json

def read_msg():
    line = sys.stdin.readline()
    if not line: return None
    return json.loads(line)

def write_msg(msg):
    sys.stdout.write(json.dumps(msg) + "\\n")
    sys.stdout.flush()

msg1 = read_msg()
write_msg({
    "jsonrpc": "2.0", 
    "id": msg1["id"], 
    "result": {
        "protocolVersion": "2026-07-28", 
        "capabilities": {}, 
        "serverInfo": {"name": "Mock", "version": "1"}
    }
})

while True:
    msg = read_msg()
    if not msg: break
    if msg.get("method") == "tools/list":
        write_msg({"jsonrpc": "2.0", "id": msg["id"], "result": {"tools": []}})
    elif msg.get("method") in ("prompts/list", "resources/list"):
        write_msg({"jsonrpc": "2.0", "id": msg["id"], "result": {}})
    elif msg.get("method") == "notifications/initialized":
        continue
    else:
        write_msg({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "Method not found"}})
"""

def test_detect_mcp_stdio_discover():
    res = detect_mcp_stdio([sys.executable, "-c", MOCK_SERVER_DISCOVER], timeout=1.0)
    assert res["is_mcp"] is True
    assert res["protocol_version"] == "2026-07-28"

def test_prober_stdio_discover():
    prober = McpStdioProber()
    report = prober.probe([sys.executable, "-c", MOCK_SERVER_DISCOVER], timeout=2.0)
    assert report.connection_successful is True
    assert report.protocol_version == "2026-07-28"

def test_sandbox_stdio_discover():
    tools = probe_mcp_server_stdio([sys.executable, "-c", MOCK_SERVER_DISCOVER], timeout_seconds=2.0)
    assert tools == [] # Empty tools list, but it connected!

def test_detect_mcp_http_discover():
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2026-07-28",
            "capabilities": {},
            "serverInfo": {"name": "Mock", "version": "1"}
        }
    }).encode("utf-8")
    mock_response.headers = MagicMock()
    mock_response.headers.get.return_value = "application/json"
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_ctx
        
        res = detect_mcp_http("http://example.com/mcp", timeout=1.0)
        assert res["is_mcp"] is True
        assert res["protocol_version"] == "2026-07-28"

def test_prober_http_discover():
    mock_handshake = MagicMock()
    mock_handshake.read.return_value = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2026-07-28",
            "capabilities": {},
            "serverInfo": {"name": "Mock", "version": "1"}
        }
    }).encode("utf-8")
    mock_handshake_ctx = MagicMock()
    mock_handshake_ctx.__enter__.return_value = mock_handshake
    
    mock_tools = MagicMock()
    mock_tools.read.return_value = json.dumps({"jsonrpc": "2.0", "id": 3, "result": {"tools": []}}).encode("utf-8")
    mock_tools_ctx = MagicMock()
    mock_tools_ctx.__enter__.return_value = mock_tools
    
    mock_prompts = MagicMock()
    mock_prompts.read.return_value = json.dumps({"jsonrpc": "2.0", "id": 4, "result": {"prompts": []}}).encode("utf-8")
    mock_prompts_ctx = MagicMock()
    mock_prompts_ctx.__enter__.return_value = mock_prompts
    
    mock_resources = MagicMock()
    mock_resources.read.return_value = json.dumps({"jsonrpc": "2.0", "id": 5, "result": {"resources": []}}).encode("utf-8")
    mock_resources_ctx = MagicMock()
    mock_resources_ctx.__enter__.return_value = mock_resources
    
    with patch("urllib.request.urlopen", side_effect=[mock_handshake_ctx, mock_tools_ctx, mock_prompts_ctx, mock_resources_ctx]):
        prober = McpHttpProber()
        report = prober.probe("http://example.com/mcp", timeout=1.0)
        assert report.connection_successful is True
        assert report.protocol_version == "2026-07-28"

def test_cli_validate_protocol(capsys):
    with patch("sys.argv", ["mcp-fingerprints", "validate-protocol", "--", sys.executable, "-c", MOCK_SERVER_DISCOVER]):
        try:
            cli_main()
        except SystemExit as e:
            assert e.code == 0
        captured = capsys.readouterr()
        assert "PASS: Valid sequence" in captured.out
