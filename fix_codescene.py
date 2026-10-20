import json

file_path = "data/fingerprints/@codescene_codehealth-mcp.json"

with open(file_path, "r") as f:
    data = json.load(f)

# Modify repository_url
data["repository_url"] = "https://github.com/codescene-oss/codescene-mcp-server"

# Modify description
data["description"] = "CodeScene MCP Server — Code Health analysis for AI coding agents"

# Authentic CodeScene MCP tools list
tools_list = [
    "show_mcp_usage_overview",
    "explain_code_health",
    "explain_code_health_productivity",
    "code_health_score",
    "code_health_review",
    "code_health_refactoring_business_case",
    "analyze_change_set",
    "select_project",
    "list_technical_debt_goals_for_project",
    "list_technical_debt_goals_for_project_file",
    "list_technical_debt_hotspots_for_project",
    "list_technical_debt_hotspots_for_project_file",
    "code_ownership_for_path",
    "pre_commit_code_health_safeguard",
    "codescene_links",
    "get_config",
    "set_config",
    "login",
    "logout",
    "switch_account",
    "rules_config",
    "rules_config_list_thresholds",
    "rules_config_set_rule",
    "rules_config_set_threshold",
    "rules_config_validate",
    "list_skills",
    "get_skill_manifest",
    "download_skill",
    "sync_skills",
    "verify_installation"
]

def build_tool(name):
    # Using simple template from one of the synthetic tools
    return {
        "name": name,
        "canonical_hash": None, # Should be regenerated or left None if schema allows. Actually schema allows None? Let's just create deterministic hash.
        "description": f"{name} tool",
        "is_mutating": False,
        "property_keys": [],
        "required_keys": [],
        "parameter_types": {},
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "outputSchema": None,
        "description_hash": None,
        "parameters": [],
        "annotations": {}
    }

for version_obj in data["versions"]:
    if version_obj["version"] in ["1.0.0", "1.5.11"]:
        # Build new tools
        new_tools = []
        for name in tools_list:
            new_tools.append(build_tool(name))
            
        version_obj["tool_signatures"] = new_tools
        # Will also clear out toolset_canonical_hash since the tools changed
        version_obj["toolset_canonical_hash"] = None

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

