import json
import tempfile
import time
from pathlib import Path

from mcp_fingerprints.cache import PassportCacheEngine


def test_cache_miss_then_hit():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        cache_path = tdp / ".cache.json"
        engine = PassportCacheEngine(cache_path)

        # Create a mock file
        mock_file = tdp / "mock.json"
        data = {"package_name": "test-pkg", "tool_signatures": []}
        mock_file.write_text(json.dumps(data), encoding="utf-8")

        # Initial check should be a miss
        is_hit, cached_data = engine.check_cache(mock_file)
        assert not is_hit
        assert cached_data is None

        # Update cache
        engine.update_cache(mock_file, data)
        engine.save_cache()

        # Check cache again, should hit
        engine2 = PassportCacheEngine(cache_path)
        is_hit, cached_data = engine2.check_cache(mock_file)
        assert is_hit
        assert cached_data == data


def test_cache_prune():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        cache_path = tdp / ".cache.json"
        engine = PassportCacheEngine(cache_path)

        mock_file = tdp / "mock.json"
        mock_file.write_text("{}", encoding="utf-8")
        engine.update_cache(mock_file, {})
        engine.save_cache()

        assert len(engine.cache_data) == 1

        # Prune with empty current files
        engine.prune(set())
        assert len(engine.cache_data) == 0


def test_cache_sha256_hit():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        cache_path = tdp / ".cache.json"
        engine = PassportCacheEngine(cache_path)

        mock_file = tdp / "mock.json"
        data = {"test": 123}
        mock_file.write_text(json.dumps(data), encoding="utf-8")

        engine.update_cache(mock_file, data)
        engine.save_cache()

        # "Touch" the file to change its mtime but keep content same
        time.sleep(0.01)
        mock_file.write_text(json.dumps(data), encoding="utf-8")

        # Check cache
        is_hit, cached_data = engine.check_cache(mock_file)
        assert is_hit, "Should be a hit based on SHA-256 fallback"


def test_cache_sha256_miss():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        cache_path = tdp / ".cache.json"
        engine = PassportCacheEngine(cache_path)

        mock_file = tdp / "mock.json"
        mock_file.write_text(json.dumps({"test": 123}), encoding="utf-8")

        engine.update_cache(mock_file, {"test": 123})
        engine.save_cache()

        # Modify content (different size to ensure it misses size cache too, or just wait slightly so mtime changes, or both)
        import time

        time.sleep(0.01)
        mock_file.write_text(
            json.dumps({"test": 456, "extra": "field"}), encoding="utf-8"
        )

        # Check cache
        is_hit, cached_data = engine.check_cache(mock_file)
        assert not is_hit, "Should miss because content changed"
