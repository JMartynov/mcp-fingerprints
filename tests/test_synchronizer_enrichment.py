"""Tests for multi-file tarball synchronization and metadata enrichment (VC-35.1, VC-35.2, VC-35.3)."""

from __future__ import annotations

import io
import json
import tarfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch

from mcp_fingerprints.synchronizer import PassportSynchronizer


class TestSynchronizerEnrichment(unittest.TestCase):
    """Verify multi-file tarball extraction, cross-file PyPI AST bundling, and metadata enrichment."""

    def setUp(self) -> None:
        self.sync = PassportSynchronizer()

    def test_vc35_1_multi_file_npm_tarball_aggregation(self) -> None:
        """Verify that _extract_tools_from_npm_tarball scans all files in a tarball without premature exit."""
        tar_buf = io.BytesIO()
        with tarfile.open(fileobj=tar_buf, mode="w:gz") as tar:
            # File 1: package/dist/file1.js
            code1 = b'''
server.tool("tool_alpha", "First tool", { query: z.string() }, async () => {});
'''
            info1 = tarfile.TarInfo(name="package/dist/file1.js")
            info1.size = len(code1)
            tar.addfile(info1, io.BytesIO(code1))

            # File 2: package/dist/file2.js
            code2 = b'''
server.tool("tool_beta", "Second tool", { count: z.number() }, async () => {});
'''
            info2 = tarfile.TarInfo(name="package/dist/file2.js")
            info2.size = len(code2)
            tar.addfile(info2, io.BytesIO(code2))

            # File 3: package/src/file3.ts
            code3 = b'''
server.tool("tool_gamma", "Third tool", { flag: z.boolean() }, async () => {});
'''
            info3 = tarfile.TarInfo(name="package/src/file3.ts")
            info3.size = len(code3)
            tar.addfile(info3, io.BytesIO(code3))

        tar_bytes = tar_buf.getvalue()

        # Mock urllib.request.urlopen to return tar_bytes
        mock_resp = MagicMock()
        mock_resp.read.side_effect = [tar_bytes, b""]
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            tools = self.sync._extract_tools_from_npm_tarball(
                package_name="test-multi-pkg",
                dist_tarball_url="https://registry.npmjs.org/test-multi-pkg/-/test-multi-pkg-1.0.0.tgz",
            )

        tool_names = [t["name"] for t in tools]
        self.assertEqual(len(tools), 3)
        self.assertIn("tool_alpha", tool_names)
        self.assertIn("tool_beta", tool_names)
        self.assertIn("tool_gamma", tool_names)

    def test_vc35_1_pypi_package_cross_file_ast_bundle(self) -> None:
        """Verify that _extract_tools_from_pypi_package bundles multiple Python files and resolves cross-file models."""
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode="w") as zf:
            zf.writestr(
                "mypkg/models.py",
                '''
from pydantic import BaseModel, Field

class SearchQuery(BaseModel):
    query_text: str = Field(description="Search terms")
    limit: int = Field(default=20, description="Max results")
''',
            )
            zf.writestr(
                "mypkg/server.py",
                '''
from mcp.server.fastmcp import FastMCP
from mypkg.models import SearchQuery

mcp = FastMCP("SearchServer")

@mcp.tool()
def search(query: SearchQuery) -> str:
    """Execute search query."""
    return query.query_text
''',
            )
            zf.writestr(
                "mypkg/extra.py",
                '''
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("ExtraServer")

@mcp.tool()
def health_check() -> str:
    """Check service health."""
    return "ok"
''',
            )

        whl_bytes = zip_buf.getvalue()

        pypi_metadata = {
            "info": {
                "name": "mcp-test-search",
                "version": "1.0.0",
                "author": "Test Author",
            },
            "urls": [
                {
                    "packagetype": "bdist_wheel",
                    "url": "https://files.pythonhosted.org/packages/test/mcp_test_search-1.0.0-py3-none-any.whl",
                }
            ],
        }

        # Mock PyPI metadata request followed by wheel download
        meta_resp = MagicMock()
        meta_resp.read.return_value = json.dumps(pypi_metadata).encode("utf-8")
        meta_resp.__enter__.return_value = meta_resp

        wheel_resp = MagicMock()
        wheel_resp.read.side_effect = [whl_bytes, b""]
        wheel_resp.__enter__.return_value = wheel_resp

        with patch("urllib.request.urlopen", side_effect=[meta_resp, wheel_resp]):
            tools = self.sync._extract_tools_from_pypi_package("mcp-test-search")

        self.assertEqual(len(tools), 2)
        tool_map = {t["name"]: t for t in tools}
        self.assertIn("search", tool_map)
        self.assertIn("health_check", tool_map)

        search_props = tool_map["search"]["inputSchema"]["properties"]
        self.assertIn("query_text", search_props)
        self.assertEqual(search_props["query_text"]["description"], "Search terms")
        self.assertIn("limit", search_props)
        self.assertEqual(search_props["limit"]["default"], 20)

    def test_vc35_2_package_metadata_enrichment_pypi(self) -> None:
        """Verify author and repository_url extraction from PyPI metadata and project_urls."""
        pypi_data = {
            "info": {
                "name": "my-mcp-server",
                "version": "2.1.0",
                "summary": "An MCP server for PyPI testing",
                "author": "Alice Montgomery",
                "project_urls": {
                    "Documentation": "https://docs.alice.org",
                    "Source Code": "https://github.com/alice-montgomery/my-mcp-server",
                    "Homepage": "https://alice.org",
                },
            },
            "releases": {
                "2.1.0": [{"upload_time_iso_8601": "2026-01-01T00:00:00Z"}],
            },
        }

        spec = self.sync.merge_and_enrich_passport(
            package_name="my-mcp-server",
            ecosystem="pypi",
            pypi_data=pypi_data,
            pre_extracted_tools=[{"name": "test_tool", "description": "A test tool", "inputSchema": {}}],
            auto_cross_resolve=False,
        )

        self.assertIsNotNone(spec)
        self.assertEqual(spec.author, "Alice Montgomery")
        self.assertEqual(spec.repository_url, "https://github.com/alice-montgomery/my-mcp-server")
        self.assertEqual(spec.description, "An MCP server for PyPI testing")

    def test_vc35_2_package_metadata_enrichment_npm(self) -> None:
        """Verify author extraction from NPM registry metadata."""
        npm_data = {
            "name": "@alice/npm-mcp-tool",
            "description": "An NPM MCP server",
            "author": {
                "name": "Bob Martinez",
                "email": "bob@example.com",
            },
            "homepage": "https://github.com/bob/npm-mcp-tool",
            "dist-tags": {"latest": "1.0.0"},
            "versions": {
                "1.0.0": {
                    "version": "1.0.0",
                    "dependencies": {},
                }
            },
            "time": {"1.0.0": "2026-02-01T00:00:00Z"},
        }

        spec = self.sync.merge_and_enrich_passport(
            package_name="@alice/npm-mcp-tool",
            ecosystem="npm",
            npm_data=npm_data,
            pre_extracted_tools=[{"name": "test_tool", "description": "A test tool", "inputSchema": {}}],
            auto_cross_resolve=False,
        )

        self.assertIsNotNone(spec)
        self.assertEqual(spec.author, "Bob Martinez")
        self.assertEqual(spec.repository_url, "https://github.com/bob/npm-mcp-tool")


if __name__ == "__main__":
    unittest.main()
