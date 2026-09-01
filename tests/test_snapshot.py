import gzip
import json
from pathlib import Path
from mcp_fingerprints.snapshot import build_snapshot


def test_build_snapshot(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test_pkg.json").write_text(
        json.dumps({
            "package_name": "@test/mcp-server",
            "purl": "pkg:npm/%40test/mcp-server",
            "versions": []
        }),
        encoding="utf-8"
    )
    
    out_gz = tmp_path / "passports.json.gz"
    res = build_snapshot(data_dir=data_dir, output_gz=out_gz)
    
    assert res["total_passports"] == 1
    assert out_gz.is_file()
    
    with gzip.open(out_gz, "rt", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_passports"] == 1
    assert "@test/mcp-server" in data["passports"]
