#!/usr/bin/env python3
"""Static Web Catalog Generator for MCP Server Passports."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
try:
    from packaging.version import InvalidVersion, parse as parse_version
except ImportError:
    parse_version = None

logger = logging.getLogger("mcp_fingerprints.web_catalog")


def _safe_version_key(v: dict[str, Any]):
    v_str = str(v.get("version", "0.0.0") if isinstance(v, dict) else "0.0.0")
    if parse_version is not None:
        try:
            return (0, parse_version(v_str))
        except Exception:
            pass
    import re
    nums = [int(n) for n in re.findall(r"\d+", v_str)]
    return (1, tuple(nums or [0]))


def build_catalog_entry(passport: dict[str, Any]) -> dict[str, Any]:
    """Compile an enriched catalog entry for the static web dashboard."""
    pkg_name = passport.get("package_name", "unknown")
    ecosystem = passport.get("ecosystem", "generic")
    raw_versions = passport.get("versions", [])
    versions = sorted(raw_versions, key=_safe_version_key, reverse=True) if raw_versions else []
    latest_v = versions[0] if versions else {}

    tool_sigs = latest_v.get("tool_signatures", [])
    tools = []
    for t in tool_sigs:
        if isinstance(t, dict) and "name" in t:
            tools.append(
                {
                    "name": t["name"],
                    "description": t.get("description") or "",
                    "canonical_hash": t.get("canonical_hash") or "",
                    "annotations": t.get("annotations") or {},
                    "parameters": t.get("parameters") or [],
                }
            )

    prompts = []
    prompt_sigs = latest_v.get("prompt_signatures", [])
    for p in prompt_sigs:
        if isinstance(p, dict) and "name" in p:
            prompts.append(
                {"name": p["name"], "description": p.get("description") or ""}
            )

    resources = []
    resource_sigs = latest_v.get("resource_signatures", [])
    for r in resource_sigs:
        if isinstance(r, dict) and ("name" in r or "uri_template" in r):
            resources.append(
                {
                    "name": r.get("name") or "",
                    "uri_template": r.get("uri_template") or "",
                    "description": r.get("description") or "",
                }
            )

    # Default install / run command
    conn = None
    connections = latest_v.get("connections", [])
    transports = []
    for c in connections:
        if c.get("type"):
            transports.append(c["type"])
        if not conn and c.get("type") in ("stdio", "sse"):
            conn = c

    transports = list(dict.fromkeys(transports))  # Deduplicate

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

    author = passport.get("author") or ""
    if not author and "repository_url" in passport:
        # Simple fallback for github repos
        repo = passport["repository_url"]
        if "github.com/" in repo:
            parts = repo.split("github.com/")
            if len(parts) > 1:
                author = parts[1].split("/")[0]

    versions_data = []
    for v in versions:
        v_num = v.get("version", "1.0.0")
        v_tool_sigs = v.get("tool_signatures", [])
        v_tools = []
        for t in v_tool_sigs:
            if isinstance(t, dict) and "name" in t:
                v_tools.append(
                    {
                        "name": t["name"],
                        "description": t.get("description") or "",
                        "canonical_hash": t.get("canonical_hash") or "",
                        "annotations": t.get("annotations") or {},
                        "parameters": t.get("parameters") or [],
                    }
                )
        v_conns = v.get("connections", [])
        v_transports = list(dict.fromkeys([c["type"] for c in v_conns if c.get("type")]))

        v_conn = None
        for c in v_conns:
            if not v_conn and c.get("type") in ("stdio", "sse"):
                v_conn = c
        if v_conn and v_conn.get("type") == "sse":
            v_install_cmd = v_conn.get("url") or ""
            v_conn_type = "sse"
        elif v_conn and v_conn.get("command"):
            v_args_str = " ".join(v_conn.get("args", []))
            v_install_cmd = f"{v_conn['command']} {v_args_str}".strip()
            v_conn_type = "stdio"
        elif ecosystem == "npm":
            v_install_cmd = f"npx -y {pkg_name}@{v_num}"
            v_conn_type = "stdio"
        elif ecosystem in ("pypi", "python"):
            v_install_cmd = f"uvx {pkg_name}=={v_num}"
            v_conn_type = "stdio"
        else:
            v_install_cmd = f"{pkg_name} {v_num}"
            v_conn_type = "generic"

        versions_data.append(
            {
                "version": v_num,
                "release_date": v.get("release_date") or "",
                "tool_count": len(v_tools),
                "tools": v_tools,
                "transports": v_transports,
                "required_env_vars": v.get("required_env_vars") or [],
                "connection_type": v_conn_type,
                "command": v_install_cmd,
            }
        )

    return {
        "name": pkg_name,
        "ecosystem": ecosystem,
        "version": latest_v.get("version", "1.0.0"),
        "latest_version": latest_v.get("version", "1.0.0"),
        "release_date": latest_v.get("release_date") or "",
        "total_versions": len(versions),
        "versions_summary": len(versions),
        "versions": versions_data,
        "description": passport.get("description") or "",
        "repository_url": passport.get("repository_url") or "",
        "homepage_url": passport.get("homepage_url") or "",
        "author": author,
        "license": passport.get("license") or "",
        "tool_count": len(tools),
        "tools": tools,
        "prompts": prompts,
        "resources": resources,
        "toolset_canonical_hash": latest_v.get("toolset_canonical_hash") or "",
        "transports": transports,
        "required_env_vars": latest_v.get("required_env_vars") or [],
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

    import time

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

    sw_path = out_dir / "sw.js"
    if sw_path.exists():
        version_str = str(int(time.time()))
        sw_content = sw_path.read_text(encoding="utf-8")
        import re

        sw_content = re.sub(
            r"mcp-catalog-v[0-9a-zA-Z_]+", f"mcp-catalog-v{version_str}", sw_content
        )
        sw_content = sw_content.replace("__CACHE_VERSION__", version_str)
        sw_path.write_text(sw_content, encoding="utf-8")
        logger.info(f"Injected cache version {version_str} into sw.js")

    logger.info("Compiled %d server catalog entries into %s", len(catalog), target_json)
    return target_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile Static Web Catalog for MCP Servers"
    )
    parser.add_argument(
        "--passports-dir",
        default="data/fingerprints",
        help="Source passports directory",
    )
    parser.add_argument("--output-dir", default="web", help="Target web directory")
    args = parser.parse_args()

    compile_web_catalog(args.passports_dir, args.output_dir)


if __name__ == "__main__":
    main()
