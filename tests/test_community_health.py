import os
from pathlib import Path


def test_contributing_md_exists_and_content():
    path = Path("CONTRIBUTING.md")
    assert path.exists(), "CONTRIBUTING.md does not exist"
    content = path.read_text().lower()
    
    assert "development setup" in content
    assert "running tests" in content
    assert "contributing passports" in content or "new mcp server" in content
    assert "security" in content


def test_issue_templates_exist_and_non_empty():
    templates = [
        "bug_report.md",
        "feature_request.md",
        "new_mcp_server.md"
    ]
    for template in templates:
        path = Path(f".github/ISSUE_TEMPLATE/{template}")
        assert path.exists(), f"Issue template {template} does not exist"
        content = path.read_text().strip()
        assert len(content) > 0, f"Issue template {template} is empty"


def test_pull_request_template_exists_and_content():
    path = Path(".github/pull_request_template.md")
    assert path.exists(), "Pull request template does not exist"
    content = path.read_text().lower()
    
    assert "tests pass locally" in content
    assert "documentation updated" in content
    assert "pre-commit hooks run cleanly" in content


def test_release_template_exists_and_content():
    path = Path(".github/RELEASE_TEMPLATE.md")
    assert path.exists(), "Release template does not exist"
    content = path.read_text().lower()
    
    assert "testpypi" in content
    assert "release" in content
    assert "v" in content # e.g. vx.y.z
