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
