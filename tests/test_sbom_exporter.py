import json
import uuid
import pytest
from pathlib import Path

from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature
from mcp_fingerprints.sbom_exporter import CycloneDXExporter, SBOMFormat

@pytest.fixture
def sample_spec():
    tool = ToolContractSignature(
        name="test_tool",
        description="A test tool",
        input_schema={"type": "object", "properties": {"arg1": {"type": "string"}}}, canonical_hash="1234"
    )
    
    version = VersionFingerprint(
        version="1.0.0",
        toolset_canonical_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        tool_signatures=(tool,)
    )
    
    spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server",
        ecosystem="npm",
        description="A test server",
        repository_url="https://github.com/test/test-server",
        versions=(version,)
    )
    return spec

def test_cyclonedx_export_format(sample_spec):
    sbom = CycloneDXExporter.export(sample_spec, format=SBOMFormat.CYCLONEDX)
    
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"
    assert "serialNumber" in sbom
    assert sbom["serialNumber"].startswith("urn:uuid:")
    
    assert len(sbom["components"]) == 1
    comp = sbom["components"][0]
    
    assert comp["name"] == "test-server"
    assert comp["version"] == "1.0.0"
    assert comp["purl"] == "pkg:npm/test-server"
    
    assert len(comp["hashes"]) == 1
    assert comp["hashes"][0]["content"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    assert "components" in comp
    assert len(comp["components"]) == 1
    sub = comp["components"][0]
    
    assert sub["name"] == "mcp-tool:test_tool"
    assert sub["type"] == "library"

def test_spdx_export_format(sample_spec):
    sbom = CycloneDXExporter.export(sample_spec, format=SBOMFormat.SPDX)
    
    assert sbom["spdxVersion"] == "SPDX-2.3"
    assert len(sbom["packages"]) == 1
    
    pkg = sbom["packages"][0]
    assert pkg["name"] == "test-server"
    assert pkg["versionInfo"] == "1.0.0"

def test_cyclonedx_determinism(sample_spec):
    sbom1 = CycloneDXExporter.export(sample_spec)
    sbom2 = CycloneDXExporter.export(sample_spec)
    assert sbom1["serialNumber"] == sbom2["serialNumber"]

def test_purl_generation():
    spec = ServerPackageSpec(
        package_name="test-server",
        purl="",
        ecosystem="cargo",
        versions=()
    )
    sbom = CycloneDXExporter.export(spec)
    assert sbom["components"][0]["purl"] == "pkg:cargo/test-server"

