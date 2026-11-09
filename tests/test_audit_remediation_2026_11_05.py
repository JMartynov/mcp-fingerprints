import pytest
from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor

def test_markdown_exclusions():
    auditor = DeepZeroToolAuditor()
    markdown_content = "| Tool | Description |\n|---|---|\n| test_tool | testing |"

    # Should be excluded
    assert auditor.inspect_file("docs/design/visimark-simulate-mcp-tool-plan.md", markdown_content) == []
    assert auditor.inspect_file("skills/references/autoloop.md", markdown_content) == []
    assert auditor.inspect_file("skills/image-prompting/SKILL.md", markdown_content) == []
    assert auditor.inspect_file("docs/some-plan.md", markdown_content) == []
    assert auditor.inspect_file("/path/to/design/doc.md", markdown_content) == []

    # Should not be excluded (unless handled differently, but we mock standard parser logic)
    # the fallback only looks for `| Tool |` so we use that. Also it expects an empty line after, or we can use a tools section.
    valid_markdown_content = "## Tools\n| Tool | Description |\n|---|---|\n| test_tool | testing |"
    res = auditor.inspect_file("README.md", valid_markdown_content)
    # The default basic parser fallback logic or doc_parser will catch it:
    assert len(res) > 0
    assert res[0]["name"] == "test_tool" or res[0]["name"] == "unknown_tool"

def test_json_manifest_extraction():
    auditor = DeepZeroToolAuditor()
    json_content = '{"tools": [{"name": "test_json_tool", "description": "test"}]}'
    res = auditor.inspect_file("server.json", json_content)
    assert len(res) == 1
    assert res[0]["name"] == "test_json_tool"
    
    res2 = auditor.inspect_file(".well-known/mcp/server-card.json", json_content)
    assert len(res2) == 1
    assert res2[0]["name"] == "test_json_tool"

def test_ts_explicit_registration():
    auditor = DeepZeroToolAuditor()
    ts_content = 'server.registerTool("test_ts_tool", async () => {});'
    res = auditor.inspect_file("src/tools.ts", ts_content)
    assert len(res) == 1
    assert res[0]["name"] == "test_ts_tool"

def test_status_mappings():
    from mcp_fingerprints.deep_zero_tool_auditor import map_audit_to_status
    server_card = {"name": "test", "ecosystem": "npm", "tool_count": 5}
    
    # UNRESOLVED_SOURCE
    res = map_audit_to_status(server_card, {"status": "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"})
    assert res["match_status"] == "UNRESOLVED_SOURCE"
    assert res["root_cause"] == "UNRESOLVED_OR_MISSING_SOURCE"
    
    # MISMATCH
    res2 = map_audit_to_status(server_card, {"status": "CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK"})
    assert res2["match_status"] == "MISMATCH"
    assert res2["root_cause"] == "CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK"
    assert res2["source_tools"] == 0
