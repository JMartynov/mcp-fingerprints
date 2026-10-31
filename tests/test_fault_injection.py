import json
import subprocess
import urllib.error
import time
from unittest.mock import MagicMock, patch

import pytest
from mcp_fingerprints.prober import McpStdioProber, McpHttpProber
from mcp_fingerprints.runtime_sandbox import probe_mcp_server_stdio


def test_stdio_prober_malformed_json_rpc():
    """Test stdio prober handling of malformed JSON-RPC payloads interspersed with valid ones."""
    prober = McpStdioProber()
    mock_process = MagicMock()
    mock_process.stdout = MagicMock()
    
    # We will simulate readline returning:
    # 1. Plaintext log line
    # 2. Malformed JSON
    # 3. Valid JSON response
    valid_resp = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}).encode('utf-8') + b'\n'
    
    responses = [
        b"INFO: Server starting...\n",
        b"{malformed json\n",
        valid_resp
    ]
    
    def side_effect(*args, **kwargs):
        if responses:
            return responses.pop(0)
        return b""
        
    mock_process.stdout.readline.side_effect = side_effect
    mock_process.poll.return_value = None
    
    result = prober._read_jsonrpc_response(mock_process, timeout=1.0)
    assert result is not None
    assert result.get("id") == 1


def test_stdio_prober_buffer_cap_limit():
    """Test stdio prober enforcing the 10MB read buffer cap."""
    prober = McpStdioProber()
    mock_process = MagicMock()
    mock_process.stdout = MagicMock()
    
    # Simulate a single massive line over 10MB
    massive_line = b"a" * (10 * 1024 * 1024 + 1)
    mock_process.stdout.readline.return_value = massive_line
    mock_process.poll.return_value = None
    
    result = prober._read_jsonrpc_response(mock_process, timeout=1.0)
    assert result is None
    # Process should be killed due to buffer limit
    mock_process.kill.assert_called_once()


def test_runtime_sandbox_timeout():
    """Test runtime_sandbox gracefully handling subprocess timeouts."""
    # We use a mock to simulate a process that hangs and doesn't return anything
    with patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        # stdin and stdout pipes
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        
        # Hang on readline
        def hang_readline(*args, **kwargs):
            time.sleep(0.2)
            return b""
            
        mock_process.stdout.readline.side_effect = hang_readline
        mock_process.poll.return_value = None
        
        start_time = time.time()
        tools = probe_mcp_server_stdio(["dummy"], timeout_seconds=0.1)
        
        assert tools == []
        # ensure it terminated
        mock_process.terminate.assert_called()


@patch('urllib.request.urlopen')
def test_http_prober_mid_stream_network_drop(mock_urlopen):
    """Test HTTP prober handling a mid-stream network drop (e.g. read fails halfway)."""
    prober = McpHttpProber()
    
    # Simulate first POST succeeding (initialize), but second failing
    mock_response_1 = MagicMock()
    mock_response_1.read.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}).encode('utf-8')
    mock_response_1.__enter__.return_value = mock_response_1
    
    mock_response_2 = MagicMock()
    mock_response_2.read.side_effect = Exception("Mid-stream network drop!")
    mock_response_2.__enter__.return_value = mock_response_2
    
    mock_urlopen.side_effect = [
        # This one is for the initial SSE check (will fail or fall through to POST)
        urllib.error.URLError("No SSE"),
        mock_response_1, # initialize
        mock_response_2, # initialized notification / tools list
        mock_response_2, 
        mock_response_2,
        mock_response_2
    ]
    
    report = prober.probe("http://localhost:8080/mcp", timeout=0.1)
    
    # It should fail gracefully or just return what it got (probably fail during tools/list)
    # The HTTP prober catches exceptions and returns ProbeReport with connection_successful=False or missing tools
    assert report is not None
    # Because tools list fails, tools_observed will be empty if not erroring outright.
    # The current prober.py handles exceptions during POST and sets connection_successful=False if initialize fails, 
    # but tools_list failing will just result in empty tools list because send_post catches Exception and returns None.
    assert len(report.tools_observed) == 0

