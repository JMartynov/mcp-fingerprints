"""Regression tests for Phase 1 code review bug fixes."""

import gzip
import json
from pathlib import Path

from mcp_fingerprints.db_engine import EphemeralDBEngine
from mcp_fingerprints.index import FingerprintFastIndex
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.reporter import iter_passports
from mcp_fingerprints.sbom_exporter import CycloneDXExporter


def test_iter_passports_gz_dict_format(tmp_path: Path) -> None:
    """iter_passports yields passport dicts when .json.gz stores passports as a dict."""
    gz_path = tmp_path / "passports.json.gz"
    payload = {
        "passports": {
            "pkg-a": {"package_name": "pkg-a", "ecosystem": "npm", "versions": []},
            "pkg-b": {"package_name": "pkg-b", "ecosystem": "pypi", "versions": []},
        }
    }
    with gzip.open(gz_path, "wt", encoding="utf-8") as f:
        json.dump(payload, f)

    items = list(iter_passports(gz_path))
    assert len(items) == 2
    assert {item["package_name"] for item in items} == {"pkg-a", "pkg-b"}


def test_index_find_package_by_purl_with_scope_and_slash() -> None:
    """find_package_by_hint_or_alias matches PURLs containing '@' and '/'."""
    idx = FingerprintFastIndex()
    spec = ServerPackageSpec(
        package_name="@modelcontextprotocol/server-postgres",
        purl="pkg:npm/@modelcontextprotocol/server-postgres",
        ecosystem="npm",
        versions=(),
    )
    idx.register_package(spec)

    found = idx.find_package_by_hint_or_alias("pkg:npm/@modelcontextprotocol/server-postgres")
    assert found is not None
    assert found.package_name == "@modelcontextprotocol/server-postgres"


def test_db_engine_find_by_hash_canonical_versions_key(tmp_path: Path) -> None:
    """find_by_hash locates canonical passports using the 'versions' key."""
    fp_dir = tmp_path / "fingerprints"
    fp_dir.mkdir()
    passport = {
        "package_name": "demo-server",
        "ecosystem": "npm",
        "purl": "pkg:npm/demo-server",
        "versions": [
            {
                "version": "1.0.0",
                "toolset_canonical_hash": "sha256:abc123",
                "tool_signatures": [],
            }
        ],
    }
    (fp_dir / "demo-server.json").write_text(json.dumps(passport), encoding="utf-8")

    engine = EphemeralDBEngine(data_dir=fp_dir, use_cache=False)
    res = engine.find_by_hash("sha256:abc123")
    assert res is not None
    assert res["package_name"] == "demo-server"


def test_sbom_exporter_semver_ordering() -> None:
    """_get_latest_version uses semver ordering so 0.10.0 > 0.9.0."""
    v9 = VersionFingerprint(
        version="0.9.0",
        toolset_canonical_hash="h9",
        tool_signatures=(),
    )
    v10 = VersionFingerprint(
        version="0.10.0",
        toolset_canonical_hash="h10",
        tool_signatures=(),
    )
    spec = ServerPackageSpec(
        package_name="demo",
        purl="pkg:pypi/demo",
        ecosystem="pypi",
        versions=(v10, v9),
    )
    latest = CycloneDXExporter._get_latest_version(spec)
    assert latest is not None
    assert latest.version == "0.10.0"
