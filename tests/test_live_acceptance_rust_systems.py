import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_fingerprints.ast_parser import parse_rust_mcp_code
from mcp_fingerprints.crawler.crates_io import get_mcp_crates
from mcp_fingerprints.schema_validator import PassportSchemaValidator

def test_rust_rmcp_ast_parsing():
    code = """
    #[tool(description = "Provides codescene metrics")]
    async fn get_metrics(repo_url: String, limit: i32) -> Result<String, String> {
        Ok("metrics".to_string())
    }
    """
    tools = parse_rust_mcp_code(code)
    assert len(tools) == 1
    t = tools[0]
    assert t["name"] == "get_metrics"
    assert t["description"] == "Provides codescene metrics"
    assert t["inputSchema"]["type"] == "object"
    assert "repo_url" in t["inputSchema"]["properties"]
    assert "limit" in t["inputSchema"]["properties"]
    assert t["inputSchema"]["properties"]["repo_url"]["type"] == "string"
    assert t["inputSchema"]["properties"]["limit"]["type"] == "number"

@patch("urllib.request.urlopen")
def test_crates_io_crawler_mocked(mock_urlopen):
    mock_resp1 = MagicMock()
    mock_resp1.__enter__.return_value = mock_resp1
    mock_resp1.read.return_value = json.dumps({
        "crates": [{"name": "mcp-server-rust", "repository": "https://github.com/rust/mcp", "description": "Rust MCP"}]
    }).encode("utf-8")
    
    mock_resp2 = MagicMock()
    mock_resp2.__enter__.return_value = mock_resp2
    mock_resp2.read.return_value = json.dumps({"crates": []}).encode("utf-8")
    
    mock_resp3 = MagicMock()
    mock_resp3.__enter__.return_value = mock_resp3
    mock_resp3.read.return_value = json.dumps({"crates": []}).encode("utf-8")

    mock_urlopen.side_effect = [mock_resp1, mock_resp2, mock_resp3]
    
    crates = get_mcp_crates()
    assert len(crates) == 1
    assert crates[0]["name"] == "mcp-server-rust"

def test_codescene_mcp_passport_validation():
    # Verify the ingested passport exists and is valid
    passport_path = Path("data/fingerprints/@codescene_codehealth-mcp.json")
    assert passport_path.exists()
    
    with open(passport_path) as f:
        data = json.load(f)
        
    is_valid, errors = PassportSchemaValidator.validate_passport_dict(data)
    assert is_valid, f"Passport should be valid, errors: {errors}"
    assert data["package_name"] == "@codescene/codehealth-mcp"
    
    v0 = data["versions"][0]
    assert len(v0["tool_signatures"]) == 28
    assert len(v0["prompt_signatures"]) == 5
    assert len(v0["resource_signatures"]) == 19
    assert v0["toolset_canonical_hash"] == "sha256:a5d60a5fd438dfd82ed72b1b7c2fa25bd879f4f3473665bc038872bdaf1fc2af"

