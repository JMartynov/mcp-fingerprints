import json
import urllib.error
import urllib.request
from unittest.mock import patch, MagicMock
from mcp_fingerprints.synchronizer import PassportSynchronizer

@patch("urllib.request.urlopen")
def test_github_tree_modular_submodules_merging(mock_urlopen):
    sync = PassportSynchronizer()
    
    # We will mock the responses for the Tree API and the raw files.
    
    def urlopen_side_effect(req, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status = 200
        
        url = req.full_url
        if "api.github.com/repos/owner/repo/git/trees/main" in url:
            tree_data = {
                "tree": [
                    {"type": "blob", "path": "src/tools/express.ts"},
                    {"type": "blob", "path": "src/tools/platform.ts"},
                    {"type": "blob", "path": "README.md"}
                ]
            }
            mock_resp.read.return_value = json.dumps(tree_data).encode("utf-8")
        elif "raw.githubusercontent.com/owner/repo/main/src/tools/express.ts" in url:
            mock_resp.read.return_value = 'server.tool("express_tool", "Express Tool", {});'.encode("utf-8")
        elif "raw.githubusercontent.com/owner/repo/main/src/tools/platform.ts" in url:
            mock_resp.read.return_value = 'server.tool("platform_tool", "Platform Tool", {});'.encode("utf-8")
        else:
            mock_resp.status = 404
            
        # Context manager support
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    tools = sync._extract_ast_tools_from_github("owner/repo", repo_url="https://github.com/owner/repo")
    
    assert len(tools) == 2
    tool_names = {t["name"] for t in tools}
    assert "express_tool" in tool_names
    assert "platform_tool" in tool_names

@patch("urllib.request.urlopen")
def test_github_tree_python_package_structure(mock_urlopen):
    sync = PassportSynchronizer()
    
    def urlopen_side_effect(req, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status = 200
        
        url = req.full_url
        if "api.github.com/repos/schemabrain/mcp/git/trees/main" in url:
            tree_data = {
                "tree": [
                    {"type": "blob", "path": "schemabrain/mcp/server.py"},
                    {"type": "blob", "path": "tools/audio_tools.py"},
                    {"type": "blob", "path": "tests/test_server.py"}
                ]
            }
            mock_resp.read.return_value = json.dumps(tree_data).encode("utf-8")
        elif "raw.githubusercontent.com/schemabrain/mcp/main/schemabrain/mcp/server.py" in url:
            mock_resp.read.return_value = '@server.tool()\ndef schemabrain_tool():\n    """Schemabrain Tool"""\n    pass'.encode("utf-8")
        elif "raw.githubusercontent.com/schemabrain/mcp/main/tools/audio_tools.py" in url:
            mock_resp.read.return_value = '@server.tool()\ndef audio_tool():\n    """Audio Tool"""\n    pass'.encode("utf-8")
        else:
            mock_resp.status = 404
            
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    tools = sync._extract_ast_tools_from_github("schemabrain/mcp", repo_url="https://github.com/schemabrain/mcp")
    
    assert len(tools) == 2
    tool_names = {t["name"] for t in tools}
    assert "schemabrain_tool" in tool_names
    assert "audio_tool" in tool_names

@patch("urllib.request.urlopen")
def test_github_tree_rate_limit_fallback(mock_urlopen):
    sync = PassportSynchronizer()
    
    def urlopen_side_effect(req, *args, **kwargs):
        url = req.full_url
        if "api.github.com" in url:
            raise urllib.error.HTTPError(url, 403, "Rate Limit Exceeded", {}, None)
            
        mock_resp = MagicMock()
        mock_resp.status = 200
        
        if "package.json" in url:
            mock_resp.status = 404
        elif "raw.githubusercontent.com/owner/repo/main/src/server.ts" in url:
            mock_resp.read.return_value = 'server.tool("fallback_tool", "Fallback Tool", {});'.encode("utf-8")
        else:
            mock_resp.status = 404
            
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    tools = sync._extract_ast_tools_from_github("owner/repo", repo_url="https://github.com/owner/repo")
    
    assert len(tools) == 1
    assert tools[0]["name"] == "fallback_tool"

