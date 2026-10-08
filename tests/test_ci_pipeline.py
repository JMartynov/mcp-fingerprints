import pytest
from scripts.validate_passports import validate_passports
from pathlib import Path
import json

@pytest.fixture
def mock_passports_dir(tmp_path):
    data_dir = tmp_path / "data" / "fingerprints"
    data_dir.mkdir(parents=True)
    
    valid_hash = "sha256:ac0d3768d44f2b087db649ed07c4c594e41816b33310b1ea14ad39175f90bf4d"
    tool_hash = "sha256:0e5e95a3b32a01a76d7e64e4ac5aeecf6495e9773ca652201cd95b680bb34749"
    desc_hash = "sha256:537e415efdfd9b5da97ebb2aab8b7fe3cf38adf750b6c69ba1493e9e0abc164c"

    valid_passport = {
        "package_name": "valid-mcp-server",
        "purl": "pkg:npm/valid-mcp-server",
        "ecosystem": "npm",
        "display_name": "Valid MCP Server",
        "versions": [
            {
                "version": "1.0.0",
                "toolset_canonical_hash": valid_hash,
                "tool_signatures": [
                    {
                        "name": "test_tool",
                        "canonical_hash": tool_hash,
                        "description_hash": desc_hash,
                        "property_keys": ["param1"],
                        "required_keys": [],
                        "parameter_types": {"param1": "string"},
                    }
                ],
                "prompt_signatures": [],
                "resource_signatures": [],
                "capabilities": {"tools": True}
            }
        ]
    }
    
    invalid_passport_missing_field = {
        "purl": "pkg:npm/invalid-mcp-server",
        "ecosystem": "npm",
        # missing package_name
        "versions": []
    }
    
    invalid_passport_bad_tool = {
        "package_name": "bad-tool-server",
        "purl": "pkg:npm/bad-tool-server",
        "ecosystem": "npm",
        "versions": [
            {
                "version": "1.0.0",
                "toolset_canonical_hash": "invalid_hash_format",
                "tool_signatures": [
                    {
                        "name": "test_tool",
                        "canonical_hash": "invalid_hash"
                    }
                ],
                "prompt_signatures": [],
                "resource_signatures": [],
                "capabilities": {}
            }
        ]
    }
    
    return data_dir, valid_passport, invalid_passport_missing_field, invalid_passport_bad_tool

def test_validate_passports_valid(mock_passports_dir, capsys):
    data_dir, valid_passport, _, _ = mock_passports_dir
    with open(data_dir / "valid.json", "w") as f:
        json.dump(valid_passport, f)
        
    assert validate_passports(str(data_dir)) == 0
    captured = capsys.readouterr()
    assert "SUCCESS" in captured.out

def test_validate_passports_missing_field(mock_passports_dir, capsys):
    data_dir, _, invalid_passport_missing_field, _ = mock_passports_dir
    with open(data_dir / "invalid_missing.json", "w") as f:
        json.dump(invalid_passport_missing_field, f)
        
    assert validate_passports(str(data_dir)) == 1
    captured = capsys.readouterr()
    assert "FAILED" in captured.out
    assert "package_name" in captured.out

def test_validate_passports_bad_tool(mock_passports_dir, capsys):
    data_dir, _, _, invalid_passport_bad_tool = mock_passports_dir
    with open(data_dir / "invalid_bad_tool.json", "w") as f:
        json.dump(invalid_passport_bad_tool, f)
        
    assert validate_passports(str(data_dir)) == 1
    captured = capsys.readouterr()
    assert "FAILED" in captured.out
    assert "Invalid toolset_canonical_hash" in captured.out
