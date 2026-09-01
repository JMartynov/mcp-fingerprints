"""High-Performance In-Memory Multi-Index and Fast-Retrieval Engine for MCP Passports."""

from __future__ import annotations

import json
import logging
import pickle
import time
from collections import defaultdict
from pathlib import Path

from mcp_fingerprints.models import (
    ServerPackageSpec,
    VersionFingerprint,
)

logger = logging.getLogger("mcp_fingerprints.index")


class FingerprintFastIndex:
    """O(1) in-memory multi-index with binary snapshot caching for fast passport lookups."""

    CACHE_FILE_NAME = ".passport_index.pickle"

    def __init__(self) -> None:
        self.packages: dict[str, ServerPackageSpec] = {}
        # O(1) Layer 1 Exact Match: canonical_hash -> list of (package_name, VersionFingerprint)
        self.by_toolset_hash: dict[str, list[tuple[str, VersionFingerprint]]] = defaultdict(list)
        # O(1) Normalized Package Name: normalized_key -> package_name
        self.by_normalized_name: dict[str, str] = {}
        # O(1) PURL index: purl -> package_name
        self.by_purl: dict[str, str] = {}
        # O(1) Alias index: alias -> set of package_names
        self.by_alias: dict[str, set[str]] = defaultdict(set)
        # Inverted Tool Name index: tool_name -> set of package_names
        self.by_tool_name: dict[str, set[str]] = defaultdict(set)

    @classmethod
    def _normalize_key(cls, val: str) -> str:
        """Create clean canonical lookup key for package names and aliases."""
        return val.strip().lower().replace("@", "").replace("/", "-").replace("_", "-")

    def register_package(self, spec: ServerPackageSpec) -> None:
        """Index a single ServerPackageSpec into all in-memory indices in O(1) time."""
        pkg_name = spec.package_name
        self.packages[pkg_name] = spec

        # 1. Normalized name index
        norm_name = self._normalize_key(pkg_name)
        self.by_normalized_name[norm_name] = pkg_name

        # Auto-index common MCP naming conventions (e.g. server-postgres -> postgres)
        parts = norm_name.split("-")
        if "server" in parts:
            idx = parts.index("server")
            if idx + 1 < len(parts):
                short_name = "-".join(parts[idx + 1 :])
                if short_name and short_name not in self.by_normalized_name:
                    self.by_normalized_name[short_name] = pkg_name

        # 2. PURL index
        if spec.purl:
            self.by_purl[spec.purl.strip().lower()] = pkg_name

        # 3. Aliases index
        for alias in spec.aliases:
            norm_alias = self._normalize_key(alias)
            self.by_alias[norm_alias].add(pkg_name)

        # 4. Version & Tool Signatures Index
        for v in spec.versions:
            self.by_toolset_hash[v.toolset_canonical_hash].append((pkg_name, v))
            for t in v.tool_signatures:
                self.by_tool_name[t.name.lower()].add(pkg_name)

    def load_from_directory(self, directory: str | Path, use_cache: bool = True) -> int:
        """Load and index all passports with binary snapshot acceleration."""
        dir_path = Path(directory)
        if not dir_path.is_dir():
            return 0

        cache_file = dir_path / self.CACHE_FILE_NAME
        start_time = time.perf_counter()

        # Check binary snapshot cache
        if use_cache and cache_file.is_file():
            try:
                # Compare cache mtime with directory mtime
                cache_mtime = cache_file.stat().st_mtime
                dir_mtime = dir_path.stat().st_mtime
                if cache_mtime >= dir_mtime:
                    cached_data = pickle.loads(cache_file.read_bytes())
                    self.packages = cached_data["packages"]
                    self.by_toolset_hash = cached_data["by_toolset_hash"]
                    self.by_normalized_name = cached_data["by_normalized_name"]
                    self.by_purl = cached_data["by_purl"]
                    self.by_alias = cached_data["by_alias"]
                    self.by_tool_name = cached_data["by_tool_name"]
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    logger.info(
                        "FingerprintFastIndex restored %d passports from binary cache in %.2f ms",
                        len(self.packages),
                        elapsed_ms,
                    )
                    return len(self.packages)
            except Exception as exc:
                logger.debug("Failed reading binary index cache: %s", exc)

        # Full disk traversal
        count = 0
        for j_file in dir_path.rglob("*.json"):
            if j_file.name in ("index.json", "sync_state.json"):
                continue
            try:
                data = json.loads(j_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "package_name" in data and "versions" in data:
                    spec = ServerPackageSpec.from_dict(data)
                    self.register_package(spec)
                    count += 1
            except Exception:
                continue

        # Save snapshot cache
        if use_cache and count > 0:
            try:
                dump_data = {
                    "packages": self.packages,
                    "by_toolset_hash": self.by_toolset_hash,
                    "by_normalized_name": self.by_normalized_name,
                    "by_purl": self.by_purl,
                    "by_alias": self.by_alias,
                    "by_tool_name": self.by_tool_name,
                }
                cache_file.write_bytes(pickle.dumps(dump_data, protocol=pickle.HIGHEST_PROTOCOL))
            except Exception as exc:
                logger.debug("Failed writing binary cache snapshot: %s", exc)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "FingerprintFastIndex indexed %d passports from disk in %.2f ms",
            len(self.packages),
            elapsed_ms,
        )
        return count

    def get_candidate_packages_for_tools(self, tool_names: list[str]) -> set[str]:
        """O(1) inverted lookup returning package names sharing observed tool names."""
        candidates: set[str] = set()
        for t_name in tool_names:
            matches = self.by_tool_name.get(t_name.lower())
            if matches:
                candidates.update(matches)
        return candidates

    def find_package_by_hint_or_alias(self, hint: str) -> ServerPackageSpec | None:
        """O(1) exact or normalized lookup for a package by name, scope, or alias."""
        if not hint:
            return None

        # 1. Direct match
        if hint in self.packages:
            return self.packages[hint]

        # 2. Normalized name match
        norm = self._normalize_key(hint)
        if norm in self.by_normalized_name:
            return self.packages.get(self.by_normalized_name[norm])

        # 3. PURL match
        if norm in self.by_purl:
            return self.packages.get(self.by_purl[norm])

        # 4. Alias match
        if norm in self.by_alias:
            alias_matches = self.by_alias[norm]
            if alias_matches:
                first_match = next(iter(alias_matches))
                return self.packages.get(first_match)

        return None
