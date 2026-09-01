"""Snapshot builder compiling individual MCP passport JSONs into a consolidated compressed archive."""

from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("mcp_fingerprints.snapshot")


def build_snapshot(
    data_dir: str | Path = "data/fingerprints",
    output_gz: str | Path = "passports.json.gz",
    output_json: str | Path | None = None,
) -> dict[str, Any]:
    """Compile all passport JSON files in data_dir into a single consolidated JSON/GZ snapshot."""
    dir_path = Path(data_dir)
    passports: dict[str, Any] = {}

    for j_file in sorted(dir_path.rglob("*.json")):
        if j_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
            continue
        try:
            content = json.loads(j_file.read_text(encoding="utf-8"))
            if isinstance(content, dict) and "package_name" in content:
                passports[content["package_name"]] = content
        except Exception as exc:
            logger.warning("Error reading %s: %s", j_file, exc)

    payload = {
        "version": "1.0.0",
        "total_passports": len(passports),
        "passports": passports,
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=None).encode("utf-8")

    gz_path = Path(output_gz)
    with gzip.open(gz_path, "wb", compresslevel=9) as f:
        f.write(encoded)

    if output_json:
        Path(output_json).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    gz_size_kb = gz_path.stat().st_size / 1024.0
    logger.info(
        "Successfully compiled snapshot with %d passports into %s (%.2f KB)",
        len(passports),
        gz_path,
        gz_size_kb,
    )
    return {
        "total_passports": len(passports),
        "snapshot_path": str(gz_path),
        "size_kb": gz_size_kb,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/fingerprints"
    out_gz = sys.argv[2] if len(sys.argv) > 2 else "passports.json.gz"
    res = build_snapshot(data_dir=data_dir, output_gz=out_gz)
    print(f"Compiled {res['total_passports']} passports ({res['size_kb']:.2f} KB) -> {res['snapshot_path']}")
