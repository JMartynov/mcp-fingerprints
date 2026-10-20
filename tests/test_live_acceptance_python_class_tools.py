import json
import pytest
from mcp_fingerprints.ast_parser import parse_python_mcp_ast
from mcp_fingerprints.schema_validator import PassportSchemaValidator
from mcp_fingerprints.models import ServerPackageSpec

MOCK_OUROBOROS_CODE = """
class OuroborosEvaluateTool(MCPToolDefinition):
    name = "ouroboros_evaluate"
    description = "Evaluate tool"
    parameters = [
        MCPToolParameter(name="artifact", description="Artifact", required=True, type=ToolInputType.STRING),
        MCPToolParameter(name="flag", description="Flag", required=False, type=ToolInputType.BOOLEAN)
    ]

_RALPH = "ouroboros_ralph"
class OuroborosRalphTool(MCPToolDefinition):
    name = _RALPH
    description = "Ralph tool"
    parameters = []
"""

def test_ast_parsing_mcp_tool_definition():
    tools = parse_python_mcp_ast(MOCK_OUROBOROS_CODE)
    
    assert len(tools) == 2
    
    evaluate_tool = next((t for t in tools if t["name"] == "ouroboros_evaluate"), None)
    assert evaluate_tool is not None
    assert evaluate_tool["description"] == "Evaluate tool"
    assert "artifact" in evaluate_tool["inputSchema"]["properties"]
    assert evaluate_tool["inputSchema"]["properties"]["artifact"]["type"] == "string"
    assert "artifact" in evaluate_tool["inputSchema"]["required"]
    assert "flag" not in evaluate_tool["inputSchema"]["required"]
    
    ralph_tool = next((t for t in tools if t["name"] == "ouroboros_ralph"), None)
    assert ralph_tool is not None
    assert ralph_tool["description"] == "Ralph tool"
    assert len(ralph_tool["inputSchema"]["properties"]) == 0

def test_passport_ouroboros_enrichment():
    with open("data/fingerprints/Q00_ouroboros.json", "r") as f:
        data = json.load(f)
        
        data.pop('passport_schema_version', None)
    spec = ServerPackageSpec(**data)
    
    # Validation against PassportSchemaValidator should pass
    is_valid, errors = PassportSchemaValidator.validate_file('data/fingerprints/Q00_ouroboros.json')
    assert is_valid, f'Errors: {errors}'
    
    latest_version = None
    for v in spec.versions:
        if (v['version'] if isinstance(v, dict) else getattr(v, 'version', None)) == "0.59.2":
            latest_version = v
            break
            
    assert latest_version is not None
    assert len(latest_version.get('tool_signatures', []) if isinstance(latest_version, dict) else getattr(latest_version, 'tool_signatures', [])) >= 30
    assert latest_version.get('capabilities', {}).get('tools') if isinstance(latest_version, dict) else getattr(latest_version, 'capabilities', {}).get('tools') is True
    
    names = [t.get('name') if isinstance(t, dict) else t.name for t in (latest_version.get('tool_signatures', []) if isinstance(latest_version, dict) else getattr(latest_version, 'tool_signatures', []))]
    assert "ouroboros_evaluate" in names
    assert "ouroboros_ralph" in names
    assert latest_version.get('toolset_canonical_hash', '') if isinstance(latest_version, dict) else getattr(latest_version, 'toolset_canonical_hash', '').startswith("sha256:")

