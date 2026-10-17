import json
import gzip
from pathlib import Path
from typing import Any, Iterator
from mcp_fingerprints.prober import ProbeReport
from mcp_fingerprints.canonicalizer import extract_tool_signature, compute_toolset_canonical_hash


def iter_passports(fingerprints_dir: Path | str) -> Iterator[dict[str, Any]]:
    path = Path(fingerprints_dir)
    if path.is_file() and path.name.endswith(".json.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
            yield from data.get("passports", [])
    elif path.is_dir():
        for file_path in path.rglob("*.json"):
            if file_path.name in ("sync_state.json", "index.json"):
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    yield json.load(f)
                except Exception:
                    continue
    else:
        raise ValueError(f"Invalid path: {fingerprints_dir}")


def generate_ecosystem_report(fingerprints_dir: Path | str) -> dict[str, Any]:
    total_passports = 0
    with_tools = 0
    with_connections = 0
    tombstoned = 0
    ecosystem_breakdown = {}

    # tool_distribution stats
    min_tools = float("inf")
    max_tools = 0
    total_tools = 0
    servers_with_versions = 0

    for passport in iter_passports(fingerprints_dir):
        total_passports += 1

        ecosystem = passport.get("ecosystem", "unknown")
        ecosystem_breakdown[ecosystem] = ecosystem_breakdown.get(ecosystem, 0) + 1

        versions = passport.get("versions", [])
        if versions:
            servers_with_versions += 1
            latest_version = versions[
                -1
            ]  # Assume last is latest for stats, or sum across all?
            # We will use the max tools in any version for this server.
            # Or the latest? "tools per server" usually implies the server as a whole.
            # Let's take the max tool count across versions for a single server, or just the latest version.
            # Usually the latest version is at the end or the only one.
            tools = latest_version.get("tool_signatures", [])
            tool_count = len(tools)

            if tool_count > 0:
                with_tools += 1

            connections = latest_version.get("connections", [])
            if len(connections) > 0:
                with_connections += 1

            caps = latest_version.get("capabilities", {})
            if caps.get("is_archived") or caps.get("is_unpublished"):
                tombstoned += 1

            min_tools = min(min_tools, tool_count)
            max_tools = max(max_tools, tool_count)
            total_tools += tool_count
        else:
            min_tools = 0

    if min_tools == float("inf"):
        min_tools = 0

    average_tools = (
        total_tools / servers_with_versions if servers_with_versions > 0 else 0
    )

    return {
        "total_passports": total_passports,
        "with_tools": with_tools,
        "with_connections": with_connections,
        "tombstoned": tombstoned,
        "ecosystem_breakdown": ecosystem_breakdown,
        "tool_distribution": {
            "min": min_tools,
            "max": max_tools,
            "average": average_tools,
        },
    }


def format_markdown_report(report_data: dict[str, Any]) -> str:
    total = report_data["total_passports"]

    def pct(count):
        if total == 0:
            return "0.00%"
        return f"{(count / total) * 100:.2f}%"

    lines = [
        "# Ecosystem Health Report",
        "",
        "## Overall Metrics",
        f"- **Total Passports:** {total}",
        f"- **With Tools:** {report_data['with_tools']} ({pct(report_data['with_tools'])})",
        f"- **With Connections:** {report_data['with_connections']} ({pct(report_data['with_connections'])})",
        f"- **Tombstoned:** {report_data['tombstoned']} ({pct(report_data['tombstoned'])})",
        "",
        "## Ecosystem Breakdown",
        "| Ecosystem | Count |",
        "|---|---|",
    ]

    for eco, count in sorted(report_data["ecosystem_breakdown"].items()):
        lines.append(f"| {eco} | {count} |")

    lines.extend(
        [
            "",
            "## Tool Distribution",
            f"- **Minimum Tools:** {report_data['tool_distribution']['min']}",
            f"- **Maximum Tools:** {report_data['tool_distribution']['max']}",
            f"- **Average Tools:** {report_data['tool_distribution']['average']:.2f}",
        ]
    )

    return "\n".join(lines)


def generate_badges_markdown(report_data: dict[str, Any]) -> str:
    total = report_data["total_passports"]
    badges = [
        f"[![Passports Count](https://img.shields.io/badge/passports-{total}-blue.svg)](#)",
        f"[![Tools Provided](https://img.shields.io/badge/with_tools-{report_data['with_tools']}-green.svg)](#)",
    ]
    return "\n".join(badges)


def format_probe_report(report: ProbeReport, format_type: str = "long") -> str:
    """Format the probe report in the specified layout (short, long, table, json)."""
    if format_type == "json":
        return json.dumps(report.to_dict(), indent=2)

    if not report.connection_successful:
        return f"✖ Connection Failed: {' '.join(report.server_command)}\nError: {report.error}"

    match = report.match_result
    identified = False
    pkg_name = "Unknown Server"
    version_str = "unknown"
    confidence = 0.0
    
    if match and match.matched:
        identified = True
        pkg_name = match.package_name or "Unknown Package"
        version_str = match.matched_version or "unknown"
        confidence = match.confidence_score * 100

    tool_names = [t.get("name", "unknown") for t in report.tools_observed]

    if format_type == "short":
        lines = []
        if identified:
            # Need to figure out ecosystem from purl or default to unknown
            eco = "unknown"
            if match and match.purl:
                if "npm" in match.purl: eco = "npm"
                elif "pypi" in match.purl: eco = "pypi"
                elif "docker" in match.purl: eco = "docker"
            
            status = "✔ Identified" if confidence >= 95 else "⚠ Partial Match"
            lines.append(f"{status}: {pkg_name} v{version_str} ({eco}, {confidence:.0f}% confidence)")
            if report.repository_url:
                lines.append(f"  Repository: {report.repository_url}")
            if report.install_command:
                lines.append(f"  Download:   {report.install_command}")
        else:
            lines.append(f"❓ Unidentified Server: {' '.join(report.server_command)}")
        
        tool_list = ", ".join(tool_names[:10]) + ("..." if len(tool_names) > 10 else "")
        lines.append(f"  Tools ({len(report.tools_observed)}):  {tool_list}")
        
        return "\n".join(lines)

    elif format_type == "table":
        lines = []
        if identified:
            lines.append(f"Identified Package: {pkg_name} (v{version_str})")
        else:
            lines.append(f"Unidentified Server: {' '.join(report.server_command)}")
        
        lines.append("")
        lines.append(f"{'TOOL NAME'.ljust(30)} | {'DESCRIPTION'.ljust(45)}")
        lines.append("-" * 30 + "-+-" + "-" * 45)
        
        for tool in report.tools_observed:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "")
            desc = desc.split("\n")[0]
            if len(desc) > 42:
                desc = desc[:39] + "..."
            lines.append(f"{name.ljust(30)} | {desc.ljust(45)}")
        
        return "\n".join(lines)

    else:
        # Default to long
        lines = []
        lines.append("==================================================")
        lines.append("         LIVE MCP SERVER AUDIT REPORT             ")
        lines.append("==================================================")
        lines.append(f"Command:            {' '.join(report.server_command)}")
        lines.append(f"Connection:         {'SUCCESS' if report.connection_successful else 'FAILED'}")
        if report.error:
            lines.append(f"Error:              {report.error}")
        
        lines.append(f"Observed Tools:     {len(report.tools_observed)}")
        lines.append(f"Observed Prompts:   {len(report.prompts_observed)}")
        lines.append(f"Observed Resources: {len(report.resources_observed)}")
        
        lines.append("--------------------------------------------------")
        if match and match.matched:
            lines.append(f"Identified Package: {match.package_name}")
            lines.append(f"Identified Version: {match.matched_version}")
            if report.latest_version and report.is_outdated:
                lines.append(f"Latest Version:     {report.latest_version} (OUTDATED)")
            elif report.latest_version:
                lines.append(f"Latest Version:     {report.latest_version} (Up to date)")
            lines.append(f"Confidence:         {match.confidence_score * 100:.1f}% ({match.match_layer})")
            
            if report.repository_url:
                lines.append(f"Repository:         {report.repository_url}")
            if report.install_command:
                lines.append(f"Install Command:    {report.install_command}")
            if report.author:
                lines.append(f"Author:             {report.author}")
        else:
            lines.append("Identified Package: NONE (No match found)")

        lines.append("--------------------------------------------------")
        
        if report.tools_observed:
            sigs = [extract_tool_signature(t) for t in report.tools_observed]
            hash_val = compute_toolset_canonical_hash(report.tools_observed)
            lines.append(f"Toolset Hash:       {hash_val}")
            lines.append("")
            lines.append("Tools:")
            for tool in report.tools_observed:
                name = tool.get("name", "unknown")
                desc = tool.get("description", "")
                desc = desc.split("\n")[0]
                lines.append(f"  - {name}: {desc}")
                
                params = tool.get("inputSchema", {}).get("properties", {})
                if params:
                    lines.append("    Parameters:")
                    for p_name, p_val in params.items():
                        p_type = p_val.get("type", "any")
                        lines.append(f"      * {p_name} ({p_type})")

        return "\n".join(lines)
