"""Unit tests for the CLI match subcommand."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp_fingerprints.cli import main
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature


class TestCliMatch(unittest.TestCase):
    """Test suite verifying CLI match command behavior and report outputs."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmpdir.name)

        # Create a test passport
        spec = ServerPackageSpec(
            package_name="test-calculator",
            purl="pkg:npm/test-calculator",
            ecosystem="npm",
            versions=(
                VersionFingerprint(
                    version="1.0.0",
                    toolset_canonical_hash="sha256:37c54d57518f7e23b1440168364a5cc5487cdbaa818e306f29e130d4a248f53d",
                    tool_signatures=(
                        ToolContractSignature(
                            name="add",
                            description="Add two numbers",
                            canonical_hash="sha256:1111111111111111111111111111111111111111111111111111111111111111",
                            input_schema={"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
                        ),
                    ),
                ),
            ),
        )
        (self.out_dir / "test-calculator.json").write_text(json.dumps(spec.to_dict()), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_cli_match_stdin_json(self) -> None:
        """Verify CLI match parses input from stdin and outputs valid JSON."""
        input_tools = [
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
            }
        ]
        stdin_buf = io.StringIO(json.dumps(input_tools))
        stdout_buf = io.StringIO()

        test_args = ["mcp_fingerprints.cli", "match", "--dir", str(self.out_dir), "--json"]
        with patch.object(sys, "argv", test_args), patch.object(sys, "stdin", stdin_buf), patch.object(sys, "stdout", stdout_buf):
            main()

        output = stdout_buf.getvalue()
        res = json.loads(output)
        self.assertTrue(res["matched"])
        self.assertEqual(res["package_name"], "test-calculator")
        self.assertEqual(res["matched_version"], "1.0.0")
        self.assertTrue(res["confidence_score"] >= 0.65)

    def test_cli_match_file_human_report(self) -> None:
        """Verify CLI match with --input-file outputs human-readable report."""
        tools_file = self.out_dir / "observed.json"
        tools_file.write_text(json.dumps({
            "tools": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "inputSchema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
                }
            ]
        }), encoding="utf-8")

        stdout_buf = io.StringIO()
        test_args = ["mcp_fingerprints.cli", "match", "--dir", str(self.out_dir), "--input-file", str(tools_file)]
        with patch.object(sys, "argv", test_args), patch.object(sys, "stdout", stdout_buf):
            main()

        output = stdout_buf.getvalue()
        self.assertIn("MCP FINGERPRINT MATCH REPORT", output)
        self.assertIn("Package:            test-calculator", output)
        self.assertIn("Matched:            True", output)


if __name__ == "__main__":
    unittest.main()
