import json
import os

def test_audit_group_5_json_exists():
    assert os.path.exists('docs/research/audit_group_5_monorepo_docker_emerging.json')

def test_audit_group_5_json_count():
    with open('docs/research/audit_group_5_monorepo_docker_emerging.json') as f:
        data = json.load(f)
    assert len(data) == 200

def test_audit_group_5_missing_entries_have_issue_and_remedy():
    with open('docs/research/audit_group_5_monorepo_docker_emerging.json') as f:
        data = json.load(f)
        
    for entry in data:
        if not entry['in_repo']:
            assert entry.get('issue_type'), f"Missing issue_type for {entry['name']}"
            assert entry.get('remedy'), f"Missing remedy for {entry['name']}"

def test_audit_group_5_markdown_exists():
    assert os.path.exists('docs/research/audit_group_5_monorepo_docker_emerging.md')

