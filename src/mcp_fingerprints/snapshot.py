"""Snapshot builder compiling individual MCP passport JSONs into a consolidated compressed archive."""

from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("mcp_fingerprints.snapshot")


def _read_snapshot_chunk(chunk: list[Path]) -> tuple[dict[str, dict[str, Any]], list[tuple[Path, dict[str, Any], str]]]:
    """Reads a chunk of JSON passports.
    Returns: (passports_dict, [(Path, parsed_dict, sha256_hash)])
    """
    import hashlib
    passports: dict[str, dict[str, Any]] = {}
    files_with_hash = []
    for j_file in chunk:
        try:
            raw_text = j_file.read_text(encoding="utf-8")
            content = json.loads(raw_text)
            if isinstance(content, dict) and "package_name" in content:
                passports[content["package_name"]] = content
                
                h = hashlib.sha256()
                h.update(raw_text.encode("utf-8"))
                files_with_hash.append((j_file, content, h.hexdigest()))
        except Exception as exc:
            logger.warning("Error reading %s: %s", j_file, exc)
    return passports, files_with_hash


def build_snapshot(
    data_dir: str | Path = "data/fingerprints",
    output_gz: str | Path = "passports.json.gz",
    output_json: str | Path | None = None,
    use_cache: bool = True,
    max_workers: int | None = None,
) -> dict[str, Any]:
    """Compile all passport JSON files in data_dir into a single consolidated JSON/GZ snapshot."""
    import concurrent.futures
    import os
    import time
    from mcp_fingerprints.cache import PassportCacheEngine

    start_time = time.time()
    dir_path = Path(data_dir)

    cache_engine = None
    if use_cache:
        cache_engine = PassportCacheEngine()

    passports: dict[str, Any] = {}
    files_to_read = []

    cached_count = 0
    read_count = 0

    for j_file in sorted(dir_path.rglob("*.json")):
        if j_file.name in (
            "sync_state.json",
            "index.json",
            ".passport_index.pickle",
            ".passport_cache.json",
        ):
            continue

        if use_cache and cache_engine:
            is_hit, cached_data = cache_engine.check_cache(j_file)
            if is_hit and cached_data:
                if "package_name" in cached_data:
                    passports[cached_data["package_name"]] = cached_data
                cached_count += 1
                continue

        files_to_read.append(j_file)

    if files_to_read:
        chunk_size = 50
        chunks = [
            files_to_read[i : i + chunk_size]
            for i in range(0, len(files_to_read), chunk_size)
        ]
        workers = max_workers if max_workers is not None else os.cpu_count()
        
        valid_files_to_cache = []
        if workers == 1:
            for chunk in chunks:
                chunk_passports, files_with_hash = _read_snapshot_chunk(chunk)
                passports.update(chunk_passports)
                read_count += len(chunk_passports)
                valid_files_to_cache.extend(files_with_hash)
        else:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers
            ) as executor:
                futures = [
                    executor.submit(_read_snapshot_chunk, chunk) for chunk in chunks
                ]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        chunk_passports, files_with_hash = future.result()
                        passports.update(chunk_passports)
                        read_count += len(chunk_passports)
                        valid_files_to_cache.extend(files_with_hash)
                    except Exception as e:
                        logger.warning(f"Worker process failed: {e}")

        # update cache for newly read files if needed
        # since we want to cache the parsed dictionary for faster snapshotting
        if use_cache and cache_engine:
            for j_file, content, h_val in valid_files_to_cache:
                cache_engine.update_cache(j_file, content, known_hash=h_val)
            cache_engine.save_cache()

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
        Path(output_json).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    gz_size_kb = gz_path.stat().st_size / 1024.0
    elapsed = time.time() - start_time
    logger.info(
        "Successfully compiled snapshot with %d passports into %s (%.2f KB) in %.2fs",
        len(passports),
        gz_path,
        gz_size_kb,
        elapsed,
    )
    return {
        "total_passports": len(passports),
        "snapshot_path": str(gz_path),
        "size_kb": gz_size_kb,
        "cached": cached_count,
        "read": read_count,
        "time_s": elapsed,
    }


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/fingerprints"
    out_gz = sys.argv[2] if len(sys.argv) > 2 else "passports.json.gz"
    res = build_snapshot(data_dir=data_dir, output_gz=out_gz)
    print(
        f"Compiled {res['total_passports']} passports ({res['size_kb']:.2f} KB) -> {res['snapshot_path']}"
    )
