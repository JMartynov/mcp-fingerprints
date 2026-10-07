import json
import logging
import threading
from pathlib import Path
from unittest import mock
import unittest
import tempfile

from mcp_fingerprints.synchronizer import PassportSynchronizer
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.models import ToolContractSignature

class TestParallelSynchronizer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.state_file = self.output_dir / "sync_state.json"
        
        # Create 20 mock zero-tool passports
        for i in range(20):
            spec = ServerPackageSpec(
                package_name=f"test-owner/repo-{i}",
                purl=f"pkg:github/test-owner/repo-{i}",
                ecosystem="github",
                repository_url=f"https://github.com/test-owner/repo-{i}",
                versions=[VersionFingerprint(version="1.0.0", toolset_canonical_hash="testhash")]
            )
            filepath = self.output_dir / f"test-owner_repo-{i}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(spec.to_dict(), f)

    def tearDown(self):
        self.temp_dir.cleanup()

    @mock.patch("mcp_fingerprints.synchronizer.PassportSynchronizer._extract_ast_tools_from_github")
    @mock.patch("mcp_fingerprints.synchronizer.PassportSynchronizer.merge_and_enrich_passport")
    def test_enrich_zero_tool_passports_parallel(self, mock_merge, mock_extract):
        # We simulate that extract takes a little bit of time, and 10 of them return tools, 10 return None
        lock = threading.Lock()
        counter = 0

        def extract_side_effect(package_name, check_repo):
            nonlocal counter
            with lock:
                current = counter
                counter += 1
            if current % 2 == 0:
                return [{"name": f"tool_{current}", "description": "A tool"}]
            return []

        def merge_side_effect(package_name, ecosystem, existing_spec):
            if current := [t for t in mock_extract.mock_calls if t.args[0] == package_name]:
                # If extract was called and returned tools, simulate merged_spec with tools
                mock_sig = ToolContractSignature(name="test", description="test", canonical_hash="test")
                
                spec = ServerPackageSpec(
                    package_name=existing_spec.package_name,
                    purl=existing_spec.purl,
                    ecosystem=existing_spec.ecosystem,
                    repository_url=existing_spec.repository_url,
                    versions=[VersionFingerprint(version="1.0.0", toolset_canonical_hash="testhash", tool_signatures=(mock_sig,))]
                )
                return spec
            return existing_spec

        mock_extract.side_effect = extract_side_effect
        mock_merge.side_effect = merge_side_effect

        sync = PassportSynchronizer(output_dir=self.output_dir, state_file=self.state_file)
        
        enriched_count = sync.enrich_zero_tool_passports(limit=250, max_workers=5)
        
        # 10 should be enriched
        self.assertEqual(enriched_count, 10)
        
        # State should be updated with all 20
        with open(self.state_file, "r") as f:
            state = json.load(f)
        
        ast_probed_repos = state.get("ast_probed_repos", [])
        self.assertEqual(len(ast_probed_repos), 20)
        for i in range(20):
            self.assertIn(f"https://github.com/test-owner/repo-{i}", ast_probed_repos)
            
        # Verify enriched files actually have tools
        enriched_files = 0
        for i in range(20):
            filepath = self.output_dir / f"test-owner_repo-{i}.json"
            with open(filepath, "r") as f:
                data = json.load(f)
            if data["versions"][0].get("tool_signatures"):
                enriched_files += 1
        
        self.assertEqual(enriched_files, 10)

if __name__ == "__main__":
    unittest.main()
