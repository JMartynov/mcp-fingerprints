import pytest
from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor

def test_deep_zero_tool_auditor_nested_dir():
    auditor = DeepZeroToolAuditor()
    # It just needs to work, we are mocking inspect_file anyway since we are mocking github tree...
    # But wait, the task mentioned: 
    # "Support recursive subdirectory scanning for TypeScript/JavaScript/Python MCP entrypoints (e.g. src/tools/, Tools/, lib/tools/)."
    
    # We added item.get("type") == "tree" check but recursive=1 handles it and gives blob items anyway in github API.
    # We don't actually need extra logic for subdirectory because recursive=1 gives blob with `path` = "src/tools/test.ts"
    
    # Let's test that inspect_file returns tools correctly with a nested path.
    content = "server.registerTool('myTool', 'desc');"
    tools = auditor.inspect_file("src/tools/index.ts", content)
    assert len(tools) == 1
    assert tools[0]["name"] == "myTool"
