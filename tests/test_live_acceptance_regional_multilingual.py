import pytest
import json
from pathlib import Path
from mcp_fingerprints.sanitizer import sanitize_unicode_text, sanitize_metadata, sanitize_tool_definition
from mcp_fingerprints.schema_validator import PassportSchemaValidator

def test_sanitize_preserves_cjk():
    tool = {
        "name": "获取天气",
        "description": "This is a test tool that fetches weather in Chinese",
        "inputSchema": {"type": "object", "properties": {}}
    }
    
    sanitized = sanitize_tool_definition(tool)
    assert sanitized is not None
    assert sanitized["name"] == "获取天气"
    
def test_sanitize_unicode_text():
    text = "  Hello \x00World\n  测试   "
    assert sanitize_unicode_text(text) == "Hello World 测试"

def test_sanitize_metadata():
    metadata = {
        "description": "测试\x00描述",
        "author": "User\x01Name",
        "keywords": ["tag1", "标签2\x02"],
        "other": "untouched\x00"
    }
    sanitized = sanitize_metadata(metadata)
    assert sanitized["description"] == "测试描述"
    assert sanitized["author"] == "UserName"
    assert sanitized["keywords"] == ["tag1", "标签2"]
    assert sanitized["other"] == "untouched\x00"

def test_multilingual_query_expansion():
    from mcp_fingerprints.synchronizer import PassportSynchronizer
    from unittest.mock import patch, MagicMock
    
    synchronizer = PassportSynchronizer(output_dir=Path("tmp"))
    
    with patch("mcp_fingerprints.synchronizer.fetch_json") as mock_fetch, \
         patch.object(synchronizer, '_check_budget'), \
         patch("urllib.request.urlopen"):
        
        mock_fetch.return_value = ({"items": [{"full_name": "test/test", "description": "test"}]}, None)
        
        synchronizer.checkpoint_data = {}
        synchronizer.budget_seconds = 1000
        
        # Test just the subset we want by simulating starting at polyglot substage
        synchronizer.checkpoint_data["current_stage"] = "stage_discover_new"
        synchronizer.checkpoint_data["substage"] = "polyglot"
        
        synchronizer.discover_new_mcps(limit=1, polyglot=True)
        
        # Verify the encoded multilingual queries are called
        calls = [call[0][0] for call in mock_fetch.call_args_list]
        
        # Polyglot query language:rust should have space encoded as %20
        assert any("topic%3Amcp-server%20language%3Arust" in c for c in calls)
        
        # Verify Dify MCP is encoded
        assert any("Dify%20MCP" in c for c in calls)
        
        # Verify Chinese keyword is encoded
        assert any("%E6%A8%A1%E5%9E%8B%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8D%8F%E8%AE%AE" in c for c in calls)


def test_passport_validation():
    passport_path = Path("data/fingerprints/github_Yanyutin753_mcp-weather.json")
    if not passport_path.exists():
        data = {
          "package_name": "github_Yanyutin753_mcp-weather",
          "purl": "pkg:github/Yanyutin753/mcp-weather",
          "ecosystem": "github",
          "repository_url": "https://github.com/Yanyutin753/mcp-weather",
          "description": "基于模型上下文协议 (MCP) 的天气查询服务端，提供实时气象数据和预报功能。",
          "versions": [
            {
              "version": "latest",
              "toolset_canonical_hash": "sha256:748716d3c0aeee3787c59537af8183b96dec59c2b6781a79da1af69259c55b49",
              "tool_signatures": [
                {
                  "name": "获取天气",
                  "canonical_hash": "sha256:124a2aa9ceab0791e784e90e3d5edf79d99a79f0f10b0d6e99bcbc4800b4c268",
                  "description": "查询指定城市的当前天气情况",
                  "is_mutating": False,
                  "property_keys": ["city"],
                  "required_keys": ["city"],
                  "parameter_types": {"city": "string"},
                  "input_schema": {
                    "type": "object",
                    "properties": {
                      "city": {
                        "type": "string",
                        "description": "城市名称，例如 北京"
                      }
                    },
                    "required": ["city"]
                  },
                  "output_schema": None,
                  "description_hash": "sha256:bdd41ae5b782d1e817a78a3fa6f25e5929f22c7f5c18f81f7720208fbf79e291",
                  "parameters": [
                    {
                      "name": "city",
                      "type": "string",
                      "description": "城市名称，例如 北京",
                      "required": True,
                      "default": None,
                      "enum": None,
                      "format": None,
                      "items_type": None,
                      "nested_properties": None
                    }
                  ],
                  "annotations": {}
                }
              ],
              "prompt_signatures": [],
              "resource_signatures": [],
              "release_date": None,
              "capabilities": {
                "tools": True,
                "prompts": False,
                "resources": False
              },
              "required_env_vars": [],
              "transport": "stdio"
            }
          ],
          "aliases": [],
          "sources_merged": ["github"]
        }
        passport_path.parent.mkdir(parents=True, exist_ok=True)
        with open(passport_path, "w") as f:
            json.dump(data, f)
            
    is_valid, errors = PassportSchemaValidator.validate_file(passport_path)
    assert is_valid, f"Passport validation failed with errors: {errors}"
    
    with open(passport_path) as f:
        data = json.load(f)
        assert data["package_name"] == "github_Yanyutin753_mcp-weather"
        assert "获取天气" in data["versions"][0]["tool_signatures"][0]["name"]
