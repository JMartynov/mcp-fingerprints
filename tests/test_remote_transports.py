from mcp_fingerprints.config_exporter import export_client_config
from mcp_fingerprints.validator import McpServerValidator


def test_validator_sse_transport_https():
    is_valid, _ = McpServerValidator.is_valid_mcp_server(
        package_name="test-server",
        ecosystem="generic",
        has_tools_declared=True,
        transport="sse",
        remote_endpoint="https://api.example.com/sse",
    )
    assert is_valid


def test_validator_sse_transport_http_localhost():
    is_valid, _ = McpServerValidator.is_valid_mcp_server(
        package_name="test-server",
        ecosystem="generic",
        has_tools_declared=True,
        transport="sse",
        remote_endpoint="http://localhost:8000/sse",
    )
    assert is_valid


def test_validator_sse_transport_http_rejected():
    is_valid, reason = McpServerValidator.is_valid_mcp_server(
        package_name="test-server",
        ecosystem="generic",
        has_tools_declared=True,
        transport="sse",
        remote_endpoint="http://api.example.com/sse",
    )
    assert not is_valid
    assert "must be https" in reason


def test_validator_websocket_transport_wss():
    is_valid, _ = McpServerValidator.is_valid_mcp_server(
        package_name="test-server",
        ecosystem="generic",
        has_tools_declared=True,
        transport="websocket",
        remote_endpoint="wss://api.example.com/ws",
    )
    assert is_valid


def test_validator_websocket_transport_ws_rejected():
    is_valid, reason = McpServerValidator.is_valid_mcp_server(
        package_name="test-server",
        ecosystem="generic",
        has_tools_declared=True,
        transport="websocket",
        remote_endpoint="ws://api.example.com/ws",
    )
    assert not is_valid
    assert "must be wss" in reason


def test_config_exporter_sse_with_headers():
    passport = {
        "package_name": "remote-sse",
        "ecosystem": "generic",
        "remote_endpoint": "https://mcp.io/sse",
        "headers_schema": {"Authorization": "Bearer token123"},
        "versions": [{"connections": [{"type": "sse", "url": "https://mcp.io/sse"}]}],
    }

    # Claude
    claude_cfg = export_client_config(passport, client="claude")
    assert (
        claude_cfg["mcpServers"]["remote-sse"]["headers"]["Authorization"]
        == "Bearer token123"
    )

    # Cursor
    cursor_cfg = export_client_config(passport, client="cursor")
    assert (
        cursor_cfg["mcpServers"]["remote-sse"]["headers"]["Authorization"]
        == "Bearer token123"
    )

    # Cline
    cline_cfg = export_client_config(passport, client="cline")
    assert (
        cline_cfg["mcpServers"]["remote-sse"]["headers"]["Authorization"]
        == "Bearer token123"
    )

    # Zed
    zed_cfg = export_client_config(passport, client="zed")
    assert (
        zed_cfg["context_servers"]["remote-sse"]["headers"]["Authorization"]
        == "Bearer token123"
    )
