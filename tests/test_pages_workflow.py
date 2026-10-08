import yaml
from pathlib import Path

def test_deploy_pages_workflow():
    workflow_path = Path(".github/workflows/deploy_pages.yml")
    assert workflow_path.exists(), "deploy_pages.yml workflow file should exist"
    
    with open(workflow_path, "r") as f:
        workflow = yaml.safe_load(f)
        
    on = workflow.get("on", workflow.get(True))
    assert on is not None
    assert "push" in on
    assert "main" in on["push"]["branches"]
    assert "web/**" in on["push"]["paths"]
    assert "scripts/generate_web_catalog.py" in on["push"]["paths"]
    assert "workflow_dispatch" in on
    
    assert "permissions" in workflow
    assert workflow["permissions"].get("contents") == "read"
    assert workflow["permissions"].get("pages") == "write"
    assert workflow["permissions"].get("id-token") == "write"
    
    assert "jobs" in workflow
    assert "deploy" in workflow["jobs"]
    
    steps = workflow["jobs"]["deploy"]["steps"]
    
    uses = [step.get("uses") for step in steps if "uses" in step]
    
    assert "actions/upload-pages-artifact@v3" in uses
    assert "actions/deploy-pages@v4" in uses

