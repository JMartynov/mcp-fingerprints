import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from mcp_fingerprints.synchronizer import PassportSynchronizer

class TestDockerPolyglotSync(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_docker_hub_discovery(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = b"{\"crates\": []}"
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            sync = PassportSynchronizer(output_dir=tmpdir)
            
            def mock_fetch_json(url):
                if "v2/search/repositories" in url:
                    return {
                        "results": [
                            {
                                "repo_name": "library/mcp-server",
                                "short_description": "A test docker server"
                            }
                        ]
                    }, {}
                elif "v2/repositories/library/mcp-server/" in url:
                    return {
                        "full_description": "# Tools\n\n| Tool | Description |\n|---|---|\n| docker_tool | Docker test tool |"
                    }, {}
                return {}, {}
            
            with patch("mcp_fingerprints.synchronizer.fetch_json", side_effect=mock_fetch_json):
                sync.discover_new_mcps(limit=10, docker=True, polyglot=False)
                
            out_file = Path(tmpdir) / "docker_library_mcp-server.json"
            self.assertTrue(out_file.exists())
            
            with open(out_file, "r") as f:
                data = json.load(f)
                
            self.assertEqual(data["package_name"], "docker_library_mcp-server")
            self.assertEqual(data["ecosystem"], "docker")
            self.assertEqual(len(data["versions"]), 1)
            
            tools = data["versions"][0].get("tool_signatures", [])
            self.assertEqual(len(tools), 1)
            self.assertEqual(tools[0]["name"], "docker_tool")
            self.assertEqual(tools[0]["description"], "Docker test tool")

    @patch("urllib.request.urlopen")
    def test_polyglot_github_discovery(self, mock_urlopen):
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = PassportSynchronizer(output_dir=tmpdir)
            
            def mock_fetch_json(url):
                import urllib.parse
                if urllib.parse.quote("topic:mcp-server language:rust") in url:
                    return {
                        "items": [
                            {
                                "full_name": "testowner/rust-mcp-server",
                                "description": "Rust test server",
                                "default_branch": "main"
                            }
                        ]
                    }, {}
                elif urllib.parse.quote("topic:mcp-server language:go") in url:
                    return {"items": []}, {}
                # Avoid smithery and pypi
                return None, None
            
            def urlopen_side_effect(req, *args, **kwargs):
                mock_resp = MagicMock()
                mock_resp.__enter__.return_value = mock_resp
                mock_resp.status = 200
                
                # Default empty JSON byte string
                mock_resp.read.return_value = b"{}"
                
                try:
                    url = req.full_url
                except AttributeError:
                    url = str(req)
                
                if "crates.io" in url:
                    mock_resp.read.return_value = b'{"crates": []}'
                elif "smithery" in url or "awesome" in url:
                    mock_resp.read.return_value = b"{}"
                elif "README.md" in url:
                    mock_resp.read.return_value = b"# Tools\n\n| Tool | Description |\n|---|---|\n| rust_tool | Rust test tool |"
                    
                return mock_resp

            mock_urlopen.side_effect = urlopen_side_effect
            
            with patch("mcp_fingerprints.synchronizer.fetch_json", side_effect=mock_fetch_json), \
                 patch("mcp_fingerprints.synchronizer.parse_markdown_tool_docs", return_value=[{"name": "rust_tool", "description": "Rust test tool", "inputSchema": {"type": "object", "properties": {}}}]):
                sync.discover_new_mcps(limit=10, docker=False, polyglot=True)
                
            out_file = Path(tmpdir) / "github_testowner_rust-mcp-server.json"
            self.assertTrue(out_file.exists())
            
            with open(out_file, "r") as f:
                data = json.load(f)
                
            self.assertEqual(data["package_name"], "github_testowner_rust-mcp-server")
            self.assertEqual(data["ecosystem"], "cargo")
            
            tools = data["versions"][0].get("tool_signatures", [])
            self.assertEqual(len(tools), 1)
            self.assertEqual(tools[0]["name"], "rust_tool")
            self.assertEqual(tools[0]["description"], "Rust test tool")

    @patch("urllib.request.urlopen")
    @patch("mcp_fingerprints.crawler.crates_io.get_mcp_crates")
    def test_crates_io_discovery_and_unpacking(self, mock_get_crates, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = b"{}"
        mock_urlopen.return_value = mock_resp

        mock_get_crates.return_value = [
            {
                "name": "mcp-test-empty-tools",
                "max_version": "0.1.0",
                "description": "Empty tools crate",
                "repository": "https://github.com/testowner/mcp-test-empty-tools",
            },
            {
                "name": "mcp-test-with-tools",
                "max_version": "0.2.0",
                "description": "With tools crate",
                "repository": "https://github.com/testowner/mcp-test-with-tools",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            sync = PassportSynchronizer(output_dir=tmpdir)

            def mock_extract(pkg_name, repo_url=None):
                if pkg_name == "mcp-test-with-tools":
                    return [{"name": "test_rust_tool", "description": "tool desc", "inputSchema": {"type": "object"}}]
                return []

            with patch.object(sync, "_extract_ast_tools_from_github", side_effect=mock_extract), \
                 patch("mcp_fingerprints.synchronizer.fetch_json", return_value=(None, None)):
                count = sync.discover_new_mcps(limit=10, docker=False, polyglot=False)

            self.assertEqual(count, 1)
            out_file = Path(tmpdir) / "mcp-test-with-tools.json"
            self.assertTrue(out_file.exists())
            with open(out_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data["package_name"], "mcp-test-with-tools")
            self.assertEqual(data["ecosystem"], "cargo")
            self.assertEqual(len(data["versions"][0]["tool_signatures"]), 1)
            self.assertEqual(data["versions"][0]["tool_signatures"][0]["name"], "test_rust_tool")

if __name__ == '__main__':
    unittest.main()
