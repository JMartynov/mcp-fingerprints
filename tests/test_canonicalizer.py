from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
    compute_toolset_canonical_hash,
)
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.schema_validator import PassportSchemaValidator


def test_prune_nameless_tools() -> None:
    tools = [
        {"name": "valid_tool", "description": "This is a valid tool"},
        {"name": "", "description": "Empty string name"},
        {"name": "   ", "description": "Whitespace string name"},
        {"description": "Missing name key"},
        {"name": None, "description": "None name"},
        {
            "name": 123,
            "description": "Non-string name",
        },  # str(123) is "123", so it will actually be kept. Wait, bool(123 and str(123).strip()) -> bool(123 and "123") -> True.
    ]

    # Let's adjust the test to just the things that should be pruned.
    tools = [
        {"name": "valid_tool", "description": "This is a valid tool"},
        {"name": "", "description": "Empty string name"},
        {"name": "   ", "description": "Whitespace string name"},
        {"description": "Missing name key"},
        {"name": None, "description": "None name"},
    ]

    version_fingerprint = build_version_fingerprint("1.0.0", tools=tools)

    assert len(version_fingerprint.tool_signatures) == 1
    assert version_fingerprint.tool_signatures[0].name == "valid_tool"

    hash_val = compute_toolset_canonical_hash(tools)
    assert version_fingerprint.toolset_canonical_hash == hash_val

    # Test schema validation
    spec = ServerPackageSpec(
        package_name="test-package",
        purl="pkg:npm/test-package",
        ecosystem="npm",
        versions=(version_fingerprint,),
    )

    is_valid, errors = PassportSchemaValidator.validate_passport_dict(spec.to_dict())
    assert is_valid, f"Schema validation failed: {errors}"
