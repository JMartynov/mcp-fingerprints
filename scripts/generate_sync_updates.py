#!/usr/bin/env python3
"""Generate Sync Updates Tracker for web UI."""

import argparse
import gzip
import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_fingerprints.sync_updates")

def load_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f).get("passports", {})
    else:
        return json.loads(path.read_text(encoding="utf-8")).get("passports", {})

def compute_updates(old_passports: dict[str, Any], new_passports: dict[str, Any]) -> list[dict[str, Any]]:
    updates = []
    
    for pkg_name, new_passport in new_passports.items():
        old_passport = old_passports.get(pkg_name)
        
        badges = []
        is_new_server = old_passport is None
        
        new_versions = new_passport.get("versions", [])
        old_versions = old_passport.get("versions", []) if old_passport else []
        
        new_latest = new_versions[0] if new_versions else {}
        old_latest = old_versions[0] if old_versions else {}
        
        if is_new_server:
            badges.append("NEW SERVER")
        elif new_latest.get("version") != old_latest.get("version"):
            badges.append("NEW VERSION")
            
        new_tools = {t.get("name"): t for t in new_latest.get("tool_signatures", []) if isinstance(t, dict) and "name" in t}
        old_tools = {t.get("name"): t for t in old_latest.get("tool_signatures", []) if isinstance(t, dict) and "name" in t}
        
        added_tools = len(new_tools) - len(old_tools) if len(new_tools) > len(old_tools) else 0
        if added_tools > 0 and not is_new_server:
            badges.append(f"+{added_tools} TOOLS ADDED")
            
        params_updated = False
        if not is_new_server:
            for tool_name, new_tool in new_tools.items():
                if tool_name in old_tools:
                    old_tool = old_tools[tool_name]
                    if json.dumps(new_tool.get("inputSchema", {}), sort_keys=True) != json.dumps(old_tool.get("inputSchema", {}), sort_keys=True):
                        params_updated = True
                        break
        
        if params_updated:
            badges.append("PARAMETERS UPDATED")
            
        if not badges:
            continue
            
        # Build catalog entry
        ecosystem = new_passport.get("ecosystem", "generic")
        tool_list = []
        for t in new_latest.get("tool_signatures", []):
            if isinstance(t, dict) and "name" in t:
                tool_list.append({
                    "name": t["name"],
                    "desc": (t.get("description") or "")[:120],
                })
                
        conn = None
        for c in new_latest.get("connections", []):
            if c.get("type") in ("stdio", "sse"):
                conn = c
                break
                
        if conn and conn.get("type") == "sse":
            install_cmd = conn.get("url") or ""
            conn_type = "sse"
        elif conn and conn.get("command"):
            args_str = " ".join(conn.get("args", []))
            install_cmd = f"{conn['command']} {args_str}".strip()
            conn_type = "stdio"
        elif ecosystem == "npm":
            install_cmd = f"npx -y {pkg_name}"
            conn_type = "stdio"
        elif ecosystem in ("pypi", "python"):
            install_cmd = f"uvx {pkg_name}"
            conn_type = "stdio"
        else:
            install_cmd = pkg_name
            conn_type = "generic"
            
        entry = {
            "name": pkg_name,
            "ecosystem": ecosystem,
            "version": new_latest.get("version", "1.0.0"),
            "description": new_passport.get("description") or "",
            "repository_url": new_passport.get("repository_url") or "",
            "tool_count": len(tool_list),
            "tools": tool_list,
            "connection_type": conn_type,
            "command": install_cmd,
            "is_verified": new_latest.get("capabilities", {}).get("runtime_verified", False) or new_latest.get("capabilities", {}).get("verified_tools", False),
            "badges": badges
        }
        updates.append(entry)
        
    return updates

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", default="previous_passports.json.gz")
    parser.add_argument("--new", default="passports.json.gz")
    parser.add_argument("--version", required=True)
    parser.add_argument("--out-dir", default="web/updates")
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    old_passports = load_snapshot(Path(args.old))
    new_passports = load_snapshot(Path(args.new))
    
    updates = compute_updates(old_passports, new_passports)
    
    version_file = out_dir / f"v{args.version}.json"
    latest_file = out_dir / "latest_update.json"
    history_file = out_dir / "updates_history.json"
    
    version_file.write_text(json.dumps(updates, separators=(",", ":")), encoding="utf-8")
    latest_file.write_text(json.dumps({"version": args.version, "count": len(updates), "servers": updates}, indent=2), encoding="utf-8")
    
    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    if not any(h.get("version") == args.version for h in history):
        history.insert(0, {"version": args.version, "count": len(updates)})
        history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
        
    logger.info(f"Generated updates for v{args.version}: {len(updates)} changes")

if __name__ == "__main__":
    main()
