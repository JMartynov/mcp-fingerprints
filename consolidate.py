import json
import collections

groups = [
    ("rust_systems", "docs/research/audit_group_1_rust_systems.json"),
    ("go_cloud_native", "docs/research/audit_group_2_go_cloud_native.json"),
    ("jvm_dotnet_enterprise", "docs/research/audit_group_3_jvm_dotnet_enterprise.json"),
    ("regional_international", "docs/research/audit_group_4_regional_international.json"),
    ("monorepo_docker_emerging", "docs/research/audit_group_5_monorepo_docker_emerging.json"),
]

master_list = []

for group_name, filepath in groups:
    with open(filepath, 'r') as f:
        data = json.load(f)
        for item in data:
            item['group'] = group_name
            # Reorder keys to match the expected schema closely, though order doesn't strictly matter for JSON
            new_item = {
                "name": item.get("name"),
                "group": group_name,
                "location": item.get("location"),
                "ecosystem": item.get("ecosystem"),
                "in_repo": item.get("in_repo"),
                "matched_passport": item.get("matched_passport"),
                "issue_type": item.get("issue_type"),
                "issue_details": item.get("issue_details"),
                "remedy": item.get("remedy")
            }
            master_list.append(new_item)

with open("docs/research/master_mcp_ecosystem_audit_1000.json", 'w') as f:
    json.dump(master_list, f, indent=2)

