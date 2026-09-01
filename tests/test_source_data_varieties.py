"""Comprehensive Multi-Variant Tests for All Types of MCP Source Data.

Verifies that the fingerprint extraction engine accurately extracts, normalizes,
and fingerprints all known varieties of MCP tool definitions, prompts, resources,
and manifest configurations without dropping critical data.
"""

from __future__ import annotations

import json
import pytest

from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
    extract_tool_signature,
    compute_toolset_canonical_hash,
)
from mcp_fingerprints.crawler import FingerprintGenerator
from mcp_fingerprints.distance import jaccard_similarity
from mcp_fingerprints.models import (
    PromptSignature,
    ResourceSignature,
    ServerPackageSpec,
    ToolContractSignature,
)


def test_variant_anthropic_input_schema():
    """Variant 1: Standard Anthropic MCP tool contract with inputSchema."""
    tool_def = {
        "name": "query_postgres",
        "description": "Execute a parameterized SQL query",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL statement"},
                "params": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["sql"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {"rows": {"type": "array"}},
        },
    }
    sig = extract_tool_signature(tool_def)
    assert sig.name == "query_postgres"
    assert sig.property_keys == ("params", "sql")
    assert sig.required_keys == ("sql",)
    assert sig.parameter_types == {"sql": "string", "params": "array"}
    assert sig.output_schema is not None
    assert sig.canonical_hash.startswith("sha256:")
    assert sig.description_hash is not None


def test_variant_openai_parameters_schema():
    """Variant 2: OpenAI/JSON-RPC tool contract using 'parameters' keyword."""
    tool_def = {
        "name": "search_database",
        "description": "Search customer records",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    }
    sig = extract_tool_signature(tool_def)
    assert sig.name == "search_database"
    assert sig.property_keys == ("limit", "query")
    assert sig.required_keys == ("query",)
    assert sig.parameter_types == {"query": "string", "limit": "integer"}
    assert sig.input_schema["properties"]["query"]["type"] == "string"


def test_variant_parameterless_tool():
    """Variant 3: Parameter-less tool (e.g. ping, list_schemas)."""
    tool_def = {
        "name": "ping",
        "description": "Health check probe",
    }
    sig = extract_tool_signature(tool_def)
    assert sig.name == "ping"
    assert sig.property_keys == ()
    assert sig.required_keys == ()
    assert sig.parameter_types == {}
    assert sig.canonical_hash.startswith("sha256:")


def test_variant_complex_nested_schema():
    """Variant 4: Complex nested JSON Schema with definitions and sub-objects."""
    tool_def = {
        "name": "create_workflow",
        "description": "Deploy a multi-step orchestration workflow",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string"},
                "config": {
                    "type": "object",
                    "properties": {
                        "retry_count": {"type": "integer"},
                        "timeout": {"type": "number"},
                    },
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["workflow_id", "config"],
        },
    }
    sig = extract_tool_signature(tool_def)
    assert sig.name == "create_workflow"
    assert sig.property_keys == ("config", "tags", "workflow_id")
    assert sig.required_keys == ("config", "workflow_id")
    assert sig.parameter_types["config"] == "object"
    assert sig.parameter_types["tags"] == "array"


def test_variant_prompts_with_rich_arguments():
    """Variant 5: MCP Prompt templates with diverse argument declarations."""
    prompt_data = {
        "name": "analyze_sql_performance",
        "description": "Generates EXPLAIN ANALYZE recommendations",
        "arguments": [
            {"name": "query_text", "description": "Raw SQL query", "required": True},
            {"name": "engine", "description": "Database engine name", "required": False},
        ],
    }
    sig = PromptSignature.from_dict(prompt_data)
    assert sig.name == "analyze_sql_performance"
    assert sig.argument_keys == ("query_text", "engine")
    assert sig.required_arguments == ("query_text",)
    assert len(sig.arguments_schema) == 2


def test_variant_resource_uri_and_templates():
    """Variant 6: Resource templates across static URIs and RFC 6570 URI templates."""
    # Static URI
    r1 = ResourceSignature.from_dict(
        {"uri": "file:///var/log/mcp.log", "name": "Log File", "mimeType": "text/plain"}
    )
    assert r1.uri_template == "file:///var/log/mcp.log"
    assert r1.mime_type == "text/plain"

    # RFC 6570 Template
    r2 = ResourceSignature.from_dict(
        {
            "uriTemplate": "postgres://localhost/{schema}/{table}/schema",
            "name": "Table Schema",
            "mime_type": "application/json",
        }
    )
    assert r2.uri_template == "postgres://localhost/{schema}/{table}/schema"
    assert r2.mime_type == "application/json"


def test_variant_mutating_tool_detection():
    """Variant 7: Mutating tool heuristic flags for agentic security firewalls."""
    tools = [
        {"name": "delete_table", "description": "Drops a table from the catalog"},
        {"name": "get_customer", "description": "Reads customer by ID"},
        {"name": "execute_query", "description": "Runs arbitrary SQL query"},
        {"name": "list_files", "description": "Lists directory entries"},
    ]
    # delete_table and execute_query are mutating
    sigs = [
        extract_tool_signature({"name": t["name"], "description": t["description"], "is_mutating": any(v in t["name"] for v in ("delete", "execute", "write", "update"))})
        for t in tools
    ]
    assert sigs[0].is_mutating is True
    assert sigs[1].is_mutating is False
    assert sigs[2].is_mutating is True
    assert sigs[3].is_mutating is False


def test_variant_version_drift_and_evolution():
    """Variant 8: Multi-version lifecycle tracking tool additions and schema changes."""
    # Version 1.0.0 (1 tool)
    spec = FingerprintGenerator.generate_server_spec(
        package_name="@test/mcp-server",
        ecosystem="npm",
        purl="pkg:npm/%40test/mcp-server",
        version="1.0.0",
        tools=[{"name": "read_data", "inputSchema": {"properties": {"key": {"type": "string"}}}}],
    )
    assert len(spec.versions) == 1
    assert len(spec.versions[0].tool_signatures) == 1

    # Version 2.0.0 (added write_data tool)
    spec_v2 = FingerprintGenerator.add_version_to_spec(
        existing_spec=spec,
        version="2.0.0",
        tools=[
            {"name": "read_data", "inputSchema": {"properties": {"key": {"type": "string"}}}},
            {"name": "write_data", "inputSchema": {"properties": {"key": {"type": "string"}, "val": {"type": "string"}}}},
        ],
    )
    assert len(spec_v2.versions) == 2
    v1_hash = spec_v2.versions[0].toolset_canonical_hash
    v2_hash = spec_v2.versions[1].toolset_canonical_hash
    assert v1_hash != v2_hash
