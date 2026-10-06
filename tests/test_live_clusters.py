"""Live web integration tests for MCP passport root-cause clusters.

Connecting directly to real web data sources:
- Official MCP Registry API (https://registry.modelcontextprotocol.io)
- npm Registry API (https://registry.npmjs.org)
- PyPI Registry API (https://pypi.org)
- Smithery API (https://api.smithery.ai)
- GitHub Raw Content (https://raw.githubusercontent.com)
"""

from __future__ import annotations

import os
import unittest

import pytest

from mcp_fingerprints.synchronizer import PassportSynchronizer, fetch_json

pytestmark = pytest.mark.integration

LIVE_INTEGRATION_ENV = "RUN_LIVE_INTEGRATION_TESTS"


def _require_live_integration() -> None:
    """Skip network-dependent tests unless explicitly enabled for integration runs."""
    if not os.getenv(LIVE_INTEGRATION_ENV):
        pytest.skip(
            "Live integration tests are disabled by default; set RUN_LIVE_INTEGRATION_TESTS=1 "
            "to run them."
        )


class TestLiveClustersIntegration(unittest.TestCase):
    """Live web integration tests validating issue causes and solutions for all 4 clusters."""

    def test_cluster1_official_registry_and_smithery_cross_resolution(self) -> None:
        """Cluster 1: Official MCP Registry lacks tool schemas natively.

        Live connection demonstrates fetching from Official Registry, identifying missing tools,
        and cross-resolving against Smithery / manifest sources to hydrate tool signatures.
        """
        _require_live_integration()
        # 1. Fetch live entry from Official Registry
        reg_data, _ = fetch_json("https://registry.modelcontextprotocol.io/v0.1/servers")
        self.assertIsNotNone(reg_data, "Official Registry API should be reachable")
        self.assertIn("servers", reg_data)
        servers = reg_data.get("servers", [])
        self.assertGreater(len(servers), 0)

        sample_entry = servers[0]
        srv = sample_entry.get("server", {})
        srv_name = srv.get("name")
        self.assertIsNotNone(srv_name)

        # Confirm Official Registry natively provides server metadata but NO tool contracts
        self.assertNotIn("tools", srv)

        # 2. Synchronize sample official registry server with curated flag
        syncer = PassportSynchronizer()
        passport = syncer.merge_and_enrich_passport(
            package_name=srv_name,
            ecosystem="generic",
            official_registry_data=sample_entry,
            is_curated_source=True,
        )
        self.assertIsNotNone(passport)
        self.assertIn("official_registry", passport.sources_merged)

        # 3. Resolve tools via live Smithery lookup for known package (e.g. brave)
        smithery_data, _ = fetch_json("https://api.smithery.ai/servers/brave")
        self.assertIsNotNone(smithery_data)
        self.assertIn("tools", smithery_data)
        self.assertGreater(len(smithery_data["tools"]), 0)

        # Enrich passport with Smithery cross-registry tool contracts
        enriched_passport = syncer.merge_and_enrich_passport(
            package_name="brave",
            ecosystem="npm",
            official_registry_data=sample_entry,
            smithery_data=smithery_data,
            is_curated_source=True,
        )
        self.assertIsNotNone(enriched_passport)
        latest_version = enriched_passport.versions[-1]
        self.assertGreater(len(latest_version.tool_signatures), 0)

    def test_cluster2_npm_registry_cross_resolution(self) -> None:
        """Cluster 2: npm Registry package.json lacks runtime tool contracts.

        Live connection fetches package metadata from npm and resolves tool contracts via Smithery API.
        """
        _require_live_integration()
        pkg_name = "express"

        # 1. Fetch live metadata from npm registry
        npm_data, _ = fetch_json(f"https://registry.npmjs.org/{pkg_name}")
        self.assertIsNotNone(npm_data, "npm registry should return metadata")
        self.assertEqual(npm_data.get("name"), pkg_name)
        self.assertNotIn("tools", npm_data, "npm registry does not store runtime tool definitions")

        # 2. Fetch live runtime tool signatures from Smithery API for brave
        smithery_data, _ = fetch_json("https://api.smithery.ai/servers/brave")
        self.assertIsNotNone(smithery_data, "Smithery API should possess runtime tools")
        self.assertIn("tools", smithery_data)
        self.assertGreater(len(smithery_data["tools"]), 0)

        # 3. Merge npm metadata + Smithery runtime tools into complete Passport
        syncer = PassportSynchronizer()
        passport = syncer.merge_and_enrich_passport(
            package_name=pkg_name,
            ecosystem="npm",
            npm_data=npm_data,
            smithery_data=smithery_data,
            is_curated_source=True,
        )
        self.assertIsNotNone(passport)
        self.assertIn("npm_registry", passport.sources_merged)
        self.assertIn("smithery", passport.sources_merged)

        latest_ver = passport.versions[-1]
        self.assertGreater(len(latest_ver.tool_signatures), 0)

    def test_cluster3_pypi_registry_cross_resolution(self) -> None:
        """Cluster 3: PyPI packages lack tool definitions in package metadata.

        Live connection fetches PyPI metadata and cross-resolves tool contracts.
        """
        _require_live_integration()
        pkg_name = "mcp"

        # 1. Fetch live PyPI metadata
        pypi_data, _ = fetch_json(f"https://pypi.org/pypi/{pkg_name}/json")
        self.assertIsNotNone(pypi_data, "PyPI API should return package info")
        self.assertEqual(pypi_data.get("info", {}).get("name"), pkg_name)
        self.assertNotIn("tools", pypi_data.get("info", {}))

        # 2. Cross-resolve tools from Smithery
        smithery_data, _ = fetch_json("https://api.smithery.ai/servers/brave")
        self.assertIsNotNone(smithery_data)

        syncer = PassportSynchronizer()
        passport = syncer.merge_and_enrich_passport(
            package_name=pkg_name,
            ecosystem="pypi",
            pypi_data=pypi_data,
            smithery_data=smithery_data,
            is_curated_source=True,
        )
        self.assertIsNotNone(passport)
        self.assertIn("pypi", passport.sources_merged)
        self.assertIn("smithery", passport.sources_merged)

    def test_cluster4_github_awesome_mcp_raw_manifest_extraction(self) -> None:
        """Cluster 4: GitHub / Awesome-MCP repository discoveries.

        Live connection fetches raw repository manifest files directly from GitHub.
        """
        _require_live_integration()
        raw_url = "https://raw.githubusercontent.com/modelcontextprotocol/servers/main/package.json"
        pkg_json, _ = fetch_json(raw_url)
        self.assertIsNotNone(pkg_json, "GitHub raw manifest should be readable")
        self.assertIn("name", pkg_json)

        syncer = PassportSynchronizer()
        passport = syncer.merge_and_enrich_passport(
            package_name=pkg_json["name"],
            ecosystem="github",
            npm_data=pkg_json,
            is_curated_source=True,
        )
        self.assertIsNotNone(passport)


if __name__ == "__main__":
    unittest.main()
