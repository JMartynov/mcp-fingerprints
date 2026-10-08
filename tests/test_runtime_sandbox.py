import os
import sys
from mcp_fingerprints.runtime_sandbox import probe_mcp_server_stdio, sanitize_environment

def test_sanitize_environment():
    # Set up some dummy environment variables
    os.environ["AWS_ACCESS_KEY_ID"] = "secret"
    os.environ["GITHUB_TOKEN"] = "token"
    os.environ["OPENAI_API_KEY"] = "openai_key"
    os.environ["ANTHROPIC_API_KEY"] = "anthropic_key"
    os.environ["SSH_AUTH_SOCK"] = "/tmp/ssh"
    os.environ["SAFE_VAR"] = "safe"

    safe_env = sanitize_environment({"EXTRA_SAFE": "extra", "AWS_REGION": "us-east-1"})
    
    assert "SAFE_VAR" in safe_env
    assert safe_env["SAFE_VAR"] == "safe"
    assert "EXTRA_SAFE" in safe_env
    assert safe_env["EXTRA_SAFE"] == "extra"
    assert "PATH" in safe_env
    
    # Check that dangerous variables are stripped
    assert "AWS_ACCESS_KEY_ID" not in safe_env
    assert "GITHUB_TOKEN" not in safe_env
    assert "OPENAI_API_KEY" not in safe_env
    assert "ANTHROPIC_API_KEY" not in safe_env
    assert "SSH_AUTH_SOCK" not in safe_env
    assert "AWS_REGION" not in safe_env
    
    # Cleanup
    del os.environ["AWS_ACCESS_KEY_ID"]
    del os.environ["GITHUB_TOKEN"]
    del os.environ["OPENAI_API_KEY"]
    del os.environ["ANTHROPIC_API_KEY"]
    del os.environ["SSH_AUTH_SOCK"]
    del os.environ["SAFE_VAR"]

def test_successful_handshake():
    # A simple mock MCP server
    mock_script = """
import sys
import json

def read_message():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)

def write_message(msg):
    sys.stdout.write(json.dumps(msg) + '\\n')
    sys.stdout.flush()

# Read initialize
msg1 = read_message()
assert msg1["method"] == "initialize"
write_message({"jsonrpc": "2.0", "id": msg1["id"], "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "MockServer", "version": "1.0"}}})

# Read notifications/initialized
msg2 = read_message()
assert msg2["method"] == "notifications/initialized"

# Read tools/list
msg3 = read_message()
assert msg3["method"] == "tools/list"
write_message({
    "jsonrpc": "2.0", 
    "id": msg3["id"], 
    "result": {
        "tools": [
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
    }
})
"""
    tools = probe_mcp_server_stdio([sys.executable, "-c", mock_script])
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert tools[0]["description"] == "A test tool"
    assert tools[0]["inputSchema"] == {"type": "object", "properties": {}}

def test_timeout_handling():
    mock_script = """
import time
time.sleep(10)
"""
    # Use a short timeout
    tools = probe_mcp_server_stdio([sys.executable, "-c", mock_script], timeout_seconds=0.5)
    assert tools == []

def test_malformed_json():
    mock_script = """
import sys
import json

line = sys.stdin.readline()
sys.stdout.write("Not a json string\\n")
sys.stdout.flush()
"""
    # Process might exit or hang depending on reading, but our code should just handle non-json and timeout or exit
    tools = probe_mcp_server_stdio([sys.executable, "-c", mock_script], timeout_seconds=0.5)
    assert tools == []

def test_missing_binary():
    tools = probe_mcp_server_stdio(["/path/to/nonexistent/binary"])
    assert tools == []
