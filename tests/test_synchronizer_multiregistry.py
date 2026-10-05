"""Unit tests for multi-registry synchronizer updates and safe tool provenance."""

from __future__ import annotations

import json
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


if __name__ == "__main__":
    unittest.main()
