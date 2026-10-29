import pytest
from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor

def test_json_manifest():
    auditor = DeepZeroToolAuditor()
    content = '{"tools": [{"name": "my_tool", "description": "test"}]}'
    tools = auditor.inspect_file("mcp.json", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "my_tool"
    assert tools[0]["format"] == "JSON Config"

def test_openapi_spec():
    auditor = DeepZeroToolAuditor()
    content = '{"openapi": "3.0.0", "paths": {"/test": {"get": {"operationId": "test_op"}}}}'
    tools = auditor.inspect_file("openapi.json", content)
    assert len(tools) == 1
    assert tools[0]["format"] == "OpenAPI / Swagger Spec"
    assert tools[0]["name"] == "test_op"

def test_markdown_table():
    auditor = DeepZeroToolAuditor()
    content = """
# Tools
| Tool | Description | Arguments |
|---|---|---|
| search | Search data | query |
| read | Read data | id |
    """
    tools = auditor.inspect_file("README.md", content)
    assert len(tools) == 2
    assert tools[0]["name"] == "search"
    assert tools[1]["name"] == "read"
    assert tools[0]["format"] == "Markdown Table"

def test_ts_dynamic_array():
    auditor = DeepZeroToolAuditor()
    content = """
    const TOOLS = [{name: "test"}];
    TOOLS.forEach(t => server.tool(t.name, ...));
    """
    tools = auditor.inspect_file("index.ts", content)
    assert len(tools) == 1
    assert tools[0]["format"] == "Dynamic Array Iteration"

def test_py_custom_decorator():
    auditor = DeepZeroToolAuditor()
    content = """
@action(description="test")
def my_custom_tool():
    pass
    """
    tools = auditor.inspect_file("tools.py", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "my_custom_tool"
    assert tools[0]["format"] == "Custom Decorators"

def test_ts_register_tool():
    auditor = DeepZeroToolAuditor()
    content = """
    server.registerTool("myTsTool", "test", ...);
    """
    tools = auditor.inspect_file("index.ts", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "myTsTool"
    assert tools[0]["format"] == "Explicit Tool Registration"

def test_ts_server_tool():
    auditor = DeepZeroToolAuditor()
    content = """
    server.tool('myOtherTsTool', ...);
    """
    tools = auditor.inspect_file("index.ts", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "myOtherTsTool"
    assert tools[0]["format"] == "Explicit Tool Registration"

def test_py_explicit_tool():
    auditor = DeepZeroToolAuditor()
    content = """
    t = Tool(name="myPyTool", description="test")
    """
    tools = auditor.inspect_file("tools.py", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "myPyTool"
    assert tools[0]["format"] == "Explicit Tool Instantiation"

def test_skip_secondary_markdown_tables():
    from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor
    auditor = DeepZeroToolAuditor()
    
    content = """
## Tools
| Tool | Description |
| --- | --- |
| old_tool | Removed in v2 |
    """
    
    # Should skip
    tools = auditor.inspect_file("CHANGELOG.md", content)
    assert len(tools) == 0
    tools = auditor.inspect_file("MIGRATION.md", content)
    assert len(tools) == 0
    tools = auditor.inspect_file(".cursor/skills/test.md", content)
    assert len(tools) == 0
    
    # Should keep
    tools = auditor.inspect_file("README.md", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "old_tool"
    assert tools[0]["format"] == "Markdown Table"

def test_smithery_url_resolution_pypi(monkeypatch):
    import urllib.request
    import json
    from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor
    
    class MockResponse:
        def read(self):
            return json.dumps({
                "info": {
                    "project_urls": {
                        "Source": "https://github.com/mock-owner/mock-repo"
                    }
                }
            }).encode()
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    def mock_urlopen(req, *args, **kwargs):
        if "pypi.org" in req.full_url:
            return MockResponse()
        elif "api.github.com/repos/mock-owner/mock-repo" in req.full_url:
             class MockGitTree:
                  def read(self):
                      return json.dumps({
                          "tree": []
                      }).encode()
                  def __enter__(self): return self
                  def __exit__(self, *args): pass
             return MockGitTree()
        raise urllib.error.URLError("Unexpected URL")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    auditor = DeepZeroToolAuditor()
    result = auditor.audit("https://smithery.ai/servers/mock-package", "pypi", "mock-package")
    
    assert result["status"] in ["CONFIRMED_ZERO_TOOLS: NO_TOOLS_FOUND_IN_SOURCE", "CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK"]
    assert result["tools_found_count"] == 0
