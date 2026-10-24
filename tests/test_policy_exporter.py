import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature
from mcp_fingerprints.policy_exporter import (
    PolicyExporter,
    PolicyFormat,
    PolicyMode,
    RegoPolicyCompiler,
    EnvoyWasmConfigCompiler
)

@pytest.fixture
def mock_passport():
    t1 = ToolContractSignature(
        name="read_file",
        canonical_hash="hash1",
        annotations={"readOnlyHint": True},
        input_schema={
            "type": "object",
            "required": ["filepath"],
            "properties": {
                "filepath": {"type": "string"}
            }
        }
    )
    t2 = ToolContractSignature(
        name="delete_file",
        canonical_hash="hash2",
        annotations={"destructiveHint": True},
        input_schema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string"}
            }
        }
    )
    t3 = ToolContractSignature(
        name="execute_command",
        canonical_hash="hash3",
        input_schema={
            "type": "object",
            "required": ["cmd"],
            "properties": {
                "cmd": {"type": "string"}
            }
        }
    )
    
    v1 = VersionFingerprint(
        version="1.0.0",
        toolset_canonical_hash="toolset_hash_xyz",
        tool_signatures=(t1, t2, t3)
    )
    
    spec = ServerPackageSpec(
        package_name="test-mcp-server",
        purl="pkg:test/test-mcp-server@1.0.0",
        ecosystem="test",
        versions=(v1,)
    )
    return spec

def test_rego_compiler_allowlist(mock_passport):
    rego = RegoPolicyCompiler.compile(mock_passport, PolicyMode.ALLOWLIST)
    assert "package mcp.authz" in rego
    assert "import rego.v1" in rego
    assert "default allow := false" in rego
    
    # All 3 tools should be allowed
    assert 'input.params.name == "read_file"' in rego
    assert 'input.params.name == "delete_file"' in rego
    assert 'input.params.name == "execute_command"' in rego
    
    # Required parameters should be checked
    assert 'object.get(input.params.arguments, "filepath", null) != null' in rego

def test_rego_compiler_read_only(mock_passport):
    rego = RegoPolicyCompiler.compile(mock_passport, PolicyMode.READ_ONLY)
    
    assert 'input.params.name == "read_file"' in rego
    assert 'input.params.name == "delete_file"' not in rego
    assert 'input.params.name == "execute_command"' not in rego # not prefixed with read-only

def test_rego_compiler_strict(mock_passport):
    rego = RegoPolicyCompiler.compile(mock_passport, PolicyMode.STRICT)
    
    # Should have parameter type checking
    assert 'val_filepath := object.get(input.params.arguments, "filepath", null)' in rego
    assert 'filepath_is_type := is_string(val_filepath)' in rego
    
    # Destructive hints require admin
    assert 'input.client_role == "admin"' in rego
    
    # Path sanitization guards
    assert 'not contains(val_sec_path, "..")' in rego
    assert 'not contains(val_sec_cmd, "$(")' in rego

def test_envoy_compiler(mock_passport):
    config = EnvoyWasmConfigCompiler.compile(mock_passport, PolicyMode.STRICT)
    assert config["name"] == "envoy.filters.http.rbac"
    assert config["mode_constraints"] == "strict"
    assert len(config["mcp_allowed_tools"]) == 3
    assert "read_file" in config["mcp_allowed_tools"]
    
def test_envoy_compiler_read_only(mock_passport):
    config = EnvoyWasmConfigCompiler.compile(mock_passport, PolicyMode.READ_ONLY)
    assert len(config["mcp_allowed_tools"]) == 1
    assert "read_file" in config["mcp_allowed_tools"]

@patch("mcp_fingerprints.policy_exporter.Path.is_file")
def test_policy_exporter_json_format(mock_is_file, mock_passport):
    mock_is_file.return_value = False
    with patch("mcp_fingerprints.matcher.FingerprintMatcher.load_default"):
        with patch("mcp_fingerprints.matcher.FingerprintMatcher") as mock_matcher:
            # We bypass the actual DB lookup for unit test by directly using export with spec
            result = PolicyExporter.export(mock_passport, fmt=PolicyFormat.JSON, mode=PolicyMode.STRICT)
            parsed = json.loads(result)
            assert parsed["package_name"] == "test-mcp-server"
            assert parsed["mode_constraints"] == "strict"
            assert parsed["safety_classification"] == "verified"
            assert parsed["annotation_summary"]["allowed_tools"] == 3

def test_policy_exporter_disk_write(tmp_path, mock_passport):
    out_file = tmp_path / "policy.rego"
    PolicyExporter.export(mock_passport, fmt=PolicyFormat.REGO, mode=PolicyMode.STRICT, output_path=out_file)
    assert out_file.exists()
    content = out_file.read_text()
    assert "package mcp.authz" in content

def test_policy_exporter_not_found():
    with pytest.raises(ValueError):
        PolicyExporter.export("non-existent-passport")
        
