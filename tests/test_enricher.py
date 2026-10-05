"""Unit tests for the VulnerabilityEnricher engine."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mcp_fingerprints.enricher import VulnerabilityEnricher
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint


class TestVulnerabilityEnricher(unittest.TestCase):
    """Test suite verifying passport enrichment with OSV advisories."""

    def test_enrich_spec_with_real_cve_range(self) -> None:
        """Verify enriching mcp-remote flags versions 0.0.8 as vulnerable and 0.1.16 as clean."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vulns_file = Path(tmpdir) / "vulns.json"
            vulns_data = {
                "vulnerabilities": {
                    "CVE-2025-6514": {
                        "id": "CVE-2025-6514",
                        "summary": "mcp-remote RCE via argument injection",
                        "database_specific": {
                            "severity": "CRITICAL",
                            "cvss_score": 9.6,
                        },
                        "affected": [
                            {
                                "package": {"name": "mcp-remote", "ecosystem": "npm"},
                                "ranges": [
                                    {
                                        "type": "SEMVER",
                                        "events": [
                                            {"introduced": "0.0.5"},
                                            {"fixed": "0.1.16"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                }
            }
            vulns_file.write_text(json.dumps(vulns_data), encoding="utf-8")

            enricher = VulnerabilityEnricher(vulns_file)

            spec = ServerPackageSpec(
                package_name="mcp-remote",
                purl="pkg:npm/mcp-remote",
                ecosystem="npm",
                versions=(
                    VersionFingerprint(
                        version="0.0.8",
                        toolset_canonical_hash="sha256:1111111111111111111111111111111111111111111111111111111111111111",
                    ),
                    VersionFingerprint(
                        version="0.1.16",
                        toolset_canonical_hash="sha256:2222222222222222222222222222222222222222222222222222222222222222",
                    ),
                ),
            )

            enriched = enricher.enrich_spec(spec)
            profile = enriched.security_profile

            self.assertTrue(profile["has_known_vulnerabilities"])
            self.assertEqual(profile["advisories_count"], 1)
            self.assertEqual(profile["max_cvss_score"], 9.6)
            self.assertEqual(profile["vulnerable_versions"], ["0.0.8"])

            adv = profile["advisories"][0]
            self.assertEqual(adv["id"], "CVE-2025-6514")
            self.assertEqual(adv["severity"], "CRITICAL")
            self.assertEqual(adv["fixed_version"], "0.1.16")
            self.assertEqual(adv["affected_versions"], ["0.0.8"])

    def test_enrich_directory_batch(self) -> None:
        """Verify enriching an entire directory updates files properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            passports_dir = Path(tmpdir) / "fingerprints"
            passports_dir.mkdir()
            vulns_file = Path(tmpdir) / "vulns.json"

            vulns_data = {
                "vulnerabilities": [
                    {
                        "id": "CVE-TEST-0001",
                        "summary": "Test advisory",
                        "database_specific": {"severity": "HIGH", "cvss_score": 8.1},
                        "affected": [
                            {
                                "package": {"name": "test-pkg", "ecosystem": "npm"},
                                "ranges": [{"type": "SEMVER", "events": [{"introduced": "1.0.0"}, {"fixed": "2.0.0"}]}],
                            }
                        ],
                    }
                ]
            }
            vulns_file.write_text(json.dumps(vulns_data), encoding="utf-8")

            # Clean spec
            clean_spec = ServerPackageSpec(
                package_name="clean-pkg",
                purl="pkg:npm/clean-pkg",
                ecosystem="npm",
                versions=(VersionFingerprint(version="1.0.0", toolset_canonical_hash="sha256:1111"),),
            )
            (passports_dir / "clean-pkg.json").write_text(json.dumps(clean_spec.to_dict()), encoding="utf-8")

            # Vulnerable spec
            vuln_spec = ServerPackageSpec(
                package_name="test-pkg",
                purl="pkg:npm/test-pkg",
                ecosystem="npm",
                versions=(VersionFingerprint(version="1.5.0", toolset_canonical_hash="sha256:2222"),),
            )
            (passports_dir / "test-pkg.json").write_text(json.dumps(vuln_spec.to_dict()), encoding="utf-8")

            enricher = VulnerabilityEnricher(vulns_file)
            total, with_vulns = enricher.enrich_directory(passports_dir)

            self.assertEqual(total, 2)
            self.assertEqual(with_vulns, 1)

            # Check clean file
            clean_enriched = json.loads((passports_dir / "clean-pkg.json").read_text(encoding="utf-8"))
            self.assertFalse(clean_enriched["security_profile"]["has_known_vulnerabilities"])

            # Check vuln file
            vuln_enriched = json.loads((passports_dir / "test-pkg.json").read_text(encoding="utf-8"))
            self.assertTrue(vuln_enriched["security_profile"]["has_known_vulnerabilities"])
            self.assertEqual(vuln_enriched["security_profile"]["max_cvss_score"], 8.1)


if __name__ == "__main__":
    unittest.main()
