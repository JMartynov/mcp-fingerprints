"""Comprehensive unit tests for pure structural models and canonicalization in mcp-fingerprints.

Verifies VC-33.1, VC-33.2, VC-33.3, and VC-33.4.
"""

from __future__ import annotations

from typing import get_args

from mcp_fingerprints.canonicalizer import (
    extract_tool_signature,
)
from mcp_fingerprints.models import (
    ParameterMetadata,
    ServerPackageSpec,
    ToolContractSignature,
    TransportType,
    VersionFingerprint,
)


def test_parameter_metadata_roundtrip() -> None:
    """VC-33.1: ParameterMetadata exists and round-trips all required schema attributes."""
    param = ParameterMetadata(
        name="timeout_ms",
        type="integer",
        description="Timeout in milliseconds for the operation",
        required=True,
        default=5000,
        enum=(1000, 2000, 5000, 10000),
        format="int32",
        items_type=None,
        nested_properties={"retries": {"type": "integer", "default": 3}},
    )

    d = param.to_dict()
    assert d["name"] == "timeout_ms"
    assert d["type"] == "integer"
    assert d["description"] == "Timeout in milliseconds for the operation"
    assert d["required"] is True
    assert d["default"] == 5000
    assert d["enum"] == [1000, 2000, 5000, 10000]
    assert d["format"] == "int32"
    assert d["items_type"] is None
    assert d["nested_properties"] == {"retries": {"type": "integer", "default": 3}}

    # Roundtrip from dict
    restored = ParameterMetadata.from_dict(d)
    assert restored.name == param.name
    assert restored.type == param.type
    assert restored.description == param.description
    assert restored.required == param.required
    assert restored.default == param.default
    assert restored.enum == param.enum
    assert restored.format == param.format
    assert restored.items_type == param.items_type
    assert restored.nested_properties == param.nested_properties


def test_array_parameter_metadata_roundtrip() -> None:
    """VC-33.1: ParameterMetadata roundtrip with array items_type."""
    param = ParameterMetadata(
        name="tags",
        type="array",
        description="List of tag strings",
        required=False,
        default=["default"],
        enum=None,
        format=None,
        items_type="string",
        nested_properties=None,
    )
    d = param.to_dict()
    assert d["items_type"] == "string"
    restored = ParameterMetadata.from_dict(d)
    assert restored.items_type == "string"
    assert restored.default == ["default"]


def test_server_package_spec_author_and_no_security_profile() -> None:
    """VC-33.2: ServerPackageSpec.to_dict() emits author and does NOT emit security_profile."""
    spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server",
        ecosystem="npm",
        author="Acme Corp <maintainer@example.com>",
        description="A pure structural test server",
        repository_url="https://github.com/acme/test-server",
        homepage_url="https://acme.example.com",
        license="MIT",
    )

    assert not hasattr(spec, "security_profile")
    out = spec.to_dict()
    assert out["author"] == "Acme Corp <maintainer@example.com>"
    assert "security_profile" not in out

    # Ensure from_dict safely ignores legacy security_profile without failing
    legacy_data = out.copy()
    legacy_data["security_profile"] = {"risk_tier": "Critical", "score": 9.9}
    restored = ServerPackageSpec.from_dict(legacy_data)
    assert not hasattr(restored, "security_profile")
    assert restored.author == "Acme Corp <maintainer@example.com>"
    assert "security_profile" not in restored.to_dict()


def test_version_fingerprint_required_env_vars_and_transport() -> None:
    """VC-33.3: VersionFingerprint supports required_env_vars and TransportType includes streamable-http."""
    # Check TransportType literal variants
    valid_transports = get_args(TransportType)
    assert "streamable-http" in valid_transports
    assert "stdio" in valid_transports
    assert "sse" in valid_transports
    assert "websocket" in valid_transports

    fp = VersionFingerprint(
        version="2.1.0",
        toolset_canonical_hash="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        transport="streamable-http",
        required_env_vars=("DATABASE_URL", "API_KEY"),
    )

    d = fp.to_dict()
    assert d["transport"] == "streamable-http"
    assert d["required_env_vars"] == ["DATABASE_URL", "API_KEY"]

    restored = VersionFingerprint.from_dict(d)
    assert restored.transport == "streamable-http"
    assert restored.required_env_vars == ("DATABASE_URL", "API_KEY")


def test_tool_contract_signature_parameters_and_annotations() -> None:
    """VC-33.4: ToolContractSignature roundtrip and automatic parameter derivation."""
    raw_tool = {
        "name": "query_items",
        "description": "Execute read query",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "SQL filter clause",
                    "default": "*",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max items to return",
                    "default": 100,
                    "enum": [10, 50, 100, 500],
                },
            },
            "required": ["filter"],
        },
    }

    sig = extract_tool_signature(raw_tool)
    assert sig.name == "query_items"
    assert sig.annotations["readOnlyHint"] is True
    assert sig.annotations["idempotentHint"] is True
    assert len(sig.parameters) == 2

    filter_param = next(p for p in sig.parameters if p.name == "filter")
    assert filter_param.required is True
    assert filter_param.type == "string"
    assert filter_param.default == "*"

    limit_param = next(p for p in sig.parameters if p.name == "limit")
    assert limit_param.required is False
    assert limit_param.enum == (10, 50, 100, 500)

    # Roundtrip ToolContractSignature
    sig_dict = sig.to_dict()
    assert sig_dict["annotations"]["readOnlyHint"] is True
    assert len(sig_dict["parameters"]) == 2

    restored_sig = ToolContractSignature.from_dict(sig_dict)
    assert restored_sig.canonical_hash == sig.canonical_hash
    assert restored_sig.parameters == sig.parameters
    assert restored_sig.annotations == sig.annotations


def test_canonical_hash_preserves_determinism() -> None:
    """Ensure canonical_hash remains identical whether rich parameters/annotations are added or not."""
    tool_raw = {
        "name": "sample_tool",
        "description": "A sample description",
        "inputSchema": {
            "type": "object",
            "properties": {"val": {"type": "string"}},
            "required": ["val"],
        },
    }

    sig1 = extract_tool_signature(tool_raw)

    tool_enriched = tool_raw.copy()
    tool_enriched["annotations"] = {"readOnlyHint": True}
    tool_enriched["parameters"] = [
        {"name": "val", "type": "string", "description": "some val", "required": True}
    ]

    sig2 = extract_tool_signature(tool_enriched)
    assert sig1.canonical_hash == sig2.canonical_hash
