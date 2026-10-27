#!/usr/bin/env python3
"""
Re-index and re-create passports for all Go MCP servers in the catalog.
Uses the upgraded Go AST parser (with PR #38 composite literal parsing, Go map/slice schemas, and constant name resolution),
inspects upstream GitHub source code for candidate Go files, extracts tools, and updates data/fingerprints/*.json.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.mcp_fingerprints.ast_parser import parse_golang_mcp_code
from src.mcp_fingerprints.canonicalizer import canonicalize_json, compute_sha256

def _get_ssl_context() -> ssl.SSLContext:
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()

def get_repo_owner_name(url: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not url:
        return None, None
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    if m:
        owner = m.group(1)
        repo = m.group(2).removesuffix(".git")
        return owner, repo
    return None, None

def fetch_github_tree(owner: str, repo: str, branch: str = "main") -> list[str]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    req = urllib.request.Request(url, headers={"User-Agent": "mcp-fingerprints-reindexer"})
    try:
        with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return [x["path"] for x in data.get("tree", []) if x.get("type") == "blob" and x["path"].endswith(".go") and not x["path"].endswith("_test.go")]
    except Exception:
        return []

def fetch_raw_file(owner: str, repo: str, branch: str, path: str) -> Optional[str]:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "mcp-fingerprints-reindexer"})
    try:
        with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=4.0) as resp:
            return resp.read(500 * 1024).decode("utf-8", errors="ignore")
    except Exception:
        return None

def extract_tools_from_repo(owner: str, repo: str) -> list[dict[str, Any]]:
    for branch in ("main", "master"):
        go_files = fetch_github_tree(owner, repo, branch)
        if not go_files:
            continue
        
        # Sort files prioritizing likely tool definitions
        def priority(p: str) -> int:
            low = p.lower()
            if "mcp" in low and ("tool" in low or "server" in low):
                return 0
            if "tool" in low:
                return 1
            if "server" in low:
                return 2
            if "cmd/" in low or "main.go" in low:
                return 3
            return 4

        go_files.sort(key=priority)
        candidates = go_files[:20]

        aggregated_tools = []
        seen_names = set()

        for fpath in candidates:
            code = fetch_raw_file(owner, repo, branch, fpath)
            if not code:
                continue
            
            # Fast check if file has MCP indicators before parsing
            if not any(k in code for k in ("mcp", "NewTool", "AddTool", "mark3labs", "modelcontextprotocol")):
                continue

            extracted = parse_golang_mcp_code(code)
            for t in extracted:
                tname = t.get("name")
                if tname and tname not in seen_names:
                    seen_names.add(tname)
                    aggregated_tools.append(t)

        if aggregated_tools:
            return aggregated_tools

    return []

def update_passport_tools(passport_path: Path, new_tools: list[dict[str, Any]]) -> bool:
    try:
        with open(passport_path, "r") as f:
            passport = json.load(f)
    except Exception:
        return False

    versions = passport.get("versions", [])
    if not versions:
        return False

    v = versions[0]
    existing_tools = v.get("tool_signatures", [])
    
    # Check if tools already exist and match
    existing_names = {t.get("name") for t in existing_tools}
    new_names = {t.get("name") for t in new_tools}

    if new_names.issubset(existing_names) and len(existing_names) > 0:
        return False

    # Merge tools
    merged_signatures = []
    seen = set()

    # Keep existing tools
    for et in existing_tools:
        name = et.get("name")
        if name and name not in seen:
            seen.add(name)
            merged_signatures.append(et)

    # Add new tools
    for nt in new_tools:
        name = nt.get("name")
        if name and name not in seen:
            seen.add(name)
            sig = {
                "name": name,
                "description": nt.get("description", ""),
                "inputSchema": nt.get("inputSchema", {"type": "object", "properties": {}, "required": []})
            }
            canonical_payload = {
                "name": sig["name"],
                "description": sig.get("description", ""),
                "inputSchema": sig.get("inputSchema", {})
            }
            raw_hash = compute_sha256(canonicalize_json(canonical_payload))
            sig["canonical_hash"] = f"sha256:{raw_hash}" if not raw_hash.startswith("sha256:") else raw_hash
            merged_signatures.append(sig)

    v["capabilities"]["tools"] = len(merged_signatures) > 0
    v["tool_signatures"] = merged_signatures

    # Recalculate toolset hash
    all_hashes = "".join([ts.get("canonical_hash", "") for ts in merged_signatures])
    raw_thash = compute_sha256(all_hashes)
    v["toolset_canonical_hash"] = f"sha256:{raw_thash}" if not raw_thash.startswith("sha256:") else raw_thash

    with open(passport_path, "w") as f:
        json.dump(passport, f, indent=2)

    return True

def reindex_all_go_passports():
    inventory_path = ROOT_DIR / "data" / "samples" / "golang_mcp_servers_inventory.json"
    if not inventory_path.exists():
        print(f"Inventory {inventory_path} not found.")
        return

    with open(inventory_path, "r") as f:
        inventory = json.load(f)

    report_lines = [
        "# Golang MCP Passports Re-Index Audit Report",
        "",
        "Generated for Task 85.",
        f"Total servers in inventory: {len(inventory)}",
        "",
        "| Passport | Repository | Previous Tools | Discovered Tools | Status |",
        "|:---|:---|:---:|:---:|:---|"
    ]

    updated_count = 0

    for idx, item in enumerate(inventory, 1):
        p_path = Path(item["file"])
        repo_url = item.get("repo")
        prev_count = item.get("existing_tool_count", 0)
        owner, repo = get_repo_owner_name(repo_url)

        if not owner or not repo:
            report_lines.append(f"| `{p_path.name}` | `{repo_url or 'N/A'}` | {prev_count} | 0 | `NO_GITHUB_REPO` |")
            continue

        discovered = extract_tools_from_repo(owner, repo)
        disc_count = len(discovered)

        if disc_count > 0:
            changed = update_passport_tools(p_path, discovered)
            status = "RECOVERED_NEW_TOOLS" if changed else "ALREADY_UP_TO_DATE"
            if changed:
                updated_count += 1
            tool_names = ", ".join(f"`{t['name']}`" for t in discovered[:3])
            if disc_count > 3: tool_names += f" (+{disc_count - 3} more)"
            report_lines.append(f"| `{p_path.name}` | `https://github.com/{owner}/{repo}` | {prev_count} | {disc_count} ({tool_names}) | `{status}` |")
        else:
            report_lines.append(f"| `{p_path.name}` | `https://github.com/{owner}/{repo}` | {prev_count} | 0 | `ZERO_TOOLS` |")

    report_lines.insert(4, f"Total passports updated with newly recovered tools: {updated_count}\n")

    report_path = ROOT_DIR / "docs" / "reports" / "golang_passports_reindex_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"Re-indexing complete. Updated {updated_count} passports. Report written to {report_path}")

if __name__ == "__main__":
    reindex_all_go_passports()
