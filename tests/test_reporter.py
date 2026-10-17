from pathlib import Path
import json
from mcp_fingerprints.reporter import (
    generate_ecosystem_report,
    format_markdown_report,
    generate_badges_markdown,
)


def test_generate_ecosystem_report(tmp_path: Path):
    fingerprints_dir = tmp_path / "fingerprints"
    fingerprints_dir.mkdir()

    passport_1 = {
        "ecosystem": "npm",
        "versions": [
            {
                "tool_signatures": [{"name": "t1"}, {"name": "t2"}],
                "connections": [{"type": "stdio"}],
                "capabilities": {},
            }
        ],
    }

    passport_2 = {
        "ecosystem": "pypi",
        "versions": [
            {
                "tool_signatures": [],
                "connections": [],
                "capabilities": {"is_archived": True},
            }
        ],
    }

    passport_3 = {
        "ecosystem": "npm",
        "versions": [
            {"tool_signatures": [{"name": "t3"}], "connections": [], "capabilities": {}}
        ],
    }

    with open(fingerprints_dir / "p1.json", "w") as f:
        json.dump(passport_1, f)
    with open(fingerprints_dir / "p2.json", "w") as f:
        json.dump(passport_2, f)
    with open(fingerprints_dir / "p3.json", "w") as f:
        json.dump(passport_3, f)

    report = generate_ecosystem_report(fingerprints_dir)

    assert report["total_passports"] == 3
    assert report["with_tools"] == 2
    assert report["with_connections"] == 1
    assert report["tombstoned"] == 1
    assert report["ecosystem_breakdown"]["npm"] == 2
    assert report["ecosystem_breakdown"]["pypi"] == 1

    # tool_distribution stats (tools: 2, 0, 1 -> min: 0, max: 2, avg: 1.0)
    assert report["tool_distribution"]["min"] == 0
    assert report["tool_distribution"]["max"] == 2
    assert report["tool_distribution"]["average"] == 1.0

    md_report = format_markdown_report(report)
    assert "Total Passports:** 3" in md_report
    assert "| npm | 2 |" in md_report

    badges = generate_badges_markdown(report)
    assert "passports-3-blue" in badges


def test_format_probe_report():
    from mcp_fingerprints.prober import ProbeReport
    from mcp_fingerprints.models import FingerprintMatchResult
    from mcp_fingerprints.reporter import format_probe_report

    report = ProbeReport(
        server_command=["npx", "-y", "@modelcontextprotocol/server-sqlite"],
        connection_successful=True,
        tools_observed=[
            {"name": "read_query", "description": "Read something", "inputSchema": {}},
            {"name": "write_query", "description": "Write something", "inputSchema": {}},
        ],
        match_result=FingerprintMatchResult(
            matched=True,
            package_name="@modelcontextprotocol/server-sqlite",
            matched_version="0.6.2",
            confidence_score=1.0,
            purl="pkg:npm/%40modelcontextprotocol/server-sqlite",
        ),
        repository_url="https://github.com/modelcontextprotocol/servers",
        install_command="npx -y @modelcontextprotocol/server-sqlite",
    )

    # Test short format
    short_fmt = format_probe_report(report, format_type="short")
    assert "✔ Identified: @modelcontextprotocol/server-sqlite v0.6.2 (npm, 100% confidence)" in short_fmt
    assert "Repository: https://github.com/modelcontextprotocol/servers" in short_fmt
    assert "Download:   npx -y @modelcontextprotocol/server-sqlite" in short_fmt
    assert "Tools (2):  read_query, write_query" in short_fmt

    # Test table format
    table_fmt = format_probe_report(report, format_type="table")
    assert "Identified Package: @modelcontextprotocol/server-sqlite (v0.6.2)" in table_fmt
    assert "TOOL NAME" in table_fmt
    assert "DESCRIPTION" in table_fmt
    assert "read_query" in table_fmt
    assert "Write something" in table_fmt

    # Test long format
    long_fmt = format_probe_report(report, format_type="long")
    assert "LIVE MCP SERVER AUDIT REPORT" in long_fmt
    assert "Command:            npx -y @modelcontextprotocol/server-sqlite" in long_fmt
    assert "Identified Package: @modelcontextprotocol/server-sqlite" in long_fmt
    assert "Install Command:    npx -y @modelcontextprotocol/server-sqlite" in long_fmt
    assert "- read_query: Read something" in long_fmt

    # Test JSON format
    json_fmt = format_probe_report(report, format_type="json")
    parsed = json.loads(json_fmt)
    assert parsed["tools_count"] == 2
    assert parsed["install_command"] == "npx -y @modelcontextprotocol/server-sqlite"
    assert parsed["match"]["package_name"] == "@modelcontextprotocol/server-sqlite"


def test_format_probe_report_unidentified():
    from mcp_fingerprints.prober import ProbeReport
    from mcp_fingerprints.reporter import format_probe_report
    
    report = ProbeReport(
        server_command=["npx", "-y", "unknown-server"],
        connection_successful=True,
        tools_observed=[{"name": "foo"}],
    )

    short_fmt = format_probe_report(report, "short")
    assert "❓ Unidentified Server: npx -y unknown-server" in short_fmt
    assert "Tools (1):  foo" in short_fmt

    long_fmt = format_probe_report(report, "long")
    assert "Identified Package: NONE (No match found)" in long_fmt
    assert "- foo: " in long_fmt


def test_build_package_command():
    from mcp_fingerprints.prober import McpStdioProber

    assert McpStdioProber.build_package_command("sqlite", "npm") == ["npx", "-y", "sqlite"]
    assert McpStdioProber.build_package_command("mcp-server-sqlite", "pypi") == ["python", "-m", "mcp_server_sqlite"]
    assert McpStdioProber.build_package_command("sqlite", "pypi") == ["uvx", "sqlite"]
    assert McpStdioProber.build_package_command("sqlite", "docker") == ["docker", "run", "-i", "--rm", "sqlite"]
