import json
import os

def test_master_audit_conformance():
    file_path = "docs/research/master_mcp_ecosystem_audit_1000.json"
    
    # Asserts file exists
    assert os.path.exists(file_path), "Master JSON file does not exist."
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    # Asserts length is exactly 1000
    assert len(data) == 1000, f"Expected 1000 items, but got {len(data)}."
    
    # Asserts each of the 5 groups has exactly 200 items
    groups = {
        "rust_systems": 0,
        "go_cloud_native": 0,
        "jvm_dotnet_enterprise": 0,
        "regional_international": 0,
        "monorepo_docker_emerging": 0
    }
    
    for item in data:
        groups[item['group']] += 1
        
        # Asserts every missing server (in_repo == False) has a populated issue_type and remedy
        if not item.get('in_repo'):
            issue_type = item.get('issue_type')
            remedy = item.get('remedy')
            
            assert issue_type, f"Missing issue_type for missing server: {item.get('name')}"
            assert remedy, f"Missing remedy for missing server: {item.get('name')}"
            assert len(remedy) >= 15, f"Remedy too short for missing server: {item.get('name')}"
            
    for group, count in groups.items():
        assert count == 200, f"Expected 200 items for group '{group}', but got {count}."

