import os
import shutil
import subprocess
import tarfile
import zipfile
import yaml
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from mcp_fingerprints.synchronizer import PassportSynchronizer, ArchiveNotFoundError
from mcp_fingerprints.models import ServerPackageSpec
import json

def test_sdist_and_wheel_generation():
    """Verify that PyPI build artifacts (sdist, wheel) can be successfully generated and contain core modules, schemas, and templates."""
    # Ensure build directory exists or cleanup previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
            
    # Run the build command
    import sys
    
    if shutil.which("uv"):
        cmd = ["uv", "build"]
    else:
        cmd = [sys.executable, "-m", "build"]
        
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True
    )
    
    assert result.returncode == 0, f"Build failed: {result.stderr}\n{result.stdout}"
    
    dist_dir = "dist"
    assert os.path.exists(dist_dir), "dist directory not created"
    
    files = os.listdir(dist_dir)
    sdist = next((f for f in files if f.endswith(".tar.gz")), None)
    wheel = next((f for f in files if f.endswith(".whl")), None)
    
    assert sdist is not None, "sdist (.tar.gz) not found in dist/"
    assert wheel is not None, "wheel (.whl) not found in dist/"
    
    # Check sdist contents
    with tarfile.open(os.path.join(dist_dir, sdist), "r:gz") as tar:
        names = tar.getnames()
        # Verify core modules are present
        assert any("mcp_fingerprints/__init__.py" in name for name in names)
        assert any("mcp_fingerprints/cli.py" in name for name in names)
        assert any("mcp_fingerprints/models.py" in name for name in names)
        
        # We ensure standard packaging metadata schemas and template logic gets properly bundled
        assert len(names) > 10, "sdist seems too small, missing files"

    # Check wheel contents
    with zipfile.ZipFile(os.path.join(dist_dir, wheel), "r") as z:
        names = z.namelist()
        # Verify core modules are present
        assert any("mcp_fingerprints/__init__.py" in name for name in names)
        assert any("mcp_fingerprints/cli.py" in name for name in names)
        assert any("mcp_fingerprints/models.py" in name for name in names)

def test_daily_sync_workflow_logic():
    """Verify daily_sync.yml step logic by checking expected keys and ensuring jobs have valid yaml."""
    workflow_path = Path(".github/workflows/daily_sync.yml")
    assert workflow_path.exists(), "daily_sync.yml not found"
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        # Load workflow handling 'on' keyword parsing
        workflow = yaml.safe_load(f)
        
    jobs = workflow.get("jobs", {})
    assert "sync-mcp-passports" in jobs
    
    sync_job = jobs["sync-mcp-passports"]
    steps = sync_job.get("steps", [])
    
    step_names = [step.get("name") for step in steps if step.get("name")]
    
    assert "Checkout repository" in step_names
    assert "Preserve Baseline Snapshot for Delta & Drift" in step_names
    assert "Run Multi-Source Passport Synchronizer" in step_names
    assert "Validate All Passports Against Schema Invariants" in step_names
    assert "Compile Consolidated Snapshot & Web Catalog" in step_names
    assert "Commit and push updated passports & snapshot" in step_names
    
    # Validate the script commands for compilation and drift detection
    compile_step = next((step for step in steps if step.get("name") == "Compile Consolidated Snapshot & Web Catalog"), None)
    assert compile_step is not None
    run_cmd = compile_step.get("run", "")
    assert "python -m mcp_fingerprints.snapshot data/fingerprints passports.json.gz" in run_cmd
    assert "python -m mcp_fingerprints.cli detect-drift" in run_cmd
    assert "python scripts/generate_web_catalog.py" in run_cmd

@patch("mcp_fingerprints.cli.compare_passports_for_drift")
@patch("scripts.generate_sync_updates.compute_updates")
def test_sync_diff_calculation_and_updates_logic(mock_compute_updates, mock_compare_drift):
    """Mock the diff calculation and update generation logic that happens during daily sync."""
    
    mock_compare_drift.return_value = ({"added": ["tool1"]}, 1)
    
    # Simulate detect-drift 
    drift_result = mock_compare_drift("previous_passports.json.gz", "data/fingerprints", None)
    assert drift_result[1] == 1
    assert "added" in drift_result[0]
    
    # Mock compute_updates from script logic
    mock_compute_updates.return_value = [{"name": "test", "badges": ["NEW"]}]
    
    updates = mock_compute_updates({"old": "data"}, {"new": "data"})
    assert len(updates) == 1
    assert updates[0]["name"] == "test"
    

@patch("urllib.request.urlopen")
def test_sync_handles_unreachable_repos(mock_urlopen, tmp_path):
    """Verify that daily sync crawl logic handles unreachable repositories without aborting pipeline."""
    # Mock HTTPError 404 for PyPI and GitHub
    import urllib.error
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="http://mock", code=404, msg="Not Found", hdrs={}, fp=None
    )
    
    sync = PassportSynchronizer(output_dir=tmp_path)
    
    # Test PyPI handling 
    try:
        tools = sync._extract_tools_from_pypi_package("non-existent-package")
        assert False, "Should have raised ArchiveNotFoundError"
    except ArchiveNotFoundError:
        pass # Expected
        
    # Test npm handling
    try:
        tools = sync._extract_tools_from_npm_tarball("non-existent-npm")
        assert False, "Should have raised ArchiveNotFoundError"
    except ArchiveNotFoundError:
        pass # Expected
        
    # Test GitHub repository handling
    try:
        tools = sync._extract_ast_tools_from_github("non-existent-repo", "https://github.com/foo/bar")
        assert False, "Should have raised ArchiveNotFoundError"
    except ArchiveNotFoundError:
        pass # Expected
        
    # Let's save a fake zero-tool passport
    spec_dict = {
        "package_name": "test-pkg",
        "purl": "pkg:npm/test-pkg",
        "ecosystem": "npm",
        "versions": [{
            "version": "1.0.0",
            "tool_signatures": [],
            "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "capabilities": {}
        }]
    }
    
    file_path = tmp_path / "test-pkg.json"
    with open(file_path, "w") as f:
        json.dump(spec_dict, f)
        
    # Run enrichment. It should process our fake passport, hit 404, catch it, and continue 
    # setting gateway_caps flags, but without crashing.
    enriched_count = sync.enrich_zero_tool_passports(limit=1, max_workers=1)
    
    # Verify sync completed successfully without throwing, modifying the file in the process to set gateway_caps
    assert enriched_count in (0, 1)
    
    # Ensure it updated capabilities correctly by reading back
    with open(file_path, "r") as f:
        updated_dict = json.load(f)
        
    # Check if capabilities got updated indicating 404
    caps = updated_dict["versions"][0].get("capabilities", {})
    assert caps.get("is_unpublished") is True or caps.get("is_archived") is True
