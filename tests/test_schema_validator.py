import pytest
from mcp_fingerprints.schema_validator import PassportSchemaValidator
from mcp_fingerprints.canonicalizer import build_version_fingerprint
from mcp_fingerprints.models import ServerPackageSpec

def test_schema_validator_catches_invalid_tools() -> None:
    # A valid tool
    tools_valid = [{"name": "valid_tool"}]
    fp_valid = build_version_fingerprint("1.0.0", tools=tools_valid)
    spec_valid = ServerPackageSpec(
        package_name="test-package",
        purl="pkg:npm/test-package",
        ecosystem="npm",
        versions=(fp_valid,)
    )
    is_valid, errors = PassportSchemaValidator.validate_passport_dict(spec_valid.to_dict())
    assert is_valid
    assert not errors

    # Now let's artificially construct an invalid Passport missing a tool name
    # We bypass canonicalizer to create an invalid spec manually
    spec_invalid_dict = spec_valid.to_dict()
    spec_invalid_dict["versions"][0]["tool_signatures"].append({
        "name": "",
        "canonical_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        "property_keys": [],
        "required_keys": []
    })

    is_valid, errors = PassportSchemaValidator.validate_passport_dict(spec_invalid_dict)
    assert not is_valid
    assert any("missing 'name'" in err for err in errors)

def test_schema_validator_with_pruned_nameless_tools() -> None:
    # This just ensures that if we use canonicalizer, the resulting spec is valid
    # because canonicalizer prunes them.
    tools = [
        {"name": "valid_tool"},
        {"name": ""},
        {}
    ]
    fp = build_version_fingerprint("1.0.0", tools=tools)
    spec = ServerPackageSpec(
        package_name="test-package",
        purl="pkg:npm/test-package",
        ecosystem="npm",
        versions=(fp,)
    )
    is_valid, errors = PassportSchemaValidator.validate_passport_dict(spec.to_dict())
    assert is_valid
