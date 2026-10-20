import json
import os
import pytest

def test_audit_group_4():
    json_path = "docs/research/audit_group_4_regional_international.json"
    
    # Asserts docs/research/audit_group_4_regional_international.json exists
    assert os.path.exists(json_path), f"File {json_path} does not exist"
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Asserts exactly 200 entries
    assert len(data) == 200, f"Expected 200 entries, found {len(data)}"
    
    # Asserts every missing entry has non-empty issue_type and remedy
    for i, entry in enumerate(data):
        if not entry.get("in_repo"):
            assert "issue_type" in entry and entry["issue_type"], f"Entry {i} missing issue_type"
            assert "remedy" in entry and entry["remedy"], f"Entry {i} missing remedy"
            assert "issue_details" in entry and entry["issue_details"], f"Entry {i} missing issue_details"

