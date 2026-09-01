"""CLI for MCP Fingerprint and Passport Knowledge Base."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from mcp_fingerprints.schema_validator import PassportSchemaValidator
from mcp_fingerprints.snapshot import build_snapshot
from mcp_fingerprints.synchronizer import PassportSynchronizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_fingerprints.cli")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Fingerprint & Passport Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sync
    sync_p = subparsers.add_parser("sync", help="Synchronize MCP server passports from registries")
    sync_p.add_argument("--output", default="data/fingerprints", help="Output directory")
    sync_p.add_argument("--all", action="store_true", help="Sync all registries")
    sync_p.add_argument("--smithery-pages", type=int, default=5, help="Number of Smithery pages")
    sync_p.add_argument("--npm-limit", type=int, default=100, help="NPM package limit")
    sync_p.add_argument("--pypi-limit", type=int, default=100, help="PyPI package limit")
    sync_p.add_argument("--snapshot", action="store_true", default=True, help="Compile snapshot after sync")

    # Validate
    val_p = subparsers.add_parser("validate", help="Validate passport directory invariants")
    val_p.add_argument("--dir", default="data/fingerprints", help="Passport directory to validate")

    # Snapshot
    snap_p = subparsers.add_parser("snapshot", help="Compile all passports into consolidated .json.gz")
    snap_p.add_argument("--data-dir", default="data/fingerprints", help="Passport data directory")
    snap_p.add_argument("--output-gz", default="passports.json.gz", help="Output gzip file path")
    snap_p.add_argument("--output-json", default=None, help="Optional uncompressed JSON output path")

    args = parser.parse_args()

    if args.command == "sync":
        sync = PassportSynchronizer(output_dir=args.output)
        if args.all or (not args.smithery_pages and not args.npm_limit and not args.pypi_limit):
            logger.info("Running full multi-source passport synchronization...")
            sync.sync_smithery(max_pages=args.smithery_pages)
            sync.sync_npm(limit=args.npm_limit)
            sync.sync_pypi(limit=args.pypi_limit)
        else:
            if args.smithery_pages > 0:
                sync.sync_smithery(max_pages=args.smithery_pages)
            if args.npm_limit > 0:
                sync.sync_npm(limit=args.npm_limit)
            if args.pypi_limit > 0:
                sync.sync_pypi(limit=args.pypi_limit)

        if args.snapshot:
            logger.info("Compiling consolidated snapshot...")
            build_snapshot(data_dir=args.output, output_gz=f"{Path(args.output).parent}/passports.json.gz" if args.output != "data/fingerprints" else "passports.json.gz")

    elif args.command == "validate":
        valid, invalid, errors = PassportSchemaValidator.validate_directory(args.dir)
        print(f"Validation summary: {valid} valid, {invalid} invalid passports.")
        if invalid > 0:
            for err in errors:
                print(f"ERROR: {err}")
            sys.exit(1)
        sys.exit(0)

    elif args.command == "snapshot":
        res = build_snapshot(data_dir=args.data_dir, output_gz=args.output_gz, output_json=args.output_json)
        print(f"Compiled {res['total_passports']} passports ({res['size_kb']:.2f} KB) -> {res['snapshot_path']}")


if __name__ == "__main__":
    main()
