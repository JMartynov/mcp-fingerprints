import pytest
from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor, map_audit_to_status
import json

def test_exclusion_of_design_plans():
    auditor = DeepZeroToolAuditor()
    content = """
| Tool | Description |
|---|---|
| fake_tool | Some theoretical tool |
    """
    tools = auditor.inspect_file("docs/design/visimark-simulate-mcp-tool-plan.md", content)
    assert len(tools) == 0

    tools = auditor.inspect_file("design/architecture-plan.md", content)
    assert len(tools) == 0

def test_json_config_tool_extraction():
    auditor = DeepZeroToolAuditor()
    
    # Dict format (aamio-addon.json / server.json typically)
    dict_content = json.dumps({"tools": [{"name": "test_tool_dict"}]})
    tools = auditor.inspect_file("aamio-addon.json", dict_content)
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool_dict"
    assert tools[0]["format"] == "JSON Config"

    tools = auditor.inspect_file("server.json", dict_content)
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool_dict"

    # List format
    list_content = json.dumps([{"name": "test_tool_list"}])
    tools = auditor.inspect_file("another.json", list_content)
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool_list"

def test_explicit_ts_tool_registration():
    auditor = DeepZeroToolAuditor()
    content = """
    server.tool("my_tool", () => {});
    server.registerTool("other_tool", () => {});
    server.addTool("third_tool", () => {});
    """
    tools = auditor.inspect_file("src/index.ts", content)
    assert len(tools) == 3
    names = sorted([t["name"] for t in tools])
    assert names == ["my_tool", "other_tool", "third_tool"]
    assert tools[0]["format"] == "Explicit Tool Registration"

def test_remote_gateway_categorization():
    server = {"name": "test-gateway", "tool_count": 5}
    audit_res = {"status": "CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK"}
    status = map_audit_to_status(server, audit_res)
    assert status["match_status"] == "MISMATCH"
    assert status["root_cause"] == "CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK"
    assert status["source_tools"] == 0

def test_unresolved_source_categorization():
    server = {"name": "test-repo", "tool_count": 0}
    audit_res = {"status": "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"}
    status = map_audit_to_status(server, audit_res)
    assert status["match_status"] == "UNRESOLVED_SOURCE"
    assert status["root_cause"] == "UNRESOLVED_OR_MISSING_SOURCE"
    
def test_unreachable_repo_categorization():
    server = {"name": "test-repo", "tool_count": 0}
    audit_res = {"status": "ERROR: HTTP 404"}
    status = map_audit_to_status(server, audit_res)
    assert status["match_status"] == "UNREACHABLE_REPO"
    assert status["root_cause"] == "UNREACHABLE_OR_PRIVATE_REPO"
