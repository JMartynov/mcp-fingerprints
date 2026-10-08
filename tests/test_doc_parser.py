"""Tests for Markdown Document Parser Tool Extractions."""

import json
from unittest.mock import MagicMock
from mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from mcp_fingerprints.synchronizer import PassportSynchronizer
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint


def test_parse_markdown_tables():
    content = """
# Some project

## Tools

Here are the tools:

| Tool | Description | Arguments |
| --- | --- | --- |
| `get_weather` | Get the current weather | (location: string, days: number) |
| **calculate** | Perform calculation | `expr` (string) |

## Other section
"""
    tools = parse_markdown_tool_docs(content)
    assert len(tools) == 2
    assert tools[0]["name"] == "get_weather"
    assert tools[0]["description"] == "Get the current weather"
    assert tools[0]["inputSchema"]["properties"] == {
        "location": {"type": "string"},
        "days": {"type": "number"},
    }
    assert tools[0]["inputSchema"]["required"] == ["location", "days"]
    
    assert tools[1]["name"] == "calculate"
    assert tools[1]["description"] == "Perform calculation"
    assert tools[1]["inputSchema"]["properties"] == {
        "expr": {"type": "string"},
    }
    assert tools[1]["inputSchema"]["required"] == ["expr"]


def test_parse_markdown_lists():
    content = """
# Some project

### Available Tools

* `search`: Search the web (query: string, max_results: number)
- **read_file**: Read a file
"""
    tools = parse_markdown_tool_docs(content)
    assert len(tools) == 2
    
    assert tools[0]["name"] == "search"
    assert tools[0]["description"] == "Search the web"
    assert tools[0]["inputSchema"]["properties"] == {
        "query": {"type": "string"},
        "max_results": {"type": "number"},
    }
    assert tools[0]["inputSchema"]["required"] == ["query", "max_results"]
    
    assert tools[1]["name"] == "read_file"
    assert tools[1]["description"] == "Read a file"
    assert tools[1]["inputSchema"]["properties"] == {}
    assert tools[1]["inputSchema"]["required"] == []


def test_parse_markdown_with_empty_tools_section():
    content = """
## Tools
No tools yet.
    """
    tools = parse_markdown_tool_docs(content)
    assert len(tools) == 0


def test_fallback_integration_capability_tagging(tmp_path):
    package_name = "test/fallback_pkg"
    repo_url = "https://github.com/test/fallback_pkg"
    
    spec = ServerPackageSpec(
        package_name=package_name,
        purl="pkg:generic/test%2Ffallback_pkg",
        ecosystem="generic",
        display_name=package_name,
        description="",
        repository_url=repo_url,
        license=None,
        keywords=tuple(),
        aliases=(package_name,),
        sources_merged=("github",),
        dist_tags={},
        versions=(
            VersionFingerprint(
                version="1.0.0",
                tool_signatures=tuple(),
                prompt_signatures=tuple(),
                resource_signatures=tuple(),
                capabilities={"tools": False, "prompts": False, "resources": False},
                connections=tuple(),
                toolset_canonical_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            ),
        ),
    )
    
    j_file = tmp_path / "fallback_pkg.json"
    with open(j_file, "w") as f:
        json.dump(spec.to_dict(), f)
    
    syncer = PassportSynchronizer(output_dir=tmp_path)
    syncer._extract_ast_tools_from_github = MagicMock(return_value=[])
    
    def mock_extract_readme(pkg_name, r_url):
        if pkg_name == package_name:
            return [{
                "name": "fake_tool",
                "description": "fake",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            }]
        return []
        
    syncer._extract_tools_from_github_readme = MagicMock(side_effect=mock_extract_readme)
    
    syncer.enrich_zero_tool_passports(limit=1, max_workers=1)
    
    with open(j_file, "r") as f:
        updated_spec = ServerPackageSpec.from_dict(json.load(f))
        
    assert len(updated_spec.versions) > 0
    updated_version = next(v for v in updated_spec.versions if v.version == "1.0.0")
    assert len(updated_version.tool_signatures) == 1
    assert updated_version.tool_signatures[0].name == "fake_tool"
    assert updated_version.capabilities.get("documentation_extracted_tools") is True
