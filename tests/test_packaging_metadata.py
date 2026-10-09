import os
import yaml
import tomli


def test_pyproject_toml_metadata():
    """Test that pyproject.toml contains the required PyPI metadata."""
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    assert os.path.exists(pyproject_path)

    with open(pyproject_path, "rb") as f:
        pyproject = tomli.load(f)

    project = pyproject.get("project", {})

    # Check version
    assert "version" in project
    assert isinstance(project["version"], str)

    # Check authors
    assert "authors" in project
    assert any(
        author.get("name") == "MCP Fingerprints Contributors"
        for author in project["authors"]
    )

    # Check license
    assert "license" in project
    assert project["license"].get("text") == "MIT"

    # Check keywords
    assert "keywords" in project
    expected_keywords = [
        "mcp",
        "model-context-protocol",
        "security",
        "fingerprints",
        "ai-agents",
        "llm",
    ]
    for keyword in expected_keywords:
        assert keyword in project["keywords"]

    # Check classifiers
    assert "classifiers" in project
    expected_classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ]
    for classifier in expected_classifiers:
        assert classifier in project["classifiers"]

    # Check urls
    urls = project.get("urls", {})
    assert urls.get("Homepage") == "https://jmartynov.github.io/mcp-fingerprints/"
    assert urls.get("Repository") == "https://github.com/JMartynov/mcp-fingerprints"
    assert urls.get("Issues") == "https://github.com/JMartynov/mcp-fingerprints/issues"

    # Check entry points
    scripts = project.get("scripts", {})
    assert scripts.get("mcp-fingerprints") == "mcp_fingerprints.cli:main"

    # Check dependencies
    assert "dependencies" in project
    assert any("packaging" in dep for dep in project["dependencies"])


def test_release_yml_workflow():
    """Test that the release.yml workflow has the correct syntax and jobs."""
    workflow_path = os.path.join(
        os.path.dirname(__file__), "..", ".github", "workflows", "release.yml"
    )
    assert os.path.exists(workflow_path)

    with open(workflow_path, "r") as f:
        workflow = yaml.safe_load(f)

    # Check trigger conditions
    # Note: 'on' parses as True in some YAML loaders
    on = workflow.get("on") or workflow.get(True, {})
    assert "release" in on
    assert on["release"].get("types") == ["published"]
    assert "workflow_dispatch" in on

    # Check permissions
    permissions = workflow.get("permissions", {})
    assert permissions.get("id-token") == "write"
    assert permissions.get("contents") == "read"

    # Check jobs
    jobs = workflow.get("jobs", {})
    assert "build" in jobs
    assert "publish" in jobs

    # Check publish job uses trusted publishing
    publish = jobs["publish"]
    assert publish.get("needs") == "build"

    # Verify the PyPI publish action is used
    steps = publish.get("steps", [])
    publish_step = next(
        (
            step
            for step in steps
            if step.get("uses", "").startswith("pypa/gh-action-pypi-publish")
        ),
        None,
    )
    assert publish_step is not None
    assert publish_step.get("with", {}).get("skip-existing") is True


def test_test_release_yml_workflow():
    """Test that the test_release.yml workflow has the correct syntax and jobs."""
    workflow_path = os.path.join(
        os.path.dirname(__file__), "..", ".github", "workflows", "test_release.yml"
    )
    assert os.path.exists(workflow_path)

    with open(workflow_path, "r") as f:
        # Load yaml and map True to 'on' keyword issue
        workflow = yaml.safe_load(f)

    # Check trigger conditions
    on = workflow.get("on") or workflow.get(True, {})
    assert "workflow_dispatch" in on
    inputs = on["workflow_dispatch"].get("inputs", {})
    assert "version_suffix" in inputs
    assert "skip_smoke_test" in inputs

    # Check permissions
    permissions = workflow.get("permissions", {})
    assert permissions.get("id-token") == "write"
    assert permissions.get("contents") == "read"

    # Check jobs
    jobs = workflow.get("jobs", {})
    assert "build" in jobs
    assert "publish" in jobs
    assert "smoke-test" in jobs

    # Check publish job uses trusted publishing for TestPyPI
    publish = jobs["publish"]
    assert publish.get("needs") == "build"

    # Verify the PyPI publish action is used and points to testpypi
    steps = publish.get("steps", [])
    publish_step = next(
        (
            step
            for step in steps
            if step.get("uses", "").startswith("pypa/gh-action-pypi-publish")
        ),
        None,
    )
    assert publish_step is not None
    assert (
        publish_step.get("with", {}).get("repository-url")
        == "https://test.pypi.org/legacy/"
    )

    # Check smoke-test job
    smoke_test = jobs["smoke-test"]
    assert smoke_test.get("needs") == "publish"
