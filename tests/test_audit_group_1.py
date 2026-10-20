import json
from pathlib import Path

def test_audit_group_1_json_exists():
    assert Path("docs/research/audit_group_1_rust_systems.json").exists()

def test_audit_group_1_count():
    with open("docs/research/audit_group_1_rust_systems.json") as f:
        data = json.load(f)
    assert len(data) == 200

def test_audit_group_1_missing_entries_have_issue_and_remedy():
    with open("docs/research/audit_group_1_rust_systems.json") as f:
        data = json.load(f)
    
    for item in data:
        if not item["in_repo"]:
            assert "issue_type" in item
            assert item["issue_type"] != ""
            assert "remedy" in item
            assert item["remedy"] != ""
