"""Two-Tier SHA-256 Content-Addressable Cache Engine for fast passport validation/snapshot."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("mcp_fingerprints.cache")


class PassportCacheEngine:
    def __init__(self, cache_file: str | Path = "data/.passport_cache.json") -> None:
        self.cache_file = Path(cache_file)
        self.cache_data: dict[str, dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                self.cache_data = json.loads(
                    self.cache_file.read_text(encoding="utf-8")
                )
            except Exception as e:
                logger.warning(
                    f"Failed to read cache {self.cache_file}: {e}. Starting fresh."
                )
                self.cache_data = {}

    def save_cache(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = self.cache_file.with_name(f"{self.cache_file.name}.tmp")
            tmp_file.write_text(json.dumps(self.cache_data), encoding="utf-8")
            os.replace(tmp_file, self.cache_file)
        except Exception as e:
            logger.warning(f"Failed to save cache {self.cache_file}: {e}")

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
        except Exception as e:
            logger.warning(f"Failed to read file for hash {file_path}: {e}")
            return ""
        return h.hexdigest()

    def prune(self, current_files: set[str]) -> None:
        """Remove entries that no longer exist on disk."""
        keys_to_remove = set(self.cache_data.keys()) - current_files
        for key in keys_to_remove:
            del self.cache_data[key]
        if keys_to_remove:
            self.save_cache()

    def check_cache(self, file_path: Path) -> tuple[bool, dict[str, Any] | None]:
        """Check cache. Returns (is_hit, cached_data)."""
        abs_path_str = str(file_path.resolve())
        try:
            stat = file_path.stat()
        except OSError:
            return False, None

        current_size = stat.st_size
        current_mtime = stat.st_mtime_ns

        cached_entry = self.cache_data.get(abs_path_str)
        if not cached_entry:
            return False, None

        # Tier 1: Check size and mtime
        if (
            cached_entry.get("st_size") == current_size
            and cached_entry.get("st_mtime_ns") == current_mtime
        ):
            return True, cached_entry.get("data")

        # Tier 2: SHA-256 Digest Verification
        current_hash = self._compute_sha256(file_path)
        if cached_entry.get("sha256") == current_hash:
            # Hash matches (e.g. touch), update mtime and size
            cached_entry["st_size"] = current_size
            cached_entry["st_mtime_ns"] = current_mtime
            # Return hit, but caller should save eventually
            return True, cached_entry.get("data")

        return False, None

    def update_cache(self, file_path: Path, data: dict[str, Any] | None, known_hash: str | None = None) -> None:
        """Update cache for a file, using provided hash if known to save I/O."""
        abs_path_str = str(file_path.resolve())
        try:
            stat = file_path.stat()
            current_size = stat.st_size
            current_mtime = stat.st_mtime_ns
            current_hash = known_hash if known_hash else self._compute_sha256(file_path)
        except OSError:
            return

        self.cache_data[abs_path_str] = {
            "st_size": current_size,
            "st_mtime_ns": current_mtime,
            "sha256": current_hash,
            "data": data,
        }
