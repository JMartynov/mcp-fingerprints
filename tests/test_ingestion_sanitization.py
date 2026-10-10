"""Unit tests for ingestion hardening and malformed tool sanitization."""

import pytest
from mcp_fingerprints.validator import sanitize_tool_definition
from mcp_fingerprints.models import ToolContractSignature
from mcp_fingerprints.ast_parser import parse_python_mcp_ast, parse_typescript_mcp_ast


def test_sanitize_tool_definition_valid():
    raw_tool = {
        "name": "calculate_tax",
        "description": "Calculates tax based on rate",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "rate": {"type": "number"},
            },
            "required": ["amount", "rate"],
        },
    }
    sanitized = sanitize_tool_definition(raw_tool)
    assert sanitized is not None
    assert sanitized["name"] == "calculate_tax"
    assert sanitized["description"] == "Calculates tax based on rate"
    assert sanitized["inputSchema"]["type"] == "object"
    assert "amount" in sanitized["inputSchema"]["properties"]
    assert sanitized["inputSchema"]["required"] == ["amount", "rate"]


def test_sanitize_tool_definition_invalid_name():
    # Non-dict input
    assert sanitize_tool_definition("not-a-dict") is None
    assert sanitize_tool_definition(12345) is None
    assert sanitize_tool_definition(None) is None

    # Missing or non-string name
    assert sanitize_tool_definition({}) is None
    assert sanitize_tool_definition({"name": None}) is None
    assert sanitize_tool_definition({"name": 1234}) is None
    assert sanitize_tool_definition({"name": ""}) is None
    assert sanitize_tool_definition({"name": "   "}) is None

    # Control characters only
    assert sanitize_tool_definition({"name": "\x00\x01\x1f"}) is None


def test_sanitize_tool_definition_name_sanitization():
    # Whitespace and control chars should be stripped
    raw = {"name": " \x00fetch_data\x1f\n "}
    sanitized = sanitize_tool_definition(raw)
    assert sanitized is not None
    assert sanitized["name"] == "fetch_data"


def test_sanitize_tool_definition_schema_normalization():
    # Missing inputSchema
    raw1 = {"name": "tool1"}
    s1 = sanitize_tool_definition(raw1)
    assert s1 is not None
    assert s1["inputSchema"] == {"type": "object", "properties": {}}

    # Non-dict inputSchema
    raw2 = {"name": "tool2", "inputSchema": "invalid"}
    s2 = sanitize_tool_definition(raw2)
    assert s2 is not None
    assert s2["inputSchema"] == {"type": "object", "properties": {}}

    # Non-dict properties
    raw3 = {"name": "tool3", "inputSchema": {"properties": None}}
    s3 = sanitize_tool_definition(raw3)
    assert s3 is not None
    assert s3["inputSchema"]["properties"] == {}

    # Malformed property item
    raw4 = {
        "name": "tool4",
        "inputSchema": {
            "properties": {
                "valid": {"type": "string"},
                "malformed": "not-a-schema-dict",
            }
        },
    }
    s4 = sanitize_tool_definition(raw4)
    assert s4 is not None
    assert s4["inputSchema"]["properties"]["valid"] == {"type": "string"}
    assert s4["inputSchema"]["properties"]["malformed"] == {}

    # Non-list required
    raw5 = {"name": "tool5", "inputSchema": {"required": "not-a-list"}}
    s5 = sanitize_tool_definition(raw5)
    assert s5 is not None
    assert s5["inputSchema"]["required"] == []


def test_tool_contract_signature_from_dict_defensive():
    # Complete garbage input
    sig = ToolContractSignature.from_dict({})
    assert sig.name == ""
    assert sig.canonical_hash == ""
    assert sig.property_keys == ()
    assert sig.required_keys == ()
    assert sig.parameter_types == {}
    assert sig.input_schema == {}
    assert sig.output_schema is None

    # Corrupted field types
    corrupted = {
        "name": "broken_tool",
        "canonical_hash": "hash123",
        "property_keys": "not-a-list",
        "required_keys": None,
        "parameter_types": [1, 2, 3],
        "inputSchema": None,
        "outputSchema": "invalid",
    }
    sig2 = ToolContractSignature.from_dict(corrupted)
    assert sig2.name == "broken_tool"
    assert sig2.property_keys == ()
    assert sig2.required_keys == ()
    assert sig2.parameter_types == {}
    assert sig2.input_schema == {}
    assert sig2.output_schema is None


def test_ast_parsers_malformed_inputs():
    # Broken python syntax
    tools = parse_python_mcp_ast("def broken syntax (: unclosed {")
    assert tools == []

    # Non-code empty input
    assert parse_python_mcp_ast("") == []

    # TypeScript parser with random text
    assert parse_typescript_mcp_ast("malformed typescript code !@#$%^&*()") == []
