import os
import sys
import time
import json
import pytest
import subprocess
from unittest import mock

from mcp_fingerprints.runtime_sandbox import probe_mcp_server_stdio, sanitize_environment
from mcp_fingerprints.protocol_validator import (
    validate_jsonrpc_message,
    validate_mcp_handshake,
    ProtocolViolationError
)

def test_subprocess_execution_timeout():
    """
    Test that a hung stdio process is terminated within the specified timeout.
    """
    start_time = time.time()
    # Python script that sleeps for 30 seconds
    cmd = [sys.executable, "-c", "import time; time.sleep(30)"]
    
    # Run with a short timeout
    result = probe_mcp_server_stdio(cmd, timeout_seconds=1.0)
    
    elapsed = time.time() - start_time
    assert result == [], "Expected empty tools result from hung process"
    assert elapsed < 5.0, f"Process took {elapsed} seconds, expected less than 5.0s"

def test_credential_sanitization():
    """
    Test that dangerous environment variables are stripped.
    """
    dirty_env = {
        "AWS_SECRET_ACCESS_KEY": "supersecret",
        "OPENAI_API_KEY": "sk-1234",
        "GITHUB_TOKEN": "ghp_5678",
        "ANTHROPIC_API_KEY": "sk-ant-9012",
        "SSH_AUTH_SOCK": "/tmp/ssh-sock",
        "SAFE_VAR": "safe_value",
        "PATH": "/usr/bin"
    }
    
    with mock.patch.dict(os.environ, dirty_env, clear=True):
        clean_env = sanitize_environment()
        
        assert "SAFE_VAR" in clean_env
        assert clean_env["SAFE_VAR"] == "safe_value"
        assert "PATH" in clean_env
        
        assert "AWS_SECRET_ACCESS_KEY" not in clean_env
        assert "OPENAI_API_KEY" not in clean_env
        assert "GITHUB_TOKEN" not in clean_env
        assert "ANTHROPIC_API_KEY" not in clean_env
        assert "SSH_AUTH_SOCK" not in clean_env

def test_credential_sanitization_child_process():
    """
    Test that child process actually doesn't receive the dangerous variables.
    """
    env = {
        "AWS_SECRET_ACCESS_KEY": "supersecret",
        "OPENAI_API_KEY": "sk-1234",
        "SAFE_VAR": "safe_value"
    }
    
    script = "import os, json; print(json.dumps(dict(os.environ)))"
    clean_env = sanitize_environment(env)
    
    proc = subprocess.run([sys.executable, "-c", script], env=clean_env, capture_output=True, text=True)
    child_env = json.loads(proc.stdout)
    
    assert "AWS_SECRET_ACCESS_KEY" not in child_env
    assert "OPENAI_API_KEY" not in child_env
    assert child_env.get("SAFE_VAR") == "safe_value"

def test_jsonrpc_conformance_valid():
    msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    validate_jsonrpc_message(msg, request_id=1)
    
    msg_no_id = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    validate_jsonrpc_message(msg_no_id)

def test_jsonrpc_conformance_invalid_version():
    with pytest.raises(ProtocolViolationError, match="Invalid 'jsonrpc' version"):
        validate_jsonrpc_message({"jsonrpc": "1.0"})
        
    with pytest.raises(ProtocolViolationError, match="Missing 'jsonrpc' field"):
        validate_jsonrpc_message({"id": 1})

def test_jsonrpc_conformance_id_reflection():
    msg = {"jsonrpc": "2.0", "id": 2, "result": {}}
    with pytest.raises(ProtocolViolationError, match="ID reflection failed"):
        validate_jsonrpc_message(msg, request_id=1)

def test_jsonrpc_conformance_error_schema():
    # Valid error
    msg = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32600, "message": "Invalid request"}}
    validate_jsonrpc_message(msg, request_id=1)
    
    # Invalid error (not object)
    bad_msg = {"jsonrpc": "2.0", "id": 1, "error": "Something went wrong"}
    with pytest.raises(ProtocolViolationError, match="Error field must be an object"):
        validate_jsonrpc_message(bad_msg, request_id=1)
        
    # Invalid error (missing code)
    bad_msg2 = {"jsonrpc": "2.0", "id": 1, "error": {"message": "Invalid request"}}
    with pytest.raises(ProtocolViolationError, match="must contain an integer 'code'"):
        validate_jsonrpc_message(bad_msg2, request_id=1)

def test_mcp_handshake_valid():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    resp = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "server", "version": "1.0"}
        }
    }
    notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    
    validate_mcp_handshake([req, resp, notif])

def test_mcp_handshake_invalid():
    # Not enough messages
    with pytest.raises(ProtocolViolationError, match="requires at least 3 messages"):
        validate_mcp_handshake([])

    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    resp = {
        "jsonrpc": "2.0",
        "id": 2, # wrong id
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "server", "version": "1.0"}
        }
    }
    notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    
    with pytest.raises(ProtocolViolationError, match="ID reflection failed"):
        validate_mcp_handshake([req, resp, notif])


def test_cli_error_handling_exit_codes():
    """
    Test CLI validate-protocol with valid and invalid scripts.
    """
    valid_server_script = '''import sys, json, time
for line in sys.stdin:
    try:
        req = json.loads(line)
        if req.get("method") == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req["id"],
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {"name": "valid", "version": "1.0"}
                }
            }
            print(json.dumps(resp), flush=True)
        elif req.get("method") == "notifications/initialized":
            pass # No response needed
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req.get("id"),
                "error": {"code": -32601, "message": "Method not found"}
            }
            print(json.dumps(resp), flush=True)
    except:
        pass
'''

    invalid_server_script = '''import sys, json
for line in sys.stdin:
    print(json.dumps({"wrong": "format"}), flush=True)
'''

    with open("valid_server.py", "w") as f:
        f.write(valid_server_script)
        
    with open("invalid_server.py", "w") as f:
        f.write(invalid_server_script)
        
    try:
        # 1. Valid server
        proc = subprocess.run([
            sys.executable, "-m", "mcp_fingerprints.cli", "validate-protocol",
            sys.executable, "valid_server.py"
        ], capture_output=True, text=True)
        assert proc.returncode == 0, f"Expected valid server to return 0, got {proc.returncode}. Out: {proc.stdout} Err: {proc.stderr}"
        assert "Protocol Conformance: PASS" in proc.stdout
        
        # 2. Invalid server
        proc_invalid = subprocess.run([
            sys.executable, "-m", "mcp_fingerprints.cli", "validate-protocol",
            sys.executable, "invalid_server.py"
        ], capture_output=True, text=True)
        assert proc_invalid.returncode == 1, "Expected invalid server to return exit code 1"
        assert "FAIL" in proc_invalid.stdout or "FAIL" in proc_invalid.stderr
        
        # 3. Missing parameters
        proc_missing = subprocess.run([
            sys.executable, "-m", "mcp_fingerprints.cli", "validate-protocol"
        ], capture_output=True, text=True)
        assert proc_missing.returncode != 0
        
    finally:
        if os.path.exists("valid_server.py"):
            os.remove("valid_server.py")
        if os.path.exists("invalid_server.py"):
            os.remove("invalid_server.py")
