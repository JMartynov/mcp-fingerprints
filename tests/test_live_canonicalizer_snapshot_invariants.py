import pytest
import os
import json
import random
import time
from pathlib import Path
from dataclasses import FrozenInstanceError

from mcp_fingerprints.canonicalizer import canonicalize_json, compute_toolset_canonical_hash, build_version_fingerprint
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.cache import PassportCacheEngine
from mcp_fingerprints.db_engine import EphemeralDBEngine
from mcp_fingerprints.snapshot import build_snapshot
from mcp_fingerprints.data_loader import load_passports


def test_canonical_hash_determinism():
    base_tool = {
        "name": "test_tool",
        "description": "A test tool",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prop1": {"type": "string", "description": "prop1 desc"},
                "prop2": {"type": "integer", "description": "prop2 desc"},
                "prop3": {"type": "boolean", "description": "prop3 desc"},
            },
            "required": ["prop1", "prop2"]
        }
    }

    reference_hash = compute_toolset_canonical_hash([base_tool])
    reference_canonical = canonicalize_json(base_tool)

    for i in range(500):
        # Permute property order
        props = list(base_tool["inputSchema"]["properties"].items())
        random.shuffle(props)
        shuffled_props = dict(props)

        # Shuffle required
        reqs = list(base_tool["inputSchema"]["required"])
        random.shuffle(reqs)
        
        varied_tool = {
            "name": base_tool["name"],
            "description": base_tool["description"] + (" " * (i % 3)),
            "inputSchema": {
                "type": "object",
                "properties": shuffled_props,
                "required": reqs
            }
        }
        
        assert compute_toolset_canonical_hash([varied_tool]) == reference_hash


def test_pure_structural_domain_isolation():
    # Test that security fields are not present in models
    data = {
        "package_name": "test-pkg",
        "purl": "pkg:test/test-pkg",
        "ecosystem": "test",
        "vulnerabilities": [{"id": "CVE-2024-1234"}],
        "cve": "CVE-2024-1234",
        "security_profile": {"risk": "high"}
    }
    
    spec = ServerPackageSpec.from_dict(data)
    assert not hasattr(spec, "vulnerabilities")
    assert not hasattr(spec, "cve")
    assert not hasattr(spec, "security_profile")
    
    data_version = {
        "version": "1.0.0",
        "toolset_canonical_hash": "hash123",
        "vulnerabilities": [{"id": "CVE-2024-1234"}],
        "cve": "CVE-2024-1234",
        "security_profile": {"risk": "high"}
    }
    
    vf = VersionFingerprint.from_dict(data_version)
    assert not hasattr(vf, "vulnerabilities")
    assert not hasattr(vf, "cve")
    assert not hasattr(vf, "security_profile")


def test_two_tier_cache_coherency(tmp_path):
    cache_file = tmp_path / "cache.json"
    engine = PassportCacheEngine(cache_file=str(cache_file))
    
    test_file = tmp_path / "test_passport.json"
    test_data = {"package_name": "test-cache", "version": "1.0.0"}
    test_file.write_text(json.dumps(test_data))
    
    # Init cache
    engine.update_cache(test_file, test_data)
    
    # Tier 1 hit
    hit, data = engine.check_cache(test_file)
    assert hit is True
    assert data == test_data
    
    # Simulate mtime change without content change
    time.sleep(0.01) # to ensure mtime is different
    os.utime(test_file, None)
    
    # Verify Tier 2 fallback (SHA-256 match, mtime mismatch)
    hit, data = engine.check_cache(test_file)
    assert hit is True
    assert data == test_data


def test_ephemeral_db_engine_fallbacks(tmp_path, monkeypatch):
    # Mock import duckdb to fail
    import sys
    monkeypatch.setitem(sys.modules, "duckdb", None)
    from mcp_fingerprints import db_engine
    monkeypatch.setattr(db_engine, "DUCKDB_AVAILABLE", False)
    
    # Create some mock JSONs
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    for i in range(3):
        (data_dir / f"pkg{i}.json").write_text(json.dumps({
            "package_name": f"test-pkg-{i}",
            "description": f"description {i}"
        }))
        
    engine = EphemeralDBEngine(data_dir=data_dir, use_cache=False)
    assert engine._duck_conn is None
    
    # Depending on how the fallback is implemented, it might use sqlite or dict
    # Test basic search
    res = engine.search_packages("pkg-1")
    assert len(res) == 1
    assert res[0]["package_name"] == "test-pkg-1"
    
    res_all = engine.search_packages("test-pkg")
    assert len(res_all) == 3


def test_snapshot_compilation(tmp_path, monkeypatch):
    data_dir = tmp_path / "fingerprints"
    data_dir.mkdir()
    
    # 50 mock passports
    for i in range(50):
        (data_dir / f"pkg_{i}.json").write_text(json.dumps({
            "package_name": f"pkg_{i}",
            "purl": f"pkg:test/pkg_{i}",
            "ecosystem": "test",
            "versions": [{"version": "1.0.0", "toolset_canonical_hash": "hash123"}]
        }))
        
    out_gz = tmp_path / "passports.json.gz"
    
    # Build snapshot
    res = build_snapshot(data_dir=str(data_dir), output_gz=str(out_gz), use_cache=False)
    assert res["total_passports"] == 50
    assert out_gz.exists()
    
    # Mock get_passports_path to return our custom out_gz path
    from mcp_fingerprints import data_loader
    def mock_get_passports_path(download_if_missing=True):
        return out_gz
        
    monkeypatch.setattr(data_loader, "get_passports_path", mock_get_passports_path)
    
    # Test load_passports uses streaming decompression successfully
    passports = data_loader.load_passports()
    assert len(passports) == 50
    assert "pkg_0" in passports
    assert passports["pkg_0"].package_name == "pkg_0"

