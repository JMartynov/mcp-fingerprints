import os
import json
from mcp_fingerprints.deep_zero_tool_auditor import extract_suspicious_cards, merge_summary, generate_report, map_audit_to_status

def test_extract_suspicious_cards(tmp_path):
    catalog_path = tmp_path / "catalog.json"
    catalog_data = [
        {"name": "good", "ecosystem": "generic", "repository_url": "foo", "tool_count": 5, "tools": [{"description": "a tool"}], "description": "this is a long enough desc"},
        {"name": "suspicious_zero", "ecosystem": "npm", "repository_url": "foo", "tool_count": 0, "tools": [], "description": "this is a long enough desc"},
        {"name": "suspicious_short_desc", "ecosystem": "npm", "repository_url": "foo", "tool_count": 2, "tools": [{"description": "a tool"}], "description": "short"},
    ]
    with open(catalog_path, "w") as f:
        json.dump(catalog_data, f)

    suspicious = extract_suspicious_cards(str(catalog_path), 50)
    assert len(suspicious) == 2
    names = [s["name"] for s in suspicious]
    assert "suspicious_zero" in names
    assert "suspicious_short_desc" in names

def test_merge_summary(tmp_path):
    summary_path = tmp_path / "summary.md"
    # test creation
    merge_summary(str(summary_path), "2026-10-26", "1.0.0", 10, 5, 5, {"PARSER_MISSED_DYNAMIC_REGISTRATION": 2})

    with open(summary_path, "r") as f:
        content = f.read()

    assert "Total Historical Runs**: 1" in content
    assert "Total Cards Verified**: 10" in content
    assert "Total Discrepancies Flagged**: 5" in content
    assert "2026-10-26 | 1.0.0 | 10 | 5 | 5" in content
    assert "PARSER_MISSED_DYNAMIC_REGISTRATION`: 2" in content

    # test update
    merge_summary(str(summary_path), "2026-10-27", "1.0.1", 20, 15, 5, {"PARSER_MISSED_DYNAMIC_REGISTRATION": 3})
    with open(summary_path, "r") as f:
        content = f.read()

    assert "Total Historical Runs**: 2" in content
    assert "Total Cards Verified**: 30" in content
    assert "Total Discrepancies Flagged**: 10" in content
    assert "PARSER_MISSED_DYNAMIC_REGISTRATION`: 5" in content

def test_generate_report(tmp_path):
    report_path = tmp_path / "report.md"
    results_a = [
        {"name": "repo1", "ecosystem": "npm", "card_tools": 0, "source_tools": 5, "match_status": "MISSED_TOOLS", "root_cause": "PARSER_MISSED_DYNAMIC_REGISTRATION", "location": "file.ts:1"}
    ]
    results_b = [
        {"name": "repo2", "ecosystem": "pypi", "card_tools": 5, "source_tools": 5, "match_status": "PERFECT_MATCH", "root_cause": "N/A", "location": "N/A"}
    ]

    total, match, disc, types = generate_report(str(report_path), "2026-10-26", "1.0.0", results_a, results_b)

    assert total == 2
    assert match == 1
    assert disc == 1
    assert types["PARSER_MISSED_DYNAMIC_REGISTRATION"] == 1

    with open(report_path, "r") as f:
        content = f.read()

    assert "Total Cards Verified**: 2" in content
    assert "Perfect Match Rate**: 50.0%" in content
    assert "repo1" in content
    assert "repo2" in content
