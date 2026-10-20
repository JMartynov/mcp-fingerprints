import json

with open('docs/research/audit_group_5_monorepo_docker_emerging.json') as f:
    results = json.load(f)

# Write to markdown
with open('docs/research/audit_group_5_monorepo_docker_emerging.md', 'w') as f:
    f.write("# Audit Group 5: Monorepos, Alternative Registries, Docker Containers & Emerging Ecosystems\n\n")
    
    # Category breakdown
    f.write("## Category Breakdown\n\n")
    breakdown = {}
    for r in results:
        it = r.get('issue_type')
        if not r['in_repo'] and it:
            breakdown[it] = breakdown.get(it, 0) + 1
            
    f.write("| Issue Type | Count |\n")
    f.write("| --- | --- |\n")
    for k, v in breakdown.items():
        f.write(f"| {k} | {v} |\n")
    f.write(f"| MATCHED_IN_REPO | {sum(1 for r in results if r['in_repo'])} |\n")
    f.write(f"| **Total** | **{len(results)}** |\n\n")
    
    # Full table
    f.write("## Candidate Audit Results\n\n")
    f.write("| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |\n")
    f.write("| --- | --- | --- | --- | --- |\n")
    
    for r in results:
        name = r.get('name', '')
        loc = r.get('location', '')
        present = '✅ Yes' if r['in_repo'] else '❌ No'
        issue = r.get('issue_type') or 'N/A'
        remedy = r.get('remedy') or 'N/A'
        f.write(f"| {name} | {loc} | {present} | {issue} | {remedy} |\n")

print("Generated markdown.")
