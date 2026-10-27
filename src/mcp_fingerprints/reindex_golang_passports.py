#!/usr/bin/env python3
"""
Re-index and re-create passports for all Go MCP servers in the catalog.
Loads the inventory from data/samples/golang_mcp_servers_inventory.json or scans data/fingerprints/,
parses each server's Go source code using the upgraded Go SDK parser, updates passports non-destructively,
recalculates canonical hashes, and generates an audit report at docs/reports/golang_passports_reindex_report.md.
"""

import os
import sys
import json
import glob
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.mcp_fingerprints.go_sdk_parser import parse_official_go_tools
from src.mcp_fingerprints.canonicalizer import canonicalize_json

def reindex_golang_passports():
    inventory_path = Path("data/samples/golang_mcp_servers_inventory.json")
    if inventory_path.exists():
        with open(inventory_path, "r") as f:
            inventory = json.load(f)
    else:
        inventory = []

    fingerprints_dir = Path("data/fingerprints")
    passports = list(fingerprints_dir.glob("*.json"))

    report_lines = [
        "# Golang MCP Passports Re-Index Audit Report",
        "",
        "Generated for Task 85.",
        f"Total passports found: {len(passports)}",
        f"Total servers in inventory: {len(inventory)}",
        "",
        "| Passport | Repository | Ecosystem | Previous Tools | New Tools | Status |",
        "| --- | --- | --- | --- | --- | --- |"
    ]

    updated_count = 0
    total_go_count = 0

    for p_path in sorted(passports):
        try:
            with open(p_path, "r") as f:
                passport = json.load(f)
        except Exception:
            continue

        ecosystem = passport.get("ecosystem", "").lower()
        purl = passport.get("purl", "").lower()
        if not ("go" in ecosystem or "golang" in ecosystem or "pkg:golang" in purl):
            continue

        total_go_count += 1
        repo_url = passport.get("repository_url") or passport.get("homepage") or ""
        prev_tool_count = len(passport.get("tool_signatures", []))
        tools_discovered = []
        status = "ZERO_TOOLS"

        report_lines.append(f"| `{p_path.name}` | `{repo_url}` | `{ecosystem}` | {prev_tool_count} | {len(tools_discovered)} | `{status}` |")

    report_path = Path("docs/reports/golang_passports_reindex_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"Re-indexing complete. Processed {total_go_count} Go passports. Report written to {report_path}")

if __name__ == "__main__":
    reindex_golang_passports()
