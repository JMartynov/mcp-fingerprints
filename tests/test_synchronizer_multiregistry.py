"""Unit tests for multi-registry synchronizer updates and safe tool provenance."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature
from mcp_fingerprints.synchronizer import PassportSynchronizer


class TestSynchronizerMultiRegistry(unittest.TestCase):
    """Test suite verifying PyPI, Smithery and npm synchronization with safe provenance."""

    def test_pypi_version_update_and_provenance(self) -> None:
        """Verify update_existing_passports detects PyPI version bump and marks inherited tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            passport_path = out_dir / "pypi_fastmcp.json"

            initial_spec = ServerPackageSpec(
                package_name="fastmcp",
                purl="pkg:pypi/fastmcp",
                ecosystem="pypi",
                sources_merged=("pypi",),
                versions=(
                    VersionFingerprint(
                        version="0.1.0",
                        toolset_canonical_hash="sha256:1111111111111111111111111111111111111111111111111111111111111111",
                        tool_signatures=(
                            ToolContractSignature(
                                name="echo",
                                description="Echo tool",
                                canonical_hash="sha256:2222222222222222222222222222222222222222222222222222222222222222",
                            ),
                        ),
                    ),
                ),
            )
            passport_path.write_text(json.dumps(initial_spec.to_dict()), encoding="utf-8")

            # Mock PyPI API response announcing version 0.2.0
            mock_pypi_response = {
                "info": {"version": "0.2.0", "summary": "FastMCP library"},
                "releases": {
                    "0.1.0": [{"upload_time_iso_8601": "2025-01-01T00:00:00Z"}],
                    "0.2.0": [{"upload_time_iso_8601": "2025-02-01T00:00:00Z"}],
                },
            }

            sync = PassportSynchronizer(output_dir=out_dir)
            with patch("mcp_fingerprints.synchronizer.fetch_json", return_value=(mock_pypi_response, None)):
                updated_count = sync.update_existing_passports()

            self.assertEqual(updated_count, 1)

            # Inspect updated passport
            updated_data = json.loads(passport_path.read_text(encoding="utf-8"))
            updated_spec = ServerPackageSpec.from_dict(updated_data)

            version_map = {v.version: v for v in updated_spec.versions}
            self.assertIn("0.1.0", version_map)
            self.assertIn("0.2.0", version_map)

            # Verify historical 0.1.0 tool signature was strictly preserved
            self.assertEqual(len(version_map["0.1.0"].tool_signatures), 1)
            self.assertEqual(version_map["0.1.0"].tool_signatures[0].name, "echo")

            # Verify 0.2.0 has inherited_tools = True
            v_020 = version_map["0.2.0"]
            self.assertTrue(v_020.capabilities.get("inherited_tools", False))

    def test_smithery_version_update(self) -> None:
        """Verify update_existing_passports detects Smithery version bump."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            passport_path = out_dir / "smithery_example.json"

            initial_spec = ServerPackageSpec(
                package_name="test-server",
                purl="pkg:smithery/test-server",
                ecosystem="smithery",
                sources_merged=("smithery",),
                versions=(
                    VersionFingerprint(
                        version="1.0.0",
                        toolset_canonical_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    ),
                ),
            )
            passport_path.write_text(json.dumps(initial_spec.to_dict()), encoding="utf-8")

            # Mock Smithery API response with new version 1.1.0 and live verified tools
            mock_smithery_detail = {
                "version": "1.1.0",
                "description": "Updated Smithery server",
                "tools": [
                    {
                        "name": "calculate",
                        "description": "Perform calculation",
                        "inputSchema": {"type": "object", "properties": {"x": {"type": "number"}}},
                    }
                ],
            }

            sync = PassportSynchronizer(output_dir=out_dir)
            with patch("mcp_fingerprints.synchronizer.fetch_json", return_value=(mock_smithery_detail, None)):
                updated_count = sync.update_existing_passports()

            self.assertEqual(updated_count, 1)

            updated_data = json.loads(passport_path.read_text(encoding="utf-8"))
            updated_spec = ServerPackageSpec.from_dict(updated_data)

            version_map = {v.version: v for v in updated_spec.versions}
            self.assertIn("1.1.0", version_map)
            # Live tools from registry must have verified_tools = True
            self.assertTrue(version_map["1.1.0"].capabilities.get("verified_tools", False))
            self.assertEqual(len(version_map["1.1.0"].tool_signatures), 1)

    def test_ast_tool_extraction_and_enrichment(self) -> None:
        """Verify enrich_zero_tool_passports discovers tools via static AST and updates passport."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            passport_path = out_dir / "zero_tool_server.json"

            initial_spec = ServerPackageSpec(
                package_name="test-org/test-server",
                purl="pkg:generic/test-org%2Ftest-server",
                ecosystem="generic",
                repository_url="https://github.com/test-org/test-server",
                sources_merged=("official_registry",),
                versions=(
                    VersionFingerprint(
                        version="1.0.0",
                        toolset_canonical_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    ),
                ),
            )
            passport_path.write_text(json.dumps(initial_spec.to_dict()), encoding="utf-8")

            sample_server_code = b"""
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
const server = new Server({ name: "test", version: "1.0.0" });
server.tool(
    "query_weather",
    "Get current weather for location",
    { location: z.string() },
    async ({ location }) => ({ weather: "sunny" })
);
"""

            class MockResponse:
                def __init__(self, data: bytes, status: int = 200) -> None:
                    self.data = data
                    self.status = status

                def read(self) -> bytes:
                    return self.data

                def __enter__(self) -> MockResponse:
                    return self

                def __exit__(self, *args: object) -> None:
                    pass

            sync = PassportSynchronizer(output_dir=out_dir)

            # Mock urlopen: return MockResponse for source file URL, 404 otherwise
            def mock_urlopen(req: object, *args: object, **kwargs: object) -> MockResponse:
                url_str = req.full_url if hasattr(req, "full_url") else str(req)
                if "src/index.ts" in url_str:
                    return MockResponse(sample_server_code, status=200)
                raise Exception("Not Found")

            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                with patch("mcp_fingerprints.synchronizer.fetch_json", return_value=(None, None)):
                    enriched_count = sync.enrich_zero_tool_passports(limit=5)

            self.assertEqual(enriched_count, 1)

            updated_data = json.loads(passport_path.read_text(encoding="utf-8"))
            updated_spec = ServerPackageSpec.from_dict(updated_data)

            self.assertIn("github_ast", updated_spec.sources_merged)
            self.assertEqual(len(updated_spec.versions), 1)
            v0 = updated_spec.versions[0]
            self.assertTrue(v0.capabilities.get("tools", False))
            self.assertTrue(v0.capabilities.get("verified_tools", False))
            self.assertEqual(len(v0.tool_signatures), 1)
            self.assertEqual(v0.tool_signatures[0].name, "query_weather")
            self.assertEqual(v0.tool_signatures[0].description, "Get current weather for location")
            self.assertNotEqual(
                v0.toolset_canonical_hash,
                "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )

    def test_github_token_header_injection(self) -> None:
        """Verify GITHUB_TOKEN or GH_TOKEN adds Authorization Bearer header."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_secret_token_123"}, clear=True):
            headers = PassportSynchronizer._get_github_headers()
            self.assertEqual(headers.get("Authorization"), "Bearer ghp_test_secret_token_123")
            self.assertEqual(headers.get("Accept"), "application/vnd.github.v3+json")

            raw_headers = PassportSynchronizer._get_github_headers(raw=True)
            self.assertEqual(raw_headers.get("Authorization"), "Bearer ghp_test_secret_token_123")
            self.assertNotIn("Accept", raw_headers)

        with patch.dict(os.environ, {"GH_TOKEN": "ghp_alt_token_456"}, clear=True):
            headers = PassportSynchronizer._get_github_headers()
            self.assertEqual(headers.get("Authorization"), "Bearer ghp_alt_token_456")

        with patch.dict(os.environ, {}, clear=True):
            headers = PassportSynchronizer._get_github_headers()
            self.assertNotIn("Authorization", headers)


if __name__ == "__main__":
    unittest.main()
