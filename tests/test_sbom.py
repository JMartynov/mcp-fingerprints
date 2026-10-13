import pytest
import re
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature
from mcp_fingerprints.sbom import generate_cyclonedx_sbom

def test_generate_cyclonedx_sbom_spec_generation():
    tool = ToolContractSignature(
        name="test_tool",
        canonical_hash="hash_123",
        description="A test tool",
        is_mutating=False,
    )
    version = VersionFingerprint(
        version="1.0.0",
        toolset_canonical_hash="toolset_hash_123",
        tool_signatures=(tool,)
    )
    spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server@1.0.0",
        ecosystem="npm",
        description="A test MCP server",
        versions=(version,)
    )

    sbom = generate_cyclonedx_sbom(spec)

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["version"] == 1
    
    # Check that serialNumber is a valid UUID urn
    assert sbom["serialNumber"].startswith("urn:uuid:")
    uuid_part = sbom["serialNumber"].replace("urn:uuid:", "")
    assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid_part, re.IGNORECASE)
    
    component = sbom["metadata"]["component"]
    assert component["type"] == "application"
    assert component["name"] == "test-server"
    assert component["version"] == "1.0.0"
    assert component["purl"] == "pkg:npm/test-server@1.0.0"
    assert component["description"] == "A test MCP server"

    # Tool mapped to property
    properties = component.get("properties", [])
    assert len(properties) == 1
    assert properties[0]["name"] == "mcp.tool.test_tool"
    assert properties[0]["value"] == "A test tool"

def test_generate_cyclonedx_sbom_no_versions():
    spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server",
        ecosystem="npm",
        description="A test MCP server with no versions"
    )

    sbom = generate_cyclonedx_sbom(spec)

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"

    component = sbom["metadata"]["component"]
    assert component["name"] == "test-server"
    assert component["version"] == "unknown"
    assert component["purl"] == "pkg:npm/test-server"

def test_generate_cyclonedx_sbom_target_version():
    tool1 = ToolContractSignature(name="tool1", canonical_hash="1")
    version1 = VersionFingerprint(version="1.0.0", toolset_canonical_hash="t1", tool_signatures=(tool1,))
    
    tool2 = ToolContractSignature(name="tool2", canonical_hash="2")
    version2 = VersionFingerprint(version="2.0.0", toolset_canonical_hash="t2", tool_signatures=(tool2,))

    spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server",
        ecosystem="npm",
        versions=(version1, version2)
    )

    sbom1 = generate_cyclonedx_sbom(spec, target_version="1.0.0")
    assert sbom1["metadata"]["component"]["version"] == "1.0.0"
    assert sbom1["metadata"]["component"]["properties"][0]["name"] == "mcp.tool.tool1"

    sbom2 = generate_cyclonedx_sbom(spec, target_version="2.0.0")
    assert sbom2["metadata"]["component"]["version"] == "2.0.0"
    assert sbom2["metadata"]["component"]["properties"][0]["name"] == "mcp.tool.tool2"
