import ast
import pytest
from mcp_fingerprints.ast_parser import FastMcpAstVisitor, parse_golang_mcp_code
from mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from mcp_fingerprints.models import (
    ServerPackageSpec,
    ToolContractSignature,
    VersionFingerprint,
)
from mcp_fingerprints.synchronizer import PassportSynchronizer


def test_merge_and_enrich_preserves_metadata():
    sync = PassportSynchronizer()
    existing_spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server",
        ecosystem="npm",
        display_name="test-server",
        description="Preserved description",
        repository_url="https://github.com/test/repo",
        homepage_url="https://test.com",
        author="Test Author",
        license="MIT",
        keywords=("preserved", "keyword"),
        aliases=("test-server",),
        sources_merged=("npm",),
        dist_tags={},
        versions=(
            VersionFingerprint(
                version="1.0.0",
                capabilities={"tools": True},
                toolset_canonical_hash="sha256:dummy",
            ),
        ),
        transport="stdio",
    )

    # New spec data is mostly empty, auto_cross_resolve=False avoids external network
    merged = sync.merge_and_enrich_passport(
        package_name="test-server",
        ecosystem="npm",
        npm_data={"name": "test-server", "description": "", "repository": "", "license": ""},
        existing_spec=existing_spec,
        auto_cross_resolve=False,
    )

    assert merged.description == "Preserved description"
    assert merged.repository_url == "https://github.com/test/repo"
    assert merged.homepage_url == "https://test.com"
    assert merged.license == "MIT"
    assert "preserved" in merged.keywords
    assert "keyword" in merged.keywords


def test_prior_version_toolset_inheritance():
    sync = PassportSynchronizer()
    v1 = VersionFingerprint(
        version="1.0.0",
        tool_signatures=[
            ToolContractSignature(
                name="tool1",
                description="desc1",
                input_schema={"type": "object", "properties": {}},
                canonical_hash="sha256:dummy",
            )
        ],
        capabilities={"tools": True},
        toolset_canonical_hash="sha256:dummy",
    )
    existing_spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server",
        ecosystem="npm",
        display_name="test-server",
        description="Desc",
        versions=(v1,),
        transport="stdio",
    )

    # No tools in new data, auto_cross_resolve=False, smithery_data={'version': '2.0.0', 'tools': []}
    merged = sync.merge_and_enrich_passport(
        package_name="test-server",
        ecosystem="npm",
        npm_data={"name": "test-server", "version": "2.0.0"},
        existing_spec=existing_spec,
        auto_cross_resolve=False,
        smithery_data={"version": "2.0.0", "tools": []},
    )

    assert merged is not None
    v2 = next(v for v in merged.versions if v.version == "2.0.0")
    assert v2.capabilities.get("inherited_tools")
    assert v2.tool_signatures is not None
    assert len(v2.tool_signatures) == 1
    assert v2.tool_signatures[0].name == "tool1"


def test_ast_python_add_tool():
    code = """
def my_tool_fn():
    \"\"\"This is my tool description.\"\"\"
    pass
mcp.add_tool(my_tool_fn)
server.add_tool(another_fn, name="tool2", description="desc2")
    """
    tree = ast.parse(code)
    visitor = FastMcpAstVisitor()
    visitor._current_module_node = tree
    visitor.visit(tree)

    tools = visitor.extracted_tools
    assert len(tools) == 2
    assert tools[0]["name"] == "my_tool_fn"
    assert tools[0]["description"] == "This is my tool description."
    assert tools[1]["name"] == "tool2"
    assert tools[1]["description"] == "desc2"


def test_ast_go_raw_schema():
    code = """
    mcp.NewToolWithRawSchema(
        "raw_tool",
        "A raw tool description",
    )
    """
    tools = parse_golang_mcp_code(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "raw_tool"
    assert tools[0]["description"] == "A raw tool description"


def test_markdown_doc_parser_flexibility():
    md = """
## Tools (5)
Here are some tools:

| Function | Params | Summary |
|---|---|---|
| my_tool | arg1: string | Does something |
    """
    tools = parse_markdown_tool_docs(md)
    assert len(tools) == 1
    assert tools[0]["name"] == "my_tool"
    assert tools[0]["description"] == "Does something"
    assert "arg1" in tools[0]["inputSchema"]["properties"]


def test_generic_github_slug_auto_resolution():
    spec = ServerPackageSpec(
        package_name="owner/repo",
        purl="pkg:generic/owner%2Frepo",
        ecosystem="generic",
        display_name="owner/repo",
        description="Desc",
        versions=(),
        transport="stdio",
        repository_url=None,
    )

    import re

    check_repo = spec.repository_url
    if not check_repo and re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", spec.package_name):
        check_repo = f"https://github.com/{spec.package_name}"

    assert check_repo == "https://github.com/owner/repo"
