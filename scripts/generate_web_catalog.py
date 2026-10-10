#!/usr/bin/env python3
"""Static Web Catalog Generator for MCP Server Passports."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from mcp_fingerprints.security_classifier import classify_server_security_profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_fingerprints.web_catalog")


def build_catalog_entry(passport: dict[str, Any]) -> dict[str, Any]:
    """Compile a compact, high-efficiency catalog entry for the static web dashboard."""
    pkg_name = passport.get("package_name", "unknown")
    ecosystem = passport.get("ecosystem", "generic")
    versions = passport.get("versions", [])
    latest_v = versions[0] if versions else {}

    tool_sigs = latest_v.get("tool_signatures", [])
    tools = []
    for t in tool_sigs:
        if isinstance(t, dict) and "name" in t:
            tools.append({
                "name": t["name"],
                "desc": (t.get("description") or "")[:120],
            })

    # Determine security risk
    sec_profile = passport.get("security_profile")
    if not sec_profile and versions:
        sec_profile = classify_server_security_profile(versions)
    
    advisories = []
    if sec_profile:
        advisories = sec_profile.get("advisories", [])
        
    advisory_count = len(advisories)
    
    # Update risk tier based on advisories
    risk_tier = sec_profile.get("highest_risk_tier", "low") if sec_profile else "low"
    if advisory_count > 0:
        # Check for critical or high severity advisories
        has_crit = any(adv.get("severity") == "CRITICAL" for adv in advisories)
        has_high = any(adv.get("severity") == "HIGH" for adv in advisories)
        if has_crit:
            risk_tier = "critical"
        elif has_high and risk_tier not in ("critical",):
            risk_tier = "high"
        elif risk_tier not in ("critical", "high"):
            risk_tier = "medium"

    # Default install / run command
    conn = None
    connections = latest_v.get("connections", [])
    for c in connections:
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

    return {
        "name": pkg_name,
        "ecosystem": ecosystem,
        "version": latest_v.get("version", "1.0.0"),
        "description": passport.get("description") or "",
        "repository_url": passport.get("repository_url") or "",
        "tool_count": len(tools),
        "tools": tools,
        "risk_tier": risk_tier,
        "advisories": advisories,
        "advisory_count": advisory_count,
        "connection_type": conn_type,
        "command": install_cmd,
        "is_verified": latest_v.get("capabilities", {}).get("runtime_verified", False)
        or latest_v.get("capabilities", {}).get("verified_tools", False),
    }


def compile_web_catalog(
    passports_dir: Path | str = "data/fingerprints",
    output_dir: Path | str = "web",
) -> Path:
    """Read all passports and output catalog.json to web output directory."""
    p_dir = Path(passports_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog: list[dict[str, Any]] = []

    for f in p_dir.rglob("*.json"):
        if f.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
            continue
        try:
            content = json.loads(f.read_text(encoding="utf-8"))
            if "package_name" in content:
                catalog.append(build_catalog_entry(content))
        except Exception:
            continue

    catalog.sort(key=lambda x: (x["tool_count"] == 0, -x["tool_count"], x["name"]))

    target_json = out_dir / "catalog.json"
    target_json.write_text(json.dumps(catalog, separators=(",", ":")), encoding="utf-8")
    logger.info("Compiled %d server catalog entries into %s", len(catalog), target_json)
    return target_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile Static Web Catalog for MCP Servers")
    parser.add_argument("--passports-dir", default="data/fingerprints", help="Source passports directory")
    parser.add_argument("--output-dir", default="web", help="Target web directory")
    args = parser.parse_args()

    compile_web_catalog(args.passports_dir, args.output_dir)


if __name__ == "__main__":
    main()
