import pytest

from mcp_fingerprints.ast_parser import parse_golang_mcp_code, parse_mcp_source_code
from mcp_fingerprints.canonicalizer import extract_tool_signature

IMPORT = 'import "github.com/modelcontextprotocol/go-sdk/mcp"'
SCHEMA = """map[string]any{
    "type": "object",
    "properties": map[string]any{
        "query": map[string]any{"type": "string", "description": "A }, delimiter"},
    },
    "required": []string{"query"},
    "additionalProperties": false,
}"""


def source(schema=SCHEMA, name='"search"', description='"Search records"'):
    return f"""package main
{IMPORT}
func main() {{
    server.AddTool(&mcp.Tool{{
        Name: {name}, Description: {description}, InputSchema: {schema},
    }}, handler)
}}
"""


def test_official_sdk_complete_literal_schema():
    tools = parse_golang_mcp_code(source())
    assert tools == [
        {
            "name": "search",
            "description": "Search records",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A }, delimiter"}
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        }
    ]


def test_omitted_description_matches_explicit_empty_description_metadata():
    explicit = source(description='""')
    omitted = explicit.replace('Description: "", ', "")
    (omitted_tool,) = parse_mcp_source_code(omitted, language="go")
    (explicit_tool,) = parse_mcp_source_code(explicit, language="go")
    omitted_signature = extract_tool_signature(omitted_tool)
    explicit_signature = extract_tool_signature(explicit_tool)

    assert omitted_signature.canonical_hash == explicit_signature.canonical_hash
    assert omitted_signature.description == explicit_signature.description == ""
    assert (
        omitted_signature.description_hash
        is explicit_signature.description_hash
        is None
    )
    assert omitted_tool == explicit_tool


def test_official_sdk_alias_raw_strings_comments_and_multiple_tools():
    code = source(description="`Search (all), {records}`")
    code = code.replace(
        IMPORT, 'import (sdk "github.com/modelcontextprotocol/go-sdk/mcp")'
    )
    code = code.replace("&mcp.Tool", "&sdk.Tool")
    code += """
// server.AddTool(&sdk.Tool{Name: "comment", InputSchema: map[string]any{}}, handler)
/* server.AddTool(&sdk.Tool{Name: "block", InputSchema: map[string]any{}}, handler) */
var example = `server.AddTool(&sdk.Tool{Name: "string"}, handler)`
func more() {
    s.AddTool(&sdk.Tool{InputSchema: map[string]interface{}{}, Name: "second"}, handler)
}
"""
    tools = parse_mcp_source_code(code, language="go")
    assert [t["name"] for t in tools] == ["search", "second"]
    assert tools[0]["description"] == "Search (all), {records}"
    assert tools[1]["inputSchema"] == {}
    assert tools[1]["description"] == ""


@pytest.mark.parametrize(
    "schema", ["factsSchema()", "schema", "nil", 'map[string]any{"type": kind}']
)
def test_unresolved_schema_does_not_become_empty_schema(schema, caplog):
    assert parse_golang_mcp_code(source(schema=schema)) == []
    assert "does not establish an empty toolset" in caplog.text


@pytest.mark.parametrize(
    "code",
    [
        source().replace(IMPORT, 'import "example.com/other/mcp"'),
        source().replace(
            IMPORT, 'var path = "github.com/modelcontextprotocol/go-sdk/mcp"'
        ),
        source().split("InputSchema:")[0],
        source().replace("server.AddTool(", "otherMethod("),
    ],
)
def test_unrelated_or_truncated_declarations_are_not_tools(code):
    assert parse_golang_mcp_code(code) == []


def test_unresolved_name_and_description_are_not_guessed():
    assert parse_golang_mcp_code(source(name="toolName")) == []
    assert parse_golang_mcp_code(source(description='"prefix" + suffix')) == []


def test_go_escapes_and_nested_schema_values():
    code = source(
        name=r'"s\x65arch"',
        description=r'"caf\u00e9\nrecords"',
        schema="""map[string]any{
        "type": "object", "properties": map[string]any{},
        "examples": []any{nil, true, 12, -1.5},
    }""",
    )
    (tool,) = parse_golang_mcp_code(code)
    assert tool["name"] == "search"
    assert tool["description"] == "café\nrecords"
    assert tool["inputSchema"]["examples"] == [None, True, 12, -1.5]


def test_official_and_builder_registration_are_deduplicated():
    code = source() + 'mcp.NewTool("search", mcp.WithDescription("builder"))'
    assert len(parse_golang_mcp_code(code)) == 1


def test_large_literal_is_not_cut_off_at_builder_window():
    code = source(description='"' + "long description " * 200 + '"')
    assert parse_golang_mcp_code(code)[0]["description"] == "long description " * 200


def test_annotations_and_output_helpers_do_not_change_input_contract():
    code = source().replace(
        'Name: "search",',
        "Annotations: &mcp.ToolAnnotations{ReadOnlyHint: true}, "
        'OutputSchema: resultSchema(), Name: "search",',
    )
    assert parse_golang_mcp_code(code) == parse_golang_mcp_code(source())


def test_unresolved_declaration_does_not_hide_a_later_complete_tool():
    code = source(schema="factsSchema()") + source(name='"complete"')
    assert [t["name"] for t in parse_golang_mcp_code(code)] == ["complete"]
