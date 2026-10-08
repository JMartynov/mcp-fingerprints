import json
import gzip
from pathlib import Path
from typing import Any, Iterator


def iter_passports(fingerprints_dir: Path | str) -> Iterator[dict[str, Any]]:
    path = Path(fingerprints_dir)
    if path.is_file() and path.name.endswith(".json.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
            yield from data.get("passports", [])
    elif path.is_dir():
        for file_path in path.rglob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                yield json.load(f)
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
