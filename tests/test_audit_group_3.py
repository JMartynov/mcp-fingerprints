import json
from pathlib import Path

def test_audit_group_3():
    json_path = Path('docs/research/audit_group_3_jvm_dotnet_enterprise.json')
    assert json_path.exists(), "JSON file does not exist"
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    assert len(data) == 200, f"Expected 200 entries, got {len(data)}"
    
    for entry in data:
        if not entry.get('in_repo'):
            assert entry.get('issue_type'), "Missing issue_type for an unmerged entry"
            assert entry.get('remedy'), "Missing remedy for an unmerged entry"
            assert entry.get('issue_details'), "Missing issue_details for an unmerged entry"

