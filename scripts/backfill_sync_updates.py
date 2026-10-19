#!/usr/bin/env python3
"""Backfill historical sync update files from git snapshots."""

import gzip
import io
import json
import logging
from pathlib import Path
import subprocess
from scripts.generate_sync_updates import compute_updates

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_fingerprints.backfill_updates")

def get_snapshot_at_commit(commit: str) -> dict:
    try:
        raw = subprocess.check_output(["git", "show", f"{commit}:passports.json.gz"])
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
            data = json.load(gz)
            return data.get("passports", {})
    except Exception as e:
        logger.error(f"Error getting snapshot at {commit}: {e}")
        return {}

def main():
    out_dir = Path("web/updates")
    out_dir.mkdir(parents=True, exist_ok=True)

    snaps = {
        "1.0.0": "adf5521",
        "1.0.1": "5b1caa4",
        "1.0.2": "62c5567",
        "1.0.3": "8cfad76",
        "1.0.4": "6572c8b",
        "1.0.5": "a08fbe5",
    }

    pairs = [
        ("1.0.1", snaps["1.0.0"], snaps["1.0.1"]),
        ("1.0.2", snaps["1.0.1"], snaps["1.0.2"]),
        ("1.0.3", snaps["1.0.2"], snaps["1.0.3"]),
        ("1.0.4", snaps["1.0.3"], snaps["1.0.4"]),
        ("1.0.5", snaps["1.0.4"], snaps["1.0.5"]),
    ]

    history = []
    latest_updates = []
    latest_version = ""

    for ver, old_c, new_c in pairs:
        logger.info(f"Computing diff for v{ver} ({old_c} -> {new_c})...")
        old_p = get_snapshot_at_commit(old_c)
        new_p = get_snapshot_at_commit(new_c)
        updates = compute_updates(old_p, new_p)
        logger.info(f"v{ver}: {len(updates)} updates")

        ver_file = out_dir / f"v{ver}.json"
        ver_file.write_text(json.dumps(updates, separators=(",", ":")), encoding="utf-8")

        history.append({"version": ver, "count": len(updates)})
        latest_updates = updates
        latest_version = ver

    history.reverse() # Newest first
    history_file = out_dir / "updates_history.json"
    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    latest_file = out_dir / "latest_update.json"
    latest_file.write_text(
        json.dumps(
            {"version": latest_version, "count": len(latest_updates), "servers": latest_updates},
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Successfully backfilled all historical update files!")

if __name__ == "__main__":
    main()
