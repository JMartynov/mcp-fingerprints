"""Unit tests for MCP Passport invariants, validation, merging, deduplication, and sync."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
    extract_tool_signature,
)
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.synchronizer import PassportSynchronizer
from mcp_fingerprints.validator import McpServerValidator

# ==============================================================================
# INVARIANT 1: Strict MCP Validation & False-Positive Disambiguation
# ==============================================================================


def test_invariant_validation_official_scope_always_approved() -> None:
    """Invariant: Packages in official @modelcontextprotocol scope are always valid MCP servers."""
    is_valid, reason = McpServerValidator.is_valid_mcp_server(
        package_name="@modelcontextprotocol/server-custom",
        ecosystem="npm",
    )
    assert is_valid is True
    assert "official scope" in reason


def test_invariant_validation_core_sdk_dependency_approved() -> None:
    """Invariant: Packages importing @modelcontextprotocol/sdk or fastmcp are approved."""
    # npm ecosystem with sdk dependency
    is_valid, reason = McpServerValidator.is_valid_mcp_server(
        package_name="community-weather-tool",
        ecosystem="npm",
        dependencies={"@modelcontextprotocol/sdk": "^1.0.0", "axios": "^1.0.0"},
    )
    assert is_valid is True
    assert "core MCP SDK dependency" in reason

    # PyPI ecosystem with PEP 508 dependency strings
    is_valid_py, reason_py = McpServerValidator.is_valid_mcp_server(
        package_name="my-custom-mcp",
        ecosystem="PyPI",
        dependencies=["fastmcp>=0.1.0", "pydantic>=2.0"],
    )
    assert is_valid_py is True
    assert "core MCP SDK dependency" in reason_py


def test_invariant_validation_false_positive_minecraft_rejected() -> None:
    """Invariant: Packages referencing Minecraft or modpack protocols are strictly rejected."""
    is_valid, reason = McpServerValidator.is_valid_mcp_server(
        package_name="mcp-server-minecraft-forge",
        ecosystem="npm",
        keywords=["minecraft", "mcp", "forge-mod"],
        description="Minecraft Coder Pack server tools",
    )
    assert is_valid is False
    assert "rejected: matched false-positive keyword" in reason


def test_invariant_validation_false_positive_microsoft_cert_rejected() -> None:
    """Invariant: Packages referencing Microsoft Certified Professional are strictly rejected."""
    is_valid, reason = McpServerValidator.is_valid_mcp_server(
        package_name="mcp-exam-prep-helper",
        ecosystem="npm",
        description="Study questions for Microsoft Certified Professional (MCP) exam",
    )
    assert is_valid is False
    assert "rejected: matched false-positive keyword 'microsoft certified'" in reason


def test_invariant_validation_generic_unrelated_package_rejected() -> None:
    """Invariant: Unrelated utility packages with 'mcp' substring are rejected if lacking SDK."""
    is_valid, reason = McpServerValidator.is_valid_mcp_server(
        package_name="mcp-random-utils",
        ecosystem="npm",
        dependencies={"lodash": "^4.17.21"},
        description="General helper functions",
    )
    assert is_valid is False
    assert "missing core MCP SDK dependency" in reason


# ==============================================================================
# INVARIANT 2: Deterministic Order-Independent Canonicalization & Hash Integrity
# ==============================================================================


def test_invariant_canonical_hash_property_order_independent() -> None:
    """Invariant: Reordering JSON Schema properties produces identical canonical hash."""
    tool_a = {
        "name": "search_database",
        "description": "Execute search query with filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword"},
                "limit": {"type": "integer", "description": "Max results"},
                "offset": {"type": "integer", "description": "Page offset"},
            },
            "required": ["query", "limit"],
        },
    }
    tool_b = {
        "name": "search_database",
        "description": "Execute search query with filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "offset": {"type": "integer", "description": "Page offset"},
                "limit": {"type": "integer", "description": "Max results"},
                "query": {"type": "string", "description": "Search keyword"},
            },
            "required": ["limit", "query"],
        },
    }

    sig_a = extract_tool_signature(tool_a)
    sig_b = extract_tool_signature(tool_b)

    assert sig_a.canonical_hash == sig_b.canonical_hash
    assert sig_a.property_keys == ("limit", "offset", "query")
    assert sig_a.required_keys == ("limit", "query")


def test_invariant_toolset_canonical_hash_tool_order_independent() -> None:
    """Invariant: Permuting ordering of tools yields an identical toolset hash."""
    tool_1 = {
        "name": "tool_alpha",
        "inputSchema": {"type": "object", "properties": {"a": {"type": "string"}}},
    }
    tool_2 = {
        "name": "tool_beta",
        "inputSchema": {"type": "object", "properties": {"b": {"type": "string"}}},
    }

    fp_1 = build_version_fingerprint("1.0.0", tools=[tool_1, tool_2])
    fp_2 = build_version_fingerprint("1.0.0", tools=[tool_2, tool_1])

    assert fp_1.toolset_canonical_hash == fp_2.toolset_canonical_hash


# ==============================================================================
# INVARIANT 3: Offline Cross-Source Merging & Deduplication
# ==============================================================================


def test_invariant_offline_cross_source_merger_combines_smithery_and_npm(tmp_path: Path) -> None:
    """Invariant: Offline merge preserves Smithery tools and npm version history in one passport."""
    syncer = PassportSynchronizer(output_dir=tmp_path)

    smithery_mock = {
        "qualifiedName": "postgres",
        "displayName": "PostgreSQL MCP Server",
        "description": "Smithery description of PostgreSQL server",
        "deploymentUrl": "https://postgres.run.tools",
        "connections": [{"type": "stdio", "command": "node dist/index.js"}],
        "tools": [
            {
                "name": "read_query",
                "description": "Execute read query",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        ],
    }

    npm_mock = {
        "name": "@modelcontextprotocol/server-postgres",
        "description": "Official PostgreSQL MCP server",
        "license": "MIT",
        "dist-tags": {"latest": "0.6.2"},
        "time": {
            "0.1.0": "2024-11-25T10:00:00Z",
            "0.6.2": "2025-05-20T14:22:10Z",
        },
        "versions": {
            "0.1.0": {"dependencies": {"@modelcontextprotocol/sdk": "^0.1.0"}},
            "0.6.2": {"dependencies": {"@modelcontextprotocol/sdk": "^1.0.0", "pg": "^8.13.1"}},
        },
    }

    spec = syncer.merge_and_enrich_passport(
        package_name="@modelcontextprotocol/server-postgres",
        ecosystem="npm",
        smithery_data=smithery_mock,
        npm_data=npm_mock,
    )

    assert spec is not None
    assert spec.package_name == "@modelcontextprotocol/server-postgres"
    assert spec.purl == "pkg:npm/@modelcontextprotocol%2Fserver-postgres"
    assert "smithery" in spec.sources_merged
    assert "npm_registry" in spec.sources_merged
    assert "postgres" in spec.aliases
    assert len(spec.versions) == 2

    # Latest version (0.6.2) has the merged tool contract
    latest_v = next(v for v in spec.versions if v.version == "0.6.2")
    assert len(latest_v.tool_signatures) == 1
    assert latest_v.tool_signatures[0].name == "read_query"
    assert latest_v.dependencies["pg"] == "^8.13.1"
    assert latest_v.connections[0]["type"] == "stdio"


def test_invariant_historical_version_preservation_on_update(tmp_path: Path) -> None:
    """Invariant: When an MCP updates upstream, old historical tool signatures are preserved."""
    syncer = PassportSynchronizer(output_dir=tmp_path)

    # Initial version 0.1.0 with a legacy tool 'query'
    legacy_tool = {
        "name": "query",
        "description": "Legacy execute sql",
        "inputSchema": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
            "required": ["sql"],
        },
    }
    v1_fp = build_version_fingerprint("0.1.0", tools=[legacy_tool])

    existing_spec = ServerPackageSpec(
        package_name="@modelcontextprotocol/server-postgres",
        purl="pkg:npm/%40modelcontextprotocol/server-postgres",
        ecosystem="npm",
        versions=(v1_fp,),
    )

    # Upstream npm now announces 0.6.0 with new tool 'read_query'
    new_tool = {
        "name": "read_query",
        "description": "Execute read sql",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    }
    smithery_new = {"tools": [new_tool]}

    npm_new = {
        "name": "@modelcontextprotocol/server-postgres",
        "dist-tags": {"latest": "0.6.0"},
        "time": {"0.1.0": "2024-11-25T10:00:00Z", "0.6.0": "2025-05-20T14:22:10Z"},
        "versions": {
            "0.1.0": {"dependencies": {"@modelcontextprotocol/sdk": "^0.1.0"}},
            "0.6.0": {"dependencies": {"@modelcontextprotocol/sdk": "^1.0.0"}},
        },
    }

    updated_spec = syncer.merge_and_enrich_passport(
        package_name="@modelcontextprotocol/server-postgres",
        ecosystem="npm",
        smithery_data=smithery_new,
        npm_data=npm_new,
        existing_spec=existing_spec,
    )

    assert updated_spec is not None
    assert len(updated_spec.versions) == 2

    # Check 0.1.0 preserved 'query' tool
    v_010 = next(v for v in updated_spec.versions if v.version == "0.1.0")
    assert len(v_010.tool_signatures) == 1
    assert v_010.tool_signatures[0].name == "query"

    # Check 0.6.0 has 'read_query' tool
    v_060 = next(v for v in updated_spec.versions if v.version == "0.6.0")
    assert len(v_060.tool_signatures) == 1
    assert v_060.tool_signatures[0].name == "read_query"


# ==============================================================================
# INVARIANT 4: Online Registry Connectivity & Web Signature Update Detection
# ==============================================================================


def test_invariant_online_live_registry_connectors() -> None:
    """Invariant: Online connectors successfully retrieve schema definitions without auth errors."""
    import ssl
    import urllib.request

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # 1. Smithery online live check
    req_smithery = urllib.request.Request(
        "https://api.smithery.ai/servers/brave",
        headers={"User-Agent": "VerityRedTeam-Test/1.0"},
    )
    with urllib.request.urlopen(req_smithery, context=ctx, timeout=10.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "tools" in data
        assert len(data["tools"]) >= 1
        assert any(t["name"] == "brave_web_search" for t in data["tools"])

    # 2. npm online live check
    req_npm = urllib.request.Request(
        "https://registry.npmjs.org/@modelcontextprotocol/server-filesystem",
        headers={"User-Agent": "VerityRedTeam-Test/1.0"},
    )
    with urllib.request.urlopen(req_npm, context=ctx, timeout=10.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "dist-tags" in data
        assert "latest" in data["dist-tags"]
        assert len(data["versions"]) >= 1

    # 3. PyPI online live check
    req_pypi = urllib.request.Request(
        "https://pypi.org/pypi/fastmcp/json",
        headers={"User-Agent": "VerityRedTeam-Test/1.0"},
    )
    with urllib.request.urlopen(req_pypi, context=ctx, timeout=10.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "info" in data
        assert data["info"]["name"] == "fastmcp"
        assert len(data.get("releases", {})) >= 1


def test_invariant_detects_web_signature_updates_and_schema_drift() -> None:
    """Invariant: Catch upstream tool signature modifications or added parameters."""
    # 1. Baseline known tool contract
    baseline_tool = {
        "name": "search_database",
        "description": "Perform SQL database search",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query expression"},
                "limit": {"type": "integer", "default": 50},
            },
            "required": ["query"],
        },
    }
    baseline_sig = extract_tool_signature(baseline_tool)

    # 2. Upstream web update (added new parameter 'timeout' and modified property typing)
    updated_web_tool = {
        "name": "search_database",
        "description": "Perform SQL database search with timeout guard",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query expression"},
                "limit": {"type": "integer", "default": 50},
                "timeout": {"type": "number", "description": "Execution timeout in seconds"},
            },
            "required": ["query"],
        },
    }
    updated_sig = extract_tool_signature(updated_web_tool)

    # Cryptographic hashes MUST differ upon upstream web schema updates
    assert baseline_sig.canonical_hash != updated_sig.canonical_hash
    assert "timeout" not in baseline_sig.property_keys
    assert "timeout" in updated_sig.property_keys

    # 3. Test Matcher detects version drift / Layer 2 fallback when signature shifts
    from mcp_fingerprints.matcher import FingerprintMatcher

    matcher = FingerprintMatcher()
    baseline_version = build_version_fingerprint("1.0.0", tools=[baseline_tool])
    spec = ServerPackageSpec(
        package_name="db-search-mcp",
        purl="pkg:npm/db-search-mcp",
        ecosystem="npm",
        versions=(baseline_version,),
    )
    matcher.register_package(spec)

    # Matcher handles schema drift with Layer 2 topological fallback
    match_res = matcher.match([updated_web_tool], server_name_hint="db-search-mcp")
    assert match_res.matched is True
    assert match_res.package_name == "db-search-mcp"
    assert match_res.layer1_exact_match is False
    assert match_res.match_layer in ("LAYER_2_TOPOLOGY", "LAYER_3_CAPABILITY")
    assert match_res.confidence_score < 1.0


def test_invariant_detects_tool_addition_and_removal_in_updated_releases() -> None:
    """Invariant: Detects when upstream releases add or remove tools over time."""
    from mcp_fingerprints.matcher import FingerprintMatcher

    v1_tools = [
        {
            "name": "fetch_user",
            "inputSchema": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"],
            },
        },
    ]
    v2_tools = [
        {
            "name": "fetch_user",
            "inputSchema": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"],
            },
        },
        {
            "name": "delete_user",
            "inputSchema": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}, "force": {"type": "boolean"}},
                "required": ["user_id"],
            },
        },
    ]

    v1_fp = build_version_fingerprint("1.0.0", tools=v1_tools)
    v2_fp = build_version_fingerprint("2.0.0", tools=v2_tools)

    spec = ServerPackageSpec(
        package_name="user-manager-mcp",
        purl="pkg:npm/user-manager-mcp",
        ecosystem="npm",
        versions=(v1_fp, v2_fp),
    )

    matcher = FingerprintMatcher()
    matcher.register_package(spec)

    # Querying with v1 tools matches v1.0.0 exactly
    res_v1 = matcher.match(v1_tools, server_name_hint="user-manager-mcp")
    assert res_v1.matched is True
    assert res_v1.matched_version == "1.0.0"
    assert res_v1.layer1_exact_match is True

    # Querying with v2 tools matches v2.0.0 exactly
    res_v2 = matcher.match(v2_tools, server_name_hint="user-manager-mcp")
    assert res_v2.matched is True
    assert res_v2.matched_version == "2.0.0"
    assert res_v2.layer1_exact_match is True
    res_v2 = matcher.match(v2_tools, server_name_hint="user-manager-mcp")
    assert res_v2.matched is True
    assert res_v2.matched_version == "2.0.0"
    assert res_v2.layer1_exact_match is True
