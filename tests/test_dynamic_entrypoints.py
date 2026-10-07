import json
import urllib.request
from unittest import mock
import pytest

from mcp_fingerprints.synchronizer import PassportSynchronizer
from mcp_fingerprints.models import ServerPackageSpec

# A mock tool returned by the parser
MOCK_TOOL = [{"name": "test_tool", "description": "a tool"}]

def setup_mock_urlopen(mock_urlopen, responses: dict):
    """
    responses is a dictionary mapping URL strings to dictionaries with keys:
    - status: int (HTTP status code)
    - body: str (response body)
    """
    def side_effect(req, *args, **kwargs):
        url = req.full_url
        if url in responses:
            resp_data = responses[url]
            mock_resp = mock.MagicMock()
            mock_resp.status = resp_data.get("status", 200)
            mock_resp.read.return_value = resp_data.get("body", "").encode("utf-8")
            
            # Context manager support
            mock_resp.__enter__.return_value = mock_resp
            mock_resp.__exit__.return_value = False
            return mock_resp
        
        # If url not mocked, return 404
        mock_resp = mock.MagicMock()
        mock_resp.status = 404
        mock_resp.read.return_value = b""
        
        # Context manager support
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        return mock_resp
        
    mock_urlopen.side_effect = side_effect


@mock.patch("mcp_fingerprints.synchronizer.urllib.request.urlopen")
@mock.patch("mcp_fingerprints.synchronizer.parse_mcp_source_code")
def test_dynamic_entrypoint_dist_index(mock_parse, mock_urlopen, tmp_path):
    """Test mapping dist/index.js -> src/index.ts from package.json"""
    mock_parse.return_value = MOCK_TOOL
    
    responses = {
        "https://raw.githubusercontent.com/testowner/testrepo/main/package.json": {
            "status": 200,
            "body": json.dumps({"main": "dist/index.js"}),
        },
        "https://raw.githubusercontent.com/testowner/testrepo/main/src/index.ts": {
            "status": 200,
            "body": "mock ts source code",
        },
    }
    setup_mock_urlopen(mock_urlopen, responses)
    
    syncer = PassportSynchronizer(output_dir=str(tmp_path))
    tools = syncer._extract_ast_tools_from_github("testowner/testrepo")
    
    assert tools == MOCK_TOOL
    # Verify parse was called with the right source code
    mock_parse.assert_called_once_with("mock ts source code", language="ts")
    
    # Verify early exit: urlopen should be called exactly twice:
    # 1. package.json
    # 2. src/index.ts
    assert mock_urlopen.call_count == 2
    
    call_args_list = mock_urlopen.call_args_list
    url_1 = call_args_list[0][0][0].full_url
    url_2 = call_args_list[1][0][0].full_url
    assert url_1 == "https://raw.githubusercontent.com/testowner/testrepo/main/package.json"
    assert url_2 == "https://raw.githubusercontent.com/testowner/testrepo/main/src/index.ts"


@mock.patch("mcp_fingerprints.synchronizer.urllib.request.urlopen")
@mock.patch("mcp_fingerprints.synchronizer.parse_mcp_source_code")
def test_dynamic_entrypoint_bin_cli(mock_parse, mock_urlopen, tmp_path):
    """Test mapping binary field 'bin': {'cli': 'dist/cli.js'} -> src/cli.ts"""
    mock_parse.return_value = MOCK_TOOL
    
    responses = {
        "https://raw.githubusercontent.com/testowner/testrepo/main/package.json": {
            "status": 200,
            "body": json.dumps({"bin": {"cli": "dist/cli.js"}}),
        },
        # Assuming src/cli.ts is not found
        "https://raw.githubusercontent.com/testowner/testrepo/main/src/cli.ts": {
            "status": 404,
            "body": "",
        },
        # Try src/cli.js
        "https://raw.githubusercontent.com/testowner/testrepo/main/src/cli.js": {
            "status": 200,
            "body": "mock js source code",
        },
    }
    setup_mock_urlopen(mock_urlopen, responses)
    
    syncer = PassportSynchronizer(output_dir=str(tmp_path))
    tools = syncer._extract_ast_tools_from_github("testowner/testrepo")
    
    assert tools == MOCK_TOOL
    # Verify parse was called with the right source code
    mock_parse.assert_called_once_with("mock js source code", language="js")


@mock.patch("mcp_fingerprints.synchronizer.urllib.request.urlopen")
@mock.patch("mcp_fingerprints.synchronizer.parse_mcp_source_code")
def test_modular_subpath_fallback(mock_parse, mock_urlopen, tmp_path):
    """Test discovering tools in modular subpath src/tools/index.ts when earlier candidates 404"""
    # Parse returns empty first time (if another file is found but has no tools),
    # but we'll mock that earlier files just 404, so parse is only called once.
    mock_parse.return_value = MOCK_TOOL
    
    # We will just 404 the package.json and all earlier static candidates.
    responses = {
        "https://raw.githubusercontent.com/testowner/testrepo/main/src/tools/index.ts": {
            "status": 200,
            "body": "mock tools index code",
        },
    }
    setup_mock_urlopen(mock_urlopen, responses)
    
    syncer = PassportSynchronizer(output_dir=str(tmp_path))
    tools = syncer._extract_ast_tools_from_github("testowner/testrepo")
    
    assert tools == MOCK_TOOL
    mock_parse.assert_called_once_with("mock tools index code", language="ts")
    
    # Find all attempted URLs
    urls_tried = [call[0][0].full_url for call in mock_urlopen.call_args_list]
    assert "https://raw.githubusercontent.com/testowner/testrepo/main/src/tools/index.ts" in urls_tried
    
    # Should not have attempted files that come AFTER src/tools/index.ts in the candidate list
    assert "https://raw.githubusercontent.com/testowner/testrepo/main/src/handlers/index.ts" not in urls_tried


@mock.patch("mcp_fingerprints.synchronizer.urllib.request.urlopen")
@mock.patch("mcp_fingerprints.synchronizer.parse_mcp_source_code")
def test_early_exit_optimization(mock_parse, mock_urlopen, tmp_path):
    """Test early-exit optimization: verify no further requests are made after tools are found."""
    mock_parse.return_value = MOCK_TOOL
    
    responses = {
        # package.json not found
        "https://raw.githubusercontent.com/testowner/testrepo/main/package.json": {
            "status": 404,
            "body": "",
        },
        # first fallback is src/tools.ts
        "https://raw.githubusercontent.com/testowner/testrepo/main/src/tools.ts": {
            "status": 200,
            "body": "found it early",
        },
    }
    setup_mock_urlopen(mock_urlopen, responses)
    
    syncer = PassportSynchronizer(output_dir=str(tmp_path))
    tools = syncer._extract_ast_tools_from_github("testowner/testrepo")
    
    assert tools == MOCK_TOOL
    
    # Total calls:
    # 1. package.json
    # 2. src/tools.ts
    assert mock_urlopen.call_count == 2
