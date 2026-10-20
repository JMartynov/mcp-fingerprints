import json

with open('docs/research/mcp_candidates_by_group.json') as f:
    data = json.load(f)

candidates = data["monorepo_docker_emerging"]
print(f"Loaded {len(candidates)} candidates.")

for c in candidates[:5]:
    print(c)
