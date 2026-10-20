import json
from mcp_fingerprints.canonicalizer import extract_tool_signature, compute_toolset_canonical_hash

file_path = "data/fingerprints/@codescene_codehealth-mcp.json"

with open(file_path, "r") as f:
    data = json.load(f)

for version_obj in data["versions"]:
    if version_obj["version"] in ["1.0.0", "1.5.11"]:
        # Re-hash tools
        new_tools = []
        for tool_dict in version_obj.get("tool_signatures", []):
            sig = extract_tool_signature(tool_dict)
            new_tools.append(sig.to_dict())
            
        version_obj["tool_signatures"] = new_tools
        version_obj["toolset_canonical_hash"] = compute_toolset_canonical_hash(new_tools)

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

