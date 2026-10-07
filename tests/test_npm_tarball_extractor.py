import io
import tarfile
import unittest
from unittest.mock import patch, MagicMock

from mcp_fingerprints.synchronizer import PassportSynchronizer

def create_in_memory_tarball(files_content: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for filename, content in files_content.items():
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))
    return buf.getvalue()


class TestNpmTarballExtractor(unittest.TestCase):
    def setUp(self):
        self.sync = PassportSynchronizer(output_dir="/tmp/dummy", state_file="/tmp/dummy/state.json")
    
    @patch("urllib.request.urlopen")
    def test_npm_tarball_in_memory_dist_js(self, mock_urlopen):
        code = b'''
        import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
        import { z } from "zod";
        const server = new McpServer({ name: "test-server", version: "1.0.0" });
        server.tool("test_tool", "A test tool", {
            param1: z.string()
        }, async ({ param1 }) => { return { content: [] }; });
        '''
        tarball_bytes = create_in_memory_tarball({
            "package/package.json": b'{"name": "test-pkg", "version": "1.0.0"}',
            "package/dist/server.js": code
        })

        mock_response = MagicMock()
        mock_response.read.side_effect = [tarball_bytes, b""]
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        tools = self.sync._extract_tools_from_npm_tarball("test-pkg", "http://fake-url/test-pkg.tgz")
        
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "test_tool")
        self.assertEqual(tools[0]["description"], "A test tool")
        self.assertIn("param1", tools[0]["inputSchema"]["properties"])

    @patch("urllib.request.urlopen")
    def test_npm_tarball_in_memory_mjs_sources(self, mock_urlopen):
        code = b'''
        import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
        import { z } from "zod";
        const server = new McpServer({ name: "test-server-2", version: "1.0.0" });
        server.tool("custom_tool_mjs", "A custom tool", {
            age: z.number()
        }, async ({ age }) => { return { content: [] }; });
        '''
        tarball_bytes = create_in_memory_tarball({
            "package/src/custom-tools.mjs": code
        })

        mock_response = MagicMock()
        mock_response.read.side_effect = [tarball_bytes, b""]
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        tools = self.sync._extract_tools_from_npm_tarball("test-pkg", "http://fake-url/test-pkg.tgz")
        
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "custom_tool_mjs")
        self.assertEqual(tools[0]["description"], "A custom tool")
        self.assertIn("age", tools[0]["inputSchema"]["properties"])

    @patch("urllib.request.urlopen")
    def test_npm_tarball_size_limit_guard(self, mock_urlopen):
        mock_response = MagicMock()
        # Return chunks that will exceed the 10MB limit (10 * 1024 * 1024 = 10485760 bytes)
        chunk_size = 1024 * 1024 # 1MB
        chunks = [b"a" * chunk_size] * 12 # 12MB total
        chunks.append(b"") # EOF
        mock_response.read.side_effect = chunks
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        tools = self.sync._extract_tools_from_npm_tarball("test-pkg", "http://fake-url/test-pkg.tgz")
        self.assertEqual(tools, []) # Should gracefully return empty list

if __name__ == '__main__':
    unittest.main()
