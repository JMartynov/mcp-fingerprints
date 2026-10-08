import pytest
from scripts.validate_passports import validate_passports
from pathlib import Path
import json

@pytest.fixture
def mock_passports_dir(tmp_path):
    data_dir = tmp_path / "data" / "fingerprints"
    data_dir.mkdir(parents=True)
    
    valid_passport = {
        "passport_schema_version": "1.1.0",
        "package_name": "valid-mcp-server",
        "purl": "pkg:npm/valid-mcp-server",
        "ecosystem": "npm",
        "display_name": "Valid MCP Server",
        "versions": [
            {
                "version": "1.0.0",
                "toolset_canonical_hash": "testhash",
                "tool_signatures": [
                    {
                        "name": "test_tool",
                        "canonical_hash": "toolhash",
                        "description": "Test tool description",
                        "inputSchema": {"type": "object"}
                    }
                ]
            }
        ]
    }
    
    invalid_passport_missing_field = {
        "passport_schema_version": "1.1.0",
        "purl": "pkg:npm/invalid-mcp-server",
        "ecosystem": "npm",
        # missing package_name
        "versions": []
    }
    
    invalid_passport_bad_tool = {
        "passport_schema_version": "1.1.0",
        "package_name": "bad-tool-server",
        "purl": "pkg:npm/bad-tool-server",
        "ecosystem": "npm",
        "versions": [
            {
                "version": "1.0.0",
                "toolset_canonical_hash": "testhash",
                "tool_signatures": [
                    {
                        "name": "test_tool",
                        "canonical_hash": "toolhash"
                        # missing description string and inputSchema dict
                    }
                ]
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
    assert "All passports valid." in captured.out

def test_validate_passports_missing_field(mock_passports_dir, capsys):
    data_dir, _, invalid_passport_missing_field, _ = mock_passports_dir
    with open(data_dir / "invalid_missing.json", "w") as f:
        json.dump(invalid_passport_missing_field, f)
        
    assert validate_passports(str(data_dir)) == 1
    captured = capsys.readouterr()
    assert "Missing required field 'package_name'" in captured.out

def test_validate_passports_bad_tool(mock_passports_dir, capsys):
    data_dir, _, _, invalid_passport_bad_tool = mock_passports_dir
    with open(data_dir / "invalid_bad_tool.json", "w") as f:
        json.dump(invalid_passport_bad_tool, f)
        
    assert validate_passports(str(data_dir)) == 1
    captured = capsys.readouterr()
    assert "missing 'description' string" in captured.out
    assert "missing 'inputSchema' dict" in captured.out
