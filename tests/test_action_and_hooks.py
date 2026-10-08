import os
import yaml
from pathlib import Path

def test_action_yml_validity():
    action_path = Path("action.yml")
    assert action_path.exists(), "action.yml should exist in the root directory"
    
    with open(action_path, "r", encoding="utf-8") as f:
        action_data = yaml.safe_load(f)
        
    assert action_data["name"] == "Audit MCP Client Configuration"
    assert "description" in action_data
    
    inputs = action_data.get("inputs", {})
    assert "config-file" in inputs
    assert "passports-dir" in inputs
    assert "fail-on-critical" in inputs
    assert "json-output" in inputs
    
    runs = action_data.get("runs", {})
    assert runs.get("using") == "composite"
    
    steps = runs.get("steps", [])
    assert len(steps) >= 1
    
    run_cmd = steps[0].get("run", "")
    assert "mcp_fingerprints.cli audit-config" in run_cmd
    assert "${{ inputs.config-file }}" in run_cmd


def test_pre_commit_hooks_yaml_validity():
    hook_path = Path(".pre-commit-hooks.yaml")
    assert hook_path.exists(), ".pre-commit-hooks.yaml should exist in the root directory"
    
    with open(hook_path, "r", encoding="utf-8") as f:
        hooks_data = yaml.safe_load(f)
        
    assert isinstance(hooks_data, list)
    assert len(hooks_data) >= 1
    
    hook = hooks_data[0]
    assert hook["id"] == "mcp-audit-config"
    assert hook["name"] == "MCP Client Configuration Auditor"
    assert "description" in hook
    assert hook["entry"] == "mcp-fingerprints audit-config"
    assert hook["language"] == "python"
    
    files_regex = hook.get("files", "")
    assert "claude_desktop_config\\.json" in files_regex
    assert "cursor_settings\\.json" in files_regex
    assert ".*mcp.*\\.json" in files_regex

