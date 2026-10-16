import json
import gzip
from pathlib import Path
import pytest
from src.mcp_fingerprints.snapshot import build_snapshot

def test_sync_updates_script_computes_new_server(tmp_path):
    old_data = {
        "passports": {
            "existing-server": {
                "package_name": "existing-server",
                "ecosystem": "npm",
                "versions": [{"version": "1.0.0", "tool_signatures": [{"name": "tool1"}]}]
            }
        }
    }
    
    new_data = {
        "passports": {
            "existing-server": {
                "package_name": "existing-server",
                "ecosystem": "npm",
                "versions": [{"version": "1.0.0", "tool_signatures": [{"name": "tool1"}]}]
            },
            "new-server": {
                "package_name": "new-server",
                "ecosystem": "pypi",
                "description": "A new server",
                "versions": [{"version": "0.1.0", "tool_signatures": [{"name": "new_tool", "description": "test"}]}]
            }
        }
    }
    
    old_file = tmp_path / "old.json"
    new_file = tmp_path / "new.json"
    
    old_file.write_text(json.dumps(old_data))
    new_file.write_text(json.dumps(new_data))
    
    import sys
    sys.path.insert(0, ".")
    from scripts.generate_sync_updates import compute_updates, load_snapshot
    
    updates = compute_updates(load_snapshot(old_file), load_snapshot(new_file))
    
    assert len(updates) == 1
    assert updates[0]["name"] == "new-server"
    assert "NEW SERVER" in updates[0]["badges"]

def test_sync_updates_script_computes_new_version(tmp_path):
    old_data = {
        "passports": {
            "existing-server": {
                "package_name": "existing-server",
                "ecosystem": "npm",
                "versions": [{"version": "1.0.0", "tool_signatures": [{"name": "tool1"}]}]
            }
        }
    }
    
    new_data = {
        "passports": {
            "existing-server": {
                "package_name": "existing-server",
                "ecosystem": "npm",
                "versions": [{"version": "1.1.0", "tool_signatures": [{"name": "tool1"}, {"name": "tool2"}]}]
            }
        }
    }
    
    old_file = tmp_path / "old.json"
    new_file = tmp_path / "new.json"
    
    old_file.write_text(json.dumps(old_data))
    new_file.write_text(json.dumps(new_data))
    
    from scripts.generate_sync_updates import compute_updates, load_snapshot
    
    updates = compute_updates(load_snapshot(old_file), load_snapshot(new_file))
    
    assert len(updates) == 1
    assert updates[0]["name"] == "existing-server"
    assert "NEW VERSION" in updates[0]["badges"]
    assert "+1 TOOLS ADDED" in updates[0]["badges"]

def test_sync_updates_script_computes_params_updated(tmp_path):
    old_data = {
        "passports": {
            "existing-server": {
                "package_name": "existing-server",
                "versions": [{"version": "1.0.0", "tool_signatures": [{"name": "tool1", "inputSchema": {"type": "object", "properties": {"a": {"type": "string"}}}}]}]
            }
        }
    }
    
    new_data = {
        "passports": {
            "existing-server": {
                "package_name": "existing-server",
                "versions": [{"version": "1.0.0", "tool_signatures": [{"name": "tool1", "inputSchema": {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "number"}}}}]}]
            }
        }
    }
    
    old_file = tmp_path / "old.json"
    new_file = tmp_path / "new.json"
    
    old_file.write_text(json.dumps(old_data))
    new_file.write_text(json.dumps(new_data))
    
    from scripts.generate_sync_updates import compute_updates, load_snapshot
    
    updates = compute_updates(load_snapshot(old_file), load_snapshot(new_file))
    
    assert len(updates) == 1
    assert updates[0]["name"] == "existing-server"
    assert "PARAMETERS UPDATED" in updates[0]["badges"]

def test_daily_sync_workflow_hardened():
    content = Path(".github/workflows/daily_sync.yml").read_text()
    
    # Check for excluded volatile state files
    assert "grep -v" in content
    assert "sync_state.json" in content
    assert "index.json" in content
    assert ".passport_index.pickle" in content
    
    # Check that update generator is called
    assert "python scripts/generate_sync_updates.py --old previous_passports.json.gz --new passports.json.gz --version" in content

