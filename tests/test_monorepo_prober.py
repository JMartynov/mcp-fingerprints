import json
import urllib.error
import urllib.request
from unittest.mock import patch, MagicMock
from mcp_fingerprints.synchronizer import PassportSynchronizer

@patch("urllib.request.urlopen")
def test_github_tree_monorepo_deep_extraction(mock_urlopen):
    sync = PassportSynchronizer()
    
    def urlopen_side_effect(req, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status = 200
        
        url = req.full_url
        if "api.github.com/repos/modelcontextprotocol/servers/git/trees/main" in url:
            tree_data = {
                "tree": [
                    # Depth 1
                    {"type": "blob", "path": "README.md"},
                    # Depth 2
                    {"type": "blob", "path": "src/index.ts"},
                    # Depth 3
                    {"type": "blob", "path": "src/servers/postgres/index.ts"},
                    # Depth 4 (Monorepo specific package structure)
                    {"type": "blob", "path": "packages/server-postgres/src/index.ts"},
                    {"type": "blob", "path": "packages/server-postgres/src/tools.ts"},
                    # Depth 5 (Ignored)
                    {"type": "blob", "path": "packages/server-postgres/src/utils/helpers.ts"}
                ]
            }
            mock_resp.read.return_value = json.dumps(tree_data).encode("utf-8")
        elif "raw.githubusercontent.com/modelcontextprotocol/servers/main/packages/server-postgres/src/index.ts" in url:
            mock_resp.read.return_value = 'server.tool("postgres_query", "Query postgres", {});'.encode("utf-8")
        elif "raw.githubusercontent.com/modelcontextprotocol/servers/main/packages/server-postgres/src/tools.ts" in url:
            mock_resp.read.return_value = 'server.tool("postgres_insert", "Insert postgres", {});'.encode("utf-8")
        elif "raw.githubusercontent.com/modelcontextprotocol/servers/main/src/index.ts" in url:
            mock_resp.read.return_value = 'server.tool("root_tool", "Root tool", {});'.encode("utf-8")
        elif "raw.githubusercontent.com/modelcontextprotocol/servers/main/src/servers/postgres/index.ts" in url:
            mock_resp.read.return_value = 'server.tool("old_postgres", "Old postgres", {});'.encode("utf-8")
        else:
            mock_resp.status = 404
            
        # Context manager support
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    tools = sync._extract_ast_tools_from_github("@modelcontextprotocol/server-postgres", repo_url="https://github.com/modelcontextprotocol/servers")
    
    assert len(tools) > 0
    # Should prioritize the packages/server-postgres/src/index.ts and packages/server-postgres/src/tools.ts files.
    tool_names = {t["name"] for t in tools}
    assert "postgres_query" in tool_names
    assert "postgres_insert" in tool_names
    assert "root_tool" not in tool_names
    assert "old_postgres" not in tool_names


@patch("urllib.request.urlopen")
def test_github_tree_monorepo_size_limit_and_cap(mock_urlopen):
    sync = PassportSynchronizer()
    
    def urlopen_side_effect(req, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status = 200
        
        url = req.full_url
        if "api.github.com/repos/org/monorepo/git/trees/main" in url:
            tree_data = {
                "tree": [
                    {"type": "blob", "path": "packages/pkg1/server.py"},
                    {"type": "blob", "path": "packages/pkg2/server.py"},
                    {"type": "blob", "path": "packages/pkg3/server.py"},
                    {"type": "blob", "path": "packages/pkg4/server.py"},
                    {"type": "blob", "path": "packages/pkg5/server.py"},
                    {"type": "blob", "path": "packages/pkg6/server.py"},
                ]
            }
            mock_resp.read.return_value = json.dumps(tree_data).encode("utf-8")
        elif "raw.githubusercontent.com/org/monorepo/main/packages/" in url:
            
            # The read size is capped at 500KB. We mock the read method to track the size argument passed.
            def read_mock(size=-1):
                if size != -1:
                    assert size <= 500 * 1024
                # Parse python tool
                return b'@server.tool()\ndef pkg_tool():\n    pass'
            mock_resp.read = MagicMock(side_effect=read_mock)
        else:
            mock_resp.status = 404
            
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    tools = sync._extract_ast_tools_from_github("pkg1", repo_url="https://github.com/org/monorepo")
    
    # Check that cap is max 5 files.
    assert len(tools) == 1
    tool_names = {t["name"] for t in tools}
    assert "pkg_tool" in tool_names
