import json
import pytest
from pathlib import Path
from mcp_fingerprints.partitioner import (
    partition_path_for_package,
    migrate_to_partitioned_layout,
    scan_partitioned_fingerprints,
)


def test_partition_path_for_package():
    # Test standard PyPI package
    path = partition_path_for_package("mcp-server-git", "pypi")
    assert path == Path("pypi/m/mcp-server-git.json")

    # Test npm namespaced package
    path = partition_path_for_package("@modelcontextprotocol/server-postgres", "npm")
    assert path == Path("npm/@/@modelcontextprotocol__server-postgres.json")

    # Test other ecosystem and numbers
    path = partition_path_for_package("1password", "homebrew")
    assert path == Path("homebrew/1/1password.json")

    # Test non-alphanumeric first char
    path = partition_path_for_package("_internal", "custom")
    assert path == Path("custom/_/_internal.json")


def test_migrate_to_partitioned_layout(tmp_path):
    data_dir = tmp_path / "fingerprints"
    data_dir.mkdir()

    # Create flat files
    pypi_pkg = {"package_name": "mcp-server-git", "ecosystem": "pypi", "version": "1.0"}
    npm_pkg = {"package_name": "@mcp/server-db", "ecosystem": "npm", "version": "2.0"}
    invalid_pkg = {"version": "3.0"}  # Missing required fields

    (data_dir / "mcp-server-git.json").write_text(json.dumps(pypi_pkg))
    (data_dir / "mcp_server_db.json").write_text(json.dumps(npm_pkg))
    (data_dir / "invalid.json").write_text(json.dumps(invalid_pkg))

    # Run migration
    migrate_to_partitioned_layout(data_dir)

    # Assert partitioned layout
    assert (data_dir / "pypi/m/mcp-server-git.json").exists()
    assert (data_dir / "npm/@/@mcp__server-db.json").exists()

    # Assert invalid is left flat or skipped correctly
    assert (data_dir / "invalid.json").exists()

    # Assert flat valid files are gone
    assert not (data_dir / "mcp-server-git.json").exists()
    assert not (data_dir / "mcp_server_db.json").exists()

    # Test scan
    found_files = list(scan_partitioned_fingerprints(data_dir))
    assert len(found_files) == 3
    assert data_dir / "pypi/m/mcp-server-git.json" in found_files
    assert data_dir / "npm/@/@mcp__server-db.json" in found_files
    assert data_dir / "invalid.json" in found_files


def test_gitignore_contains_rules():
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        assert "*.duckdb" in content
        assert "*.db" in content
        assert "*.sqlite" in content
        assert ".cache/" in content


from mcp_fingerprints.db_engine import EphemeralDBEngine, benchmark_query_performance


def test_db_engine_with_duckdb(tmp_path):
    from mcp_fingerprints.db_engine import DUCKDB_AVAILABLE

    if not DUCKDB_AVAILABLE:
        pytest.skip("DuckDB is not available")

    data_dir = tmp_path / "fingerprints"
    data_dir.mkdir()

    pkg_data = {
        "package_name": "test-pkg",
        "description": "A test package",
        "version_fingerprints": [
            {"toolset_canonical_hash": "hash000"},
            {"toolset_canonical_hash": "hash123"},
        ],
    }

    (data_dir / "test-pkg.json").write_text(json.dumps(pkg_data))

    engine = EphemeralDBEngine(data_dir)

    stats = engine.get_stats()
    assert stats["engine"] == "duckdb"
    assert stats["storage"] == ":memory:"
    assert stats["package_count"] == 1

    # Test search
    res = engine.search_packages("test")
    assert len(res) == 1
    assert res[0]["package_name"] == "test-pkg"

    # Test search description
    res = engine.search_packages("A test package")
    assert len(res) == 1

    # Test find_by_hash secondary element
    res = engine.find_by_hash("hash123")
    assert res is not None
    assert res["package_name"] == "test-pkg"

    # Test get_package
    pkg = engine.get_package("test-pkg")
    assert pkg is not None
    assert pkg["package_name"] == "test-pkg"

    # Test execute_query
    res = engine.execute_query("SELECT count(*) as count FROM fingerprints")
    assert res[0]["count"] == 1

    engine.close()


def test_db_engine_fallback_simulated(tmp_path, monkeypatch):
    import mcp_fingerprints.db_engine as db_mod

    monkeypatch.setattr(db_mod, "DUCKDB_AVAILABLE", False)

    data_dir = tmp_path / "fingerprints"
    data_dir.mkdir()

    pkg_data = {
        "package_name": "test-fallback",
        "description": "Fallback package",
        "version_fingerprints": [
            {"toolset_canonical_hash": "hash888"},
            {"toolset_canonical_hash": "hash999"},
        ],
    }
    (data_dir / "fallback.json").write_text(json.dumps(pkg_data))

    engine = db_mod.EphemeralDBEngine(
        data_dir, use_cache=True, cache_dir=tmp_path / ".cache"
    )

    stats = engine.get_stats()
    assert stats["engine"] == "sqlite"
    assert stats["package_count"] == 1

    res = engine.search_packages("Fallback")
    assert len(res) == 1
    assert res[0]["package_name"] == "test-fallback"

    pkg = engine.get_package("test-fallback")
    assert pkg["package_name"] == "test-fallback"

    # test by hash
    hash_pkg = engine.find_by_hash("hash999")
    assert hash_pkg["package_name"] == "test-fallback"

    engine.close()


def test_benchmark_performance(tmp_path):
    data_dir = tmp_path / "fingerprints"
    data_dir.mkdir()

    # generate a few fake files
    for i in range(10):
        (data_dir / f"pkg_{i}.json").write_text(
            json.dumps({"package_name": f"pkg_{i}", "description": "desc"})
        )

    (data_dir / "target_benchmark_package.json").write_text(
        json.dumps({"package_name": "target_benchmark_package", "description": "desc"})
    )

    stats = benchmark_query_performance(data_dir)
    assert "baseline_scan_seconds" in stats
    assert "db_init_seconds" in stats
    assert "db_query_seconds" in stats
