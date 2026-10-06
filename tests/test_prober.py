"""Unit tests for McpStdioProber and live runtime inspection."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.prober import McpStdioProber


MOCK_SERVER_SCRIPT = """
import sys, json

while True:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        req = json.loads(line)
        method = req.get("method")
        msg_id = req.get("id")
        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "test-mock-server", "version": "1.0.0"},
                    "capabilities": {"tools": {}}
                }
            }
            sys.stdout.write(json.dumps(resp) + "\\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "lookup_user",
                            "description": "Look up user details",
                            "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}}}
                        }
                    ]
                }
            }
            sys.stdout.write(json.dumps(resp) + "\\n")
            sys.stdout.flush()
        elif method in ("prompts/list", "resources/list"):
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            sys.stdout.write(json.dumps(resp) + "\\n")
            sys.stdout.flush()
    except Exception:
        break
"""


class TestMcpStdioProber(unittest.TestCase):
    """Test suite verifying McpStdioProber communication, matching, and vulnerability auditing."""

    def test_build_package_command(self) -> None:
        cmd_npm = McpStdioProber.build_package_command("@modelcontextprotocol/server-brave", ecosystem="npm")
        self.assertEqual(cmd_npm, ["npx", "-y", "@modelcontextprotocol/server-brave"])

        cmd_pypi = McpStdioProber.build_package_command("mcp-server-git", ecosystem="pypi")
        self.assertEqual(cmd_pypi, ["python", "-m", "mcp_server_git"])

        cmd_uvx = McpStdioProber.build_package_command("some-custom-pypi", ecosystem="pypi")
        self.assertEqual(cmd_uvx, ["uvx", "some-custom-pypi"])

    def test_probe_live_mock_mcp_server(self) -> None:
        """Verify McpStdioProber handshakes with mock server and matches its identity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            server_file = Path(tmpdir) / "mock_server.py"
            server_file.write_text(MOCK_SERVER_SCRIPT, encoding="utf-8")

            # Create matcher with matching passport
            matcher = FingerprintMatcher()
            spec = ServerPackageSpec(
                package_name="user-service-mcp",
                purl="pkg:npm/user-service-mcp",
                ecosystem="npm",
                versions=(
                    VersionFingerprint(
                        version="1.0.0",
                        toolset_canonical_hash="sha256:1111111111111111111111111111111111111111111111111111111111111111",
                        tool_signatures=(
                            ToolContractSignature(
                                name="lookup_user",
                                description="Look up user details",
                                canonical_hash="sha256:2222222222222222222222222222222222222222222222222222222222222222",
                                input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
                            ),
                        ),
                    ),
                ),
                security_profile={
                    "has_known_vulnerabilities": True,
                    "max_cvss_score": 8.5,
                    "vulnerable_versions": ["1.0.0"],
                    "advisories": [
                        {
                            "id": "CVE-2026-TEST",
                            "severity": "HIGH",
                            "cvss_score": 8.5,
                            "summary": "Information disclosure in lookup_user",
                            "fixed_version": "1.0.1",
                            "affected_versions": ["1.0.0"],
                        }
                    ],
                },
            )
            matcher.register_package(spec)

            prober = McpStdioProber(matcher)
            report = prober.probe(
                command=[sys.executable, str(server_file)],
                timeout=5.0,
            )

            self.assertTrue(report.connection_successful)
            self.assertEqual(len(report.tools_observed), 1)
            self.assertEqual(report.tools_observed[0]["name"], "lookup_user")

            self.assertIsNotNone(report.match_result)
            assert report.match_result is not None
            self.assertTrue(report.match_result.matched)
            self.assertEqual(report.match_result.package_name, "user-service-mcp")
            self.assertEqual(report.match_result.matched_version, "1.0.0")

            # Check vulnerability audit
            self.assertTrue(report.is_vulnerable)
            self.assertEqual(report.max_cvss_score, 8.5)
            self.assertEqual(report.recommended_fixed_version, "1.0.1")
            self.assertEqual(len(report.active_advisories), 1)
            self.assertEqual(report.active_advisories[0]["id"], "CVE-2026-TEST")


if __name__ == "__main__":
    unittest.main()
