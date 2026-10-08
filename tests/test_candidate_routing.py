import json
from pathlib import Path
from unittest.mock import MagicMock

from mcp_fingerprints.synchronizer import PassportSynchronizer
from mcp_fingerprints.models import ServerPackageSpec, ToolContractSignature

def test_candidate_routing_npm_vs_github(tmp_path: Path):
    output_dir = tmp_path / "fingerprints"
    output_dir.mkdir()

    # Create npm package without github repo
    npm_spec = ServerPackageSpec(
        package_name="test-npm-pkg",
        purl="pkg:npm/test-npm-pkg",
        ecosystem="npm",
        repository_url=None,
        sources_merged=["npm_registry"],
        versions=[]
    )
    (output_dir / "npm_pkg.json").write_text(json.dumps(npm_spec.to_dict()))

    # Create github package
    github_spec = ServerPackageSpec(
        package_name="test-github-pkg",
        purl="pkg:pypi/test-github-pkg",
        ecosystem="github",
        repository_url="https://github.com/user/test-github-pkg",
        sources_merged=["github"],
        versions=[]
    )
    (output_dir / "github_pkg.json").write_text(json.dumps(github_spec.to_dict()))

    sync = PassportSynchronizer(output_dir=output_dir)
    
    # Mock the extraction methods
    sync._extract_tools_from_npm_tarball = MagicMock(return_value=[
        ToolContractSignature(name="npm_tool", description="test", input_schema={}, canonical_hash="hash1")
    ])
    sync._extract_ast_tools_from_github = MagicMock(return_value=[
        ToolContractSignature(name="github_tool", description="test", input_schema={}, canonical_hash="hash2")
    ])
    
    # We also need to mock merge_and_enrich_passport since we don't have proper versions setup
    def merge_mock(package_name, ecosystem, existing_spec):
        # Attach a version with tool_signatures to trigger save and logger.info
        existing_spec.versions.append(MagicMock(tool_signatures=[
            ToolContractSignature(name="tool", description="desc", input_schema={}, canonical_hash="hash3")
        ]))
        return existing_spec

    sync.merge_and_enrich_passport = MagicMock(side_effect=merge_mock)

    sync.enrich_zero_tool_passports(limit=500)

    sync._extract_tools_from_npm_tarball.assert_called_once_with("test-npm-pkg")
    sync._extract_ast_tools_from_github.assert_called_once_with("test-github-pkg", "https://github.com/user/test-github-pkg")
    
    # Check state updates
    assert "test-npm-pkg" in sync.state["npm_probed_packages"]
    assert "https://github.com/user/test-github-pkg" in sync.state["ast_probed_repos"]
