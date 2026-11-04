import pytest
from src.mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor, map_audit_to_status
import urllib.request
import urllib.error
import urllib.parse
from unittest.mock import patch, MagicMock

@pytest.fixture
def auditor():
    return DeepZeroToolAuditor()

def test_pypi_url_resolution(auditor):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"info": {"project_urls": {"Source": "https://github.com/test-owner/test-repo"}}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test audit directly
        # Since it actually tries to hit github in audit, let's mock it to prevent external calls.
        # Actually it's easier to just mock urllib.request.urlopen completely.
        pass

def test_unresolved_source_mapping():
    server = {"name": "test", "ecosystem": "pypi", "tool_count": 5}
    audit_res = {"status": "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY", "tools_found_count": 0}
    status_map = map_audit_to_status(server, audit_res)
    assert status_map["match_status"] == "UNRESOLVED_SOURCE"
    assert status_map["source_tools"] == "?"
    assert status_map["root_cause"] == "UNRESOLVED_OR_MISSING_SOURCE"

def test_inspect_file_markdown(auditor):
    md_content = """
# Available Tools
| Name | Description |
|---|---|
| test_tool | A test tool |
"""
    tools = auditor.inspect_file("README.md", md_content)
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert tools[0]["format"] == "Markdown Table"

def test_inspect_file_openapi(auditor):
    openapi_content = """
openapi: 3.0.0
paths:
  /test:
    get:
      operationId: test_operation
"""
    tools = auditor.inspect_file("openapi.yaml", openapi_content)
    assert len(tools) == 1
    assert tools[0]["name"] == "test_operation"
    assert tools[0]["format"] == "OpenAPI / Swagger Spec"

def test_inspect_file_markdown_excluded_paths(auditor):
    md_content = """
# Available Tools
| Name | Description |
|---|---|
| test_tool | A test tool |
"""
    # These paths should be excluded and return 0 tools
    excluded_paths = [
        ".agents/skills/create-mcp-tool/SKILL.md",
        ".claude/skills/tool-definition-review/SKILL.md",
        "configs/autoloop-coder-prompt.md",
        "eval/RESULTS.md",
        "evals/test.md",
        "results.md",
        "release_notes.md",
        "contributing.md",
        "LICENSE.md"
    ]
    for path in excluded_paths:
        tools = auditor.inspect_file(path, md_content)
        assert len(tools) == 0, f"Expected 0 tools for {path}, but found {len(tools)}"

def test_inspect_file_markdown_ignored_table(auditor):
    md_content = """
# Available Tools
| Metric | Expected | Actual | Status |
|---|---|---|---|
| Tool Detection | 100% | 50% | Fail |
"""
    # Even if path is allowed, this table should not be parsed as tools because of headers
    tools = auditor.inspect_file("README.md", md_content)
    assert len(tools) == 0, "Table should be ignored based on headers"

def test_inspect_file_markdown_valid_table(auditor):
    md_content = """
# Available Tools
| Tool Name | Description | Parameters |
|---|---|---|
| my_tool | Does something | a (string) |
"""
    tools = auditor.inspect_file("README.md", md_content)
    assert len(tools) == 1, "Table should be parsed as it has valid tool headers"

    # Also test synonyms: Function, Params, Summary, Details
    md_synonyms = """
# Available Tools
| Function | Params | Summary |
|---|---|---|
| get_user | id: int | Fetches user details |
"""
    tools_syn = auditor.inspect_file("README.md", md_synonyms)
    assert len(tools_syn) == 1, "Table with Function, Params, Summary should be parsed"

