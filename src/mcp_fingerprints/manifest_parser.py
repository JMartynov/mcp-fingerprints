import json
from typing import Any, Dict, List

def parse_manifest_mcp_tools(code: str) -> List[Dict[str, Any]]:
    """Parse JSON/YAML tool manifests for tools."""
    tools = []
    
    try:
        data = json.loads(code)
    except json.JSONDecodeError:
        try:
            import yaml
            data = yaml.safe_load(code)
        except Exception:
            return tools

    if not isinstance(data, (dict, list)):
        return tools

    tool_list = []
    if isinstance(data, list):
        tool_list = data
    elif isinstance(data, dict):
        if "tools" in data and isinstance(data["tools"], list):
            tool_list = data["tools"]
        elif "tool_definitions" in data and isinstance(data["tool_definitions"], list):
            tool_list = data["tool_definitions"]

    for tool in tool_list:
        if isinstance(tool, dict) and "name" in tool:
            name = tool.get("name")
            desc = tool.get("description", name)
            input_schema = tool.get("inputSchema") or tool.get("parameters") or {"type": "object", "properties": {}, "required": []}
            tools.append({
                "name": name,
                "description": desc,
                "inputSchema": input_schema
            })

    return tools
