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


def test_pre_commit_config_yaml_validity():
    config_path = Path(".pre-commit-config.yaml")
    assert config_path.exists(), ".pre-commit-config.yaml should exist in the root directory"

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    assert isinstance(config_data, dict)
    assert "repos" in config_data
    repos = config_data["repos"]
    assert isinstance(repos, list)

    repo_map = {r.get("repo"): r for r in repos if isinstance(r, dict)}

    # Verify ruff-pre-commit hooks
    assert "https://github.com/astral-sh/ruff-pre-commit" in repo_map
    ruff_hooks = [h.get("id") for h in repo_map["https://github.com/astral-sh/ruff-pre-commit"].get("hooks", [])]
    assert "ruff" in ruff_hooks
    assert "ruff-format" in ruff_hooks

    # Verify standard hygiene hooks
    assert "https://github.com/pre-commit/pre-commit-hooks" in repo_map
    hygiene_hooks = [h.get("id") for h in repo_map["https://github.com/pre-commit/pre-commit-hooks"].get("hooks", [])]
    assert "trailing-whitespace" in hygiene_hooks
    assert "end-of-file-fixer" in hygiene_hooks
    assert "check-yaml" in hygiene_hooks

    # Verify local mcp-audit-config hook
    assert "local" in repo_map
    local_hooks = repo_map["local"].get("hooks", [])
    mcp_hook = next((h for h in local_hooks if h.get("id") == "mcp-audit-config"), None)
    assert mcp_hook is not None, "mcp-audit-config local hook should be defined"
    assert "python -m mcp_fingerprints.cli audit-config" in mcp_hook.get("entry", "")


def test_test_action_workflow_validity():
    workflow_path = Path(".github/workflows/test_action.yml")
    assert workflow_path.exists(), "test_action.yml workflow should exist"

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_data = yaml.safe_load(f)

    assert workflow_data.get("name") == "Test Reusable Action"
    assert "jobs" in workflow_data
    assert "test-action" in workflow_data["jobs"]
    steps = workflow_data["jobs"]["test-action"].get("steps", [])

    step_uses = [s.get("uses", "") for s in steps]
    assert "./" in step_uses


