"""Multi-tier data loader and local cache manager for MCP server passports."""

from __future__ import annotations

import gzip
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Dict

from mcp_fingerprints.models import ServerPackageSpec

logger = logging.getLogger("mcp_fingerprints.data_loader")

CACHE_DIR = Path.home() / ".cache" / "mcp-fingerprints"
SNAPSHOT_FILENAME = "passports.json.gz"
REMOTE_SNAPSHOT_URL = (
    "https://raw.githubusercontent.com/jmartynov/mcp-fingerprints/main/passports.json.gz"
)


def get_passports_path(download_if_missing: bool = True) -> Path:
    """Resolve the path to passports dataset via multi-tier fallback.

    Tier 1: Local repository checkout (passports.json.gz or data/fingerprints).
    Tier 2: User cache directory (~/.cache/mcp-fingerprints/passports.json.gz).
    Tier 3: On-demand download from GitHub repository CDN.
    """
    # 1. Local workspace / checkout
    repo_gz = Path(SNAPSHOT_FILENAME)
    if repo_gz.is_file():
        return repo_gz.resolve()

    data_dir = Path("data/fingerprints")
    if data_dir.is_dir():
        return data_dir.resolve()

    # 2. User cache directory
    cached_gz = CACHE_DIR / SNAPSHOT_FILENAME
    if cached_gz.is_file() and cached_gz.stat().st_size > 1024:
        return cached_gz

    # 3. On-demand download
    if download_if_missing:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading passports snapshot from %s to %s", REMOTE_SNAPSHOT_URL, cached_gz)
            req = urllib.request.Request(
                REMOTE_SNAPSHOT_URL,
                headers={"User-Agent": "mcp-fingerprints-client"},
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                data = resp.read()
                if len(data) > 1024:
                    cached_gz.write_bytes(data)
                    return cached_gz
        except Exception as exc:
            logger.warning("Failed to auto-download passports snapshot: %s", exc)

    raise FileNotFoundError(
        f"MCP passports snapshot ({SNAPSHOT_FILENAME}) not found in workspace or user cache. "
        "Run with download_if_missing=True or ensure network access to download it."
    )


def load_passports(download_if_missing: bool = True) -> Dict[str, ServerPackageSpec]:
    """Load all server passports into an in-memory dictionary of ServerPackageSpec."""
    target_path = get_passports_path(download_if_missing=download_if_missing)
    passports: Dict[str, ServerPackageSpec] = {}

    if target_path.is_dir():
        for j_file in target_path.rglob("*.json"):
            if j_file.name in ("index.json", "sync_state.json"):
                continue
            try:
                data = json.loads(j_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "package_name" in data:
                    spec = ServerPackageSpec.from_dict(data)
                    passports[spec.package_name] = spec
            except Exception:
                continue
        return passports

    open_fn = gzip.open if target_path.name.endswith(".gz") else open
    with open_fn(target_path, "rt", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            pkg_dict = data.get("passports", data)
            if isinstance(pkg_dict, dict):
                for pkg_data in pkg_dict.values():
                    if isinstance(pkg_data, dict) and "package_name" in pkg_data:
                        spec = ServerPackageSpec.from_dict(pkg_data)
                        passports[spec.package_name] = spec
            elif isinstance(pkg_dict, list):
                for pkg_data in pkg_dict:
                    if isinstance(pkg_data, dict) and "package_name" in pkg_data:
                        spec = ServerPackageSpec.from_dict(pkg_data)
                        passports[spec.package_name] = spec

    return passports
