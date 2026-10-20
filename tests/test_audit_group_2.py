import json
import os
import pytest

def test_audit_group_2_json_exists():
    assert os.path.exists("docs/research/audit_group_2_go_cloud_native.json")

def test_audit_group_2_json_count():
    with open("docs/research/audit_group_2_go_cloud_native.json") as f:
        data = json.load(f)
    assert len(data) == 200, f"Expected 200 entries, found {len(data)}"

def test_audit_group_2_missing_entries_have_remedy():
    with open("docs/research/audit_group_2_go_cloud_native.json") as f:
        data = json.load(f)
    
    for item in data:
        if not item.get("in_repo"):
            assert item.get("issue_type"), f"Missing issue_type for {item['name']}"
            assert item.get("remedy"), f"Missing remedy for {item['name']}"
