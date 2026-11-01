import json
import gzip
import os

def normalize_catalog_tools(data):
    """
    Normalizes a catalog or passport item.
    Returns a dictionary with:
    - latest_version: str
    - tool_count: int
    - tools: list of tool dictionaries
    """
    if isinstance(data, list):
        return [normalize_server_item(item) for item in data]
    return normalize_server_item(data)

def normalize_server_item(item):
    latest_version = item.get("latest_version") or item.get("version")
    
    versions = item.get("versions", [])
    if not latest_version and versions:
        latest_version = versions[0].get("version", "1.0.0")
    if not latest_version:
        latest_version = "1.0.0"
        
    found = None
    for v in versions:
        if v.get("version") == latest_version:
            found = v
            break
            
    tools = []
    if found:
        if "tool_signatures" in found and found["tool_signatures"]:
            tools = found["tool_signatures"]
        elif "tools" in found and found["tools"]:
            tools = found["tools"]
        elif "tool_signatures" in item and item["tool_signatures"]:
            tools = item["tool_signatures"]
        elif "tools" in item and item["tools"]:
            tools = item["tools"]
    else:
        if "tool_signatures" in item and item["tool_signatures"]:
            tools = item["tool_signatures"]
        elif "tools" in item and item["tools"]:
            tools = item["tools"]

    return {
        "latest_version": latest_version,
        "tool_count": len(tools),
        "tools": tools
    }

def load_data(filepath):
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(filepath, 'rt', encoding='utf-8') as f:
            return json.load(f)
