import pytest
import yaml
from pathlib import Path

def test_e2e_workflow_syntax():
    workflow_path = Path(".github/workflows/e2e.yml")
    assert workflow_path.exists(), "Workflow file does not exist"
    
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)
        
    on_key = "on" if "on" in workflow else True
    
    assert on_key in workflow
    assert "push" in workflow[on_key]
    assert "main" in workflow[on_key]["push"]["branches"]
    assert "pull_request" in workflow[on_key]
    
    assert "jobs" in workflow
    assert "test" in workflow["jobs"]
    
    steps = workflow["jobs"]["test"]["steps"]
    
    # Check for required steps
    step_commands = [step.get("run", "") for step in steps]
    step_uses = [step.get("uses", "") for step in steps]
    
    assert any("setup-python" in use for use in step_uses)
    assert any("uv run playwright install --with-deps chromium" in cmd for cmd in step_commands)
    assert any("uv run pytest tests/test_web_pwa_e2e.py -v" in cmd for cmd in step_commands)
    
    upload_step = next(step for step in steps if "upload-artifact" in step.get("uses", ""))
    assert upload_step["if"] == "failure()"
