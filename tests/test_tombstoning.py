import json
import urllib.error
from unittest.mock import patch
from pathlib import Path

import pytest
from mcp_fingerprints.canonicalizer import build_version_fingerprint
from mcp_fingerprints.crawler import FingerprintGenerator
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.synchronizer import PassportSynchronizer, ArchiveNotFoundError


def test_npm_404_raises_archive_not_found(tmp_path: Path):
    sync = PassportSynchronizer(output_dir=tmp_path)
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://registry.npmjs.org/deleted-pkg",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        with pytest.raises(ArchiveNotFoundError):
            sync._extract_tools_from_npm_tarball("deleted-pkg")


def test_pypi_404_raises_archive_not_found(tmp_path: Path):
    sync = PassportSynchronizer(output_dir=tmp_path)
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://pypi.org/pypi/deleted-pkg/json",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        with pytest.raises(ArchiveNotFoundError):
            sync._extract_tools_from_pypi_package("deleted-pkg")


def test_github_404_raises_archive_not_found(tmp_path: Path):
    sync = PassportSynchronizer(output_dir=tmp_path)
    with patch("urllib.request.urlopen") as mock_urlopen:
        # Both trees and repo check fail with 404
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/repos/owner/deleted",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        with pytest.raises(ArchiveNotFoundError):
            sync._extract_ast_tools_from_github("owner/deleted", repo_url="https://github.com/owner/deleted")


def test_merge_and_enrich_handles_archive_not_found(tmp_path: Path):
    sync = PassportSynchronizer(output_dir=tmp_path)
    existing_spec = ServerPackageSpec(
        package_name="test-org/deleted-repo",
        purl="pkg:github/test-org/deleted-repo",
        ecosystem="github",
        repository_url="https://github.com/test-org/deleted-repo",
    )
    with patch.object(sync, "_extract_ast_tools_from_github", side_effect=ArchiveNotFoundError("Repo 404")):
        spec = sync.merge_and_enrich_passport(
            package_name="test-org/deleted-repo",
            ecosystem="github",
            existing_spec=existing_spec,
        )
        assert spec is not None
        assert len(spec.versions) == 1
        caps = spec.versions[0].capabilities
        assert caps.get("is_archived") is True
        assert caps.get("http_status") == 404
        assert "404" in caps.get("archival_reason", "")


def test_hydrate_zero_tool_servers_marks_tombstone(tmp_path: Path):
    sync = PassportSynchronizer(output_dir=tmp_path)
    v_fp = build_version_fingerprint(version="1.0.0", tools=[])
    spec = ServerPackageSpec(
        package_name="ghost-pkg",
        purl="pkg:npm/ghost-pkg",
        ecosystem="npm",
        description="Ghost server",
        versions=(v_fp,),
    )
    pkg_file = tmp_path / "npm" / "ghost-pkg.json"
    pkg_file.parent.mkdir(parents=True, exist_ok=True)
    FingerprintGenerator.save_spec_to_file(spec, pkg_file)

    with patch.object(sync, "_extract_tools_from_npm_tarball", side_effect=ArchiveNotFoundError("npm 404")):
        enriched = sync.enrich_zero_tool_passports(limit=10, max_workers=1)
        assert enriched == 1

    saved = json.loads(pkg_file.read_text(encoding="utf-8"))
    ver_caps = saved["versions"][0]["capabilities"]
    assert ver_caps.get("is_unpublished") is True
    assert ver_caps.get("http_status") == 404
