#!/usr/bin/env python3
"""
Re-index and re-create passports for servers with Upgraded AST & SDK Tool Patterns.
Inspects candidate passports, accesses their upstream GitHub repos, extracts tools using
upgraded regex/AST patterns (e.g., server.registerTool, Tool(name=...)), and updates passports,
catalog, and cache.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import ssl
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.mcp_fingerprints.ast_parser import parse_mcp_source_code
from src.mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from src.mcp_fingerprints.canonicalizer import canonicalize_json, compute_sha256

# Target Passports for Task 93
TARGET_PASSPORTS = [
    "soil-dev_capsulemcp.json",
    "@zvid_mcp.json",
    "giorgio44_gateonai-mcp-server.json",
    "awkoy_notion-mcp-server.json",
    "audionaut-mcp.json",
    "tufantunc_ssh-mcp.json",
    "ihor-sokoliuk_mcp-searxng.json",
    "bvisible_mcp-ssh-manager.json",
    "PhilipAD_health-export-mcp.json",
    "eslint-plugin-mcp-sdk-security.json",
    "api-auto-mcp-server.json",
    "1mcp-app_agent.json",
    "@fodx_codelens.json",
    "@fruggr_zendesk-mcp-server.json",
    "@jrpool_kilotest.json",
    "@mojomo_mcp-server.json",
    "@openephemeris_mcp-server.json",
    "AutomateLab-tech_content-distribution-mcp.json",
]

def _get_ssl_context() -> ssl.SSLContext:
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()

def get_repo_owner_name(url: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Extracts the repository owner and name from a given GitHub URL.
    """
    if not url:
        return None, None
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    if m:
        owner = m.group(1)
        repo = m.group(2).removesuffix(".git")
        return owner, repo
    return None, None

