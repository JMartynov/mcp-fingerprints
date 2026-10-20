import json
from mcp_fingerprints.canonicalizer import Canonicalizer

file_path = "data/fingerprints/@codescene_codehealth-mcp.json"

with open(file_path, "r") as f:
    data = json.load(f)

for version_obj in data["versions"]:
    if version_obj["version"] in ["1.0.0", "1.5.11"]:
        # Re-hash tools
        for tool in version_obj.get("tool_signatures", []):
            desc_hash = Canonicalizer.hash_string(tool.get("description", ""))
            tool["description_hash"] = desc_hash
            tool_hash = Canonicalizer.hash_tool(tool)
            tool["canonical_hash"] = tool_hash
            
        toolset_hash = Canonicalizer.hash_toolset(version_obj.get("tool_signatures", []))
        version_obj["toolset_canonical_hash"] = toolset_hash

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

