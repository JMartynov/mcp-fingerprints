import json
import tempfile
from pathlib import Path

from mcp_fingerprints.schema_validator import PassportSchemaValidator


def create_valid_passport(path: Path, pkg_name: str):
    data = {
        "package_name": pkg_name,
        "purl": f"pkg:npm/{pkg_name}",
        "ecosystem": "npm",
        "versions": [
            {
                "version": "1.0.0",
                "toolset_canonical_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "tool_signatures": [],
            }
        ],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_parallel_validator():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        for i in range(10):
            create_valid_passport(tdp / f"valid_{i}.json", f"pkg-{i}")

        invalid_file = tdp / "invalid.json"
        invalid_file.write_text('{"missing": "fields"}', encoding="utf-8")

        # First run (no cache file exists)
        valid, invalid, errors, stats = PassportSchemaValidator.validate_directory(
            tdp, use_cache=True, max_workers=2
        )
        assert valid == 10
        assert invalid == 1
        assert stats["cached"] == 0
        assert stats["validated"] == 11

        # Second run (should use cache)
        valid, invalid, errors, stats = PassportSchemaValidator.validate_directory(
            tdp, use_cache=True, max_workers=2
        )
        assert valid == 10
        assert invalid == 1
        assert stats["cached"] == 10
        # The invalid file should be re-validated because we only cached valid files
        assert stats["validated"] == 1

        # Third run with --no-cache equivalent
        valid, invalid, errors, stats = PassportSchemaValidator.validate_directory(
            tdp, use_cache=False, max_workers=2
        )
        assert valid == 10
        assert invalid == 1
        assert stats["cached"] == 0
        assert stats["validated"] == 11

        # Single worker fallback
        valid, invalid, errors, stats = PassportSchemaValidator.validate_directory(
            tdp, use_cache=False, max_workers=1
        )
        assert valid == 10
        assert invalid == 1
        assert stats["cached"] == 0
        assert stats["validated"] == 11
