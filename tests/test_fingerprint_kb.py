"""Unit tests for the MCP Tri-Layer Structural Fingerprint Knowledge Base & Matcher."""

from __future__ import annotations

from pathlib import Path

from mcp_fingerprints.canonicalizer import (
    compute_toolset_canonical_hash,
    extract_tool_signature,
)
from mcp_fingerprints.distance import (
    jaccard_similarity,
)
from mcp_fingerprints.matcher import FingerprintMatcher


def test_tool_signature_canonical_hash_invariance() -> None:
    """Test that canonical hash is invariant to dictionary key ordering and whitespace."""
    tool_a = {
        "name": "read_query",
        "description": "Execute a SELECT query on PostgreSQL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The SQL query"},
                "limit": {"type": "integer", "description": "Row limit"},
            },
            "required": ["query"],
        },
    }

    tool_b = {
        "inputSchema": {
            "required": ["query"],
            "properties": {
                "limit": {"description": "Row limit", "type": "integer"},
                "query": {"description": "The SQL query", "type": "string"},
            },
            "type": "object",
        },
        "description": "Execute a SELECT query on PostgreSQL",
        "name": "read_query",
    }

    sig_a = extract_tool_signature(tool_a)
    sig_b = extract_tool_signature(tool_b)

    assert sig_a.canonical_hash == sig_b.canonical_hash
    assert sig_a.property_keys == ("limit", "query")
    assert sig_a.required_keys == ("query",)
    assert sig_a.parameter_types == {"query": "string", "limit": "integer"}


def test_toolset_canonical_hash_order_invariance() -> None:
    """Test that toolset canonical hash is order-independent across tool definitions."""
    tools_list_1 = [
        {
            "name": "query_b",
            "inputSchema": {"type": "object", "properties": {"b": {"type": "string"}}},
        },
        {
            "name": "query_a",
            "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}}},
        },
    ]
    tools_list_2 = [
        {
            "name": "query_a",
            "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}}},
        },
        {
            "name": "query_b",
            "inputSchema": {"type": "object", "properties": {"b": {"type": "string"}}},
        },
    ]

    hash_1 = compute_toolset_canonical_hash(tools_list_1)
    hash_2 = compute_toolset_canonical_hash(tools_list_2)

    assert hash_1 == hash_2
    assert hash_1.startswith("sha256:")


def test_jaccard_similarity_and_distance() -> None:
    """Test Jaccard metric bounds and calculations."""
    assert jaccard_similarity(set(), set()) == 1.0
    assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0
    assert jaccard_similarity({"a"}, {"b"}) == 0.0
    assert jaccard_similarity({"a", "b"}, {"b", "c"}) == 1.0 / 3.0


def test_matcher_layer1_exact_match(tmp_path: Path) -> None:
    """Test that identical tools yield Layer 1 exact match with confidence 1.0."""
    tools = [
        {
            "name": "authorization_endpoint",
            "description": "Authenticate against remote MCP proxy",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "endpoint_url": {
                        "type": "string",
                        "description": "OAuth authorization endpoint URL",
                    },
                    "client_id": {"type": "string", "description": "Client identifier"},
                },
                "required": ["endpoint_url"],
            },
        },
        {
            "name": "connect",
            "description": "Establish remote SSE tunnel connection to upstream MCP host",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
                "required": ["host"],
            },
        },
    ]

    matcher = FingerprintMatcher()
    matcher.load_from_directory("data/fingerprints")

    result = matcher.match(tools=tools, server_name_hint="mcp-remote")
    assert result.matched is True
    assert result.package_name == "mcp-remote"
    assert result.matched_version == "0.0.8"
    assert result.confidence_score == 1.0
    assert result.match_layer == "LAYER_1_EXACT"
    assert result.layer1_exact_match is True


def test_matcher_layer2_topology_fuzzy_match() -> None:
    """Test that modified descriptions or extra parameters match via Layer 2 topology."""
    # Modified description and slightly altered parameter description for postgres server-postgres
    observed_tools = [
        {
            "name": "read_query",
            "description": "Custom developer modified description for read queries",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Modified desc"}},
                "required": ["query"],
            },
        },
        {
            "name": "write_query",
            "description": "Execute write queries on PostgreSQL",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    ]

    matcher = FingerprintMatcher()
    matcher.load_from_directory("data/fingerprints")

    result = matcher.match(tools=observed_tools, server_name_hint="postgres")
    assert result.matched is True
    assert result.package_name == "@modelcontextprotocol/server-postgres"
    assert result.matched_version == "0.6.0"
    assert result.confidence_score >= 0.85
    assert result.match_layer == "LAYER_2_TOPOLOGY"


def test_matcher_unknown_server_returns_unmatched() -> None:
    """Test that completely foreign tool definitions return matched=False."""
    foreign_tools = [
        {
            "name": "quantum_teleport_qubit",
            "inputSchema": {"type": "object", "properties": {"qubit_id": {"type": "string"}}},
        }
    ]

    matcher = FingerprintMatcher()
    matcher.load_from_directory("data/fingerprints")

    result = matcher.match(tools=foreign_tools)
    assert result.matched is False
    assert result.confidence_score < 0.65
    assert result.match_layer == "NONE"