def _request_with_backoff(url: str) -> Optional[dict]:
    """
    Performs a standard GET request with timeout and SSL fallback.
    Returns parsed JSON on success, None on failure.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "mcp-fingerprints-reindexer"})
    if "GITHUB_TOKEN" in os.environ:
         req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    try:
        with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=5.0) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_github_tree(owner: str, repo: str, branch: str = "main") -> list[str]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    data = _request_with_backoff(url)
    if not data:
        return []
    
    # We want TS, JS, Python, Go files and Markdown for docs fallback typically.
    extensions = (".ts", ".js", ".mjs", ".py", ".go", ".md")
    return [x["path"] for x in data.get("tree", []) 
            if x.get("type") == "blob" and x["path"].lower().endswith(extensions) and not x["path"].endswith(("_test.py", ".test.ts", ".spec.ts"))]

def fetch_raw_file(owner: str, repo: str, branch: str, path: str) -> Optional[str]:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "mcp-fingerprints-reindexer"})
    if "GITHUB_TOKEN" in os.environ:
         req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    try:
        with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=5.0) as resp:
            return resp.read(1024 * 1024).decode("utf-8", errors="ignore")
    except Exception as e:
        return None

def extract_tools_from_repo(owner: str, repo: str) -> list[dict[str, Any]]:
    """
    Coordinates fetching the AST file tree from GitHub and extracting
    MCP tools using polyglot parsers. Inspects up to 30 top candidate files.
    """
    # 1. Fetch repo data to get default branch
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_data = _request_with_backoff(repo_url)
    branch = repo_data.get("default_branch", "main") if repo_data else "main"

    files = fetch_github_tree(owner, repo, branch)
    if not files:
        # Fallback to main and master
        for fb in ("main", "master"):
            if fb != branch:
                files = fetch_github_tree(owner, repo, fb)
                if files:
                    branch = fb
                    break
    
    if not files:
        return []
    
    def priority(p: str) -> int:
        low = p.lower()
        if "mcp" in low and ("tool" in low or "server" in low):
            return 0
        if "tool" in low:
            return 1
        if "server" in low:
            return 2
        if "index" in low or "main" in low:
            return 3
        if "readme" in low:
            return 4
        return 5

    files.sort(key=priority)
    candidates = files[:30] # Inspect up to 30 top files

    aggregated_tools = []
    seen_names = set()

    for fpath in candidates:
        code = fetch_raw_file(owner, repo, branch, fpath)
        if not code:
            continue
        
        # Determine language for parser
        ext = fpath.split(".")[-1].lower()
        
        if ext == "md":
            extracted = parse_markdown_tool_docs(code)
        else:
            if ext in ("py",):
                lang = "python"
            elif ext in ("ts", "js", "mjs"):
                lang = "typescript"
            elif ext in ("go",):
                lang = "go"
            else:
                lang = None

            extracted = parse_mcp_source_code(code, language=lang)
            
        for t in extracted:
            tname = t.get("name")
            if tname and tname not in seen_names:
                seen_names.add(tname)
                aggregated_tools.append(t)

    return aggregated_tools

def update_passport_tools(passport_path: Path, new_tools: list[dict[str, Any]]) -> bool:
    try:
        with open(passport_path, "r") as f:
            passport = json.load(f)
    except Exception:
        return False

    versions = passport.get("versions", [])
    if not versions:
        return False

    # We update the latest version
    v = versions[-1]
    existing_tools = v.get("tool_signatures", [])
    
    existing_names = {t.get("name") for t in existing_tools}
    new_names = {t.get("name") for t in new_tools}

    if new_names.issubset(existing_names) and len(existing_names) > 0:
        return False

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

def sync_catalog_and_cache(passport_dir: Path, updated_passports: List[str]):
    # Sync cache
    cache_path = passport_dir.parent / ".passport_cache.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            cache = json.load(f)
        for p in updated_passports:
            # We just invalidate or update the entry
            if p in cache:
                p_path = passport_dir / p
                if p_path.exists():
                    cache[p]["mtime"] = os.path.getmtime(p_path)
        with open(cache_path, "w") as f:
            json.dump(cache, f, indent=2)
            
    # Sync catalog (simplified, we just update tool count if we find it)
    catalog_path = ROOT_DIR / "web" / "catalog.json"
    if catalog_path.exists():
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
        
        for item in catalog:
            # To map item to passport, we might need repository_url or name.
            # It's usually easier to just re-read the passport for the item.
            p_name = item.get("name")
            if not p_name:
                continue
            # Basic mapping
            possible_filename = p_name.replace("/", "_") + ".json"
            if possible_filename in updated_passports:
                p_path = passport_dir / possible_filename
                if p_path.exists():
                    with open(p_path, "r") as f:
                        passport = json.load(f)
                        versions = passport.get("versions", [])
                        if versions:
                            latest_v = versions[-1]
                            item["tool_count"] = len(latest_v.get("tool_signatures", []))
                            item["latest_version"] = latest_v.get("version", item.get("latest_version"))
                            
        with open(catalog_path, "w") as f:
            json.dump(catalog, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Re-index SDK Passports")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes to disk")
    parser.add_argument("--passports", type=str, help="Comma-separated list of passport filenames to process")
    args = parser.parse_args()

    passports_to_process = TARGET_PASSPORTS
    if args.passports:
        passports_to_process = [p.strip() for p in args.passports.split(",")]

    passport_dir = ROOT_DIR / "data" / "fingerprints"
    
    report_lines = [
        "# SDK Passports Re-Index Audit Report",
        "",
        "Generated for Task 93.",
        f"Total passports targeted: {len(passports_to_process)}",
        "",
        "| Passport | Repository | Previous Tools | Discovered Tools | Status |",
        "|:---|:---|:---:|:---:|:---|"
    ]

    updated_count = 0
    updated_files = []

    for p_name in passports_to_process:
        p_path = passport_dir / p_name
        if not p_path.exists():
            report_lines.append(f"| `{p_name}` | `N/A` | 0 | 0 | `NOT_FOUND` |")
            continue
            
        with open(p_path, "r") as f:
            passport = json.load(f)
            
        repo_url = passport.get("repository_url")
        if not repo_url:
            # try to extract from name or something
            # Just fallback
            report_lines.append(f"| `{p_name}` | `N/A` | 0 | 0 | `NO_GITHUB_REPO` |")
            continue
            
        owner, repo = get_repo_owner_name(repo_url)
        if not owner or not repo:
            report_lines.append(f"| `{p_name}` | `{repo_url}` | 0 | 0 | `INVALID_GITHUB_REPO` |")
            continue

        versions = passport.get("versions", [])
        prev_count = 0
        if versions:
            prev_count = len(versions[-1].get("tool_signatures", []))

        print(f"Inspecting {owner}/{repo} for {p_name} ...")
        discovered = extract_tools_from_repo(owner, repo)
        disc_count = len(discovered)

        if disc_count > 0:
            if not args.dry_run:
                changed = update_passport_tools(p_path, discovered)
            else:
                existing_names = {t.get("name") for t in versions[-1].get("tool_signatures", [])} if versions else set()
                new_names = {t.get("name") for t in discovered}
                changed = not new_names.issubset(existing_names)
                
            status = "RECOVERED_NEW_TOOLS" if changed else "ALREADY_UP_TO_DATE"
            if changed:
                updated_count += 1
                updated_files.append(p_name)
                
            tool_names = ", ".join(f"`{t['name']}`" for t in discovered[:3])
            if disc_count > 3: tool_names += f" (+{disc_count - 3} more)"
            report_lines.append(f"| `{p_name}` | `https://github.com/{owner}/{repo}` | {prev_count} | {disc_count} ({tool_names}) | `{status}` |")
        else:
            report_lines.append(f"| `{p_name}` | `https://github.com/{owner}/{repo}` | {prev_count} | 0 | `ZERO_TOOLS` |")

    report_lines.insert(4, f"Total passports updated with newly recovered tools: {updated_count}\n")

    if not args.dry_run and updated_files:
        sync_catalog_and_cache(passport_dir, updated_files)

    # Note: we print the report or write it to a default spot if run manually.
    # The actual fix report will be generated via a separate step or can be copied from output.
    report_path = ROOT_DIR / "docs" / "reports" / "sdk_passports_reindex_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines) + "\n")
        
    print(f"Re-indexing complete. Updated {updated_count} passports. Report written to {report_path}")

if __name__ == "__main__":
    main()
