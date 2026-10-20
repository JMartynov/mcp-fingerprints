import json
import gzip
import re
from pathlib import Path
import os

# Load passports
passports = {}
with gzip.open('passports.json.gz', 'rt') as f:
    data = json.load(f)
    passports = data.get('passports', {})

# Build search index
index_urls = {}
index_names = {}
index_owner_repo = {}

for filepath, passport in passports.items():
    p_name = passport.get('package_name')
    if p_name:
        index_names[p_name.lower()] = filepath
        
    aliases = passport.get('aliases', [])
    for a in aliases:
        if a:
            index_names[a.lower()] = filepath
            
    disp_name = passport.get('display_name')
    if disp_name:
        index_names[disp_name.lower()] = filepath
    
    urls = []
    if passport.get('repository_url'):
        urls.append(passport['repository_url'])
    if passport.get('homepage_url'):
        urls.append(passport['homepage_url'])
    
    for url in urls:
        if not url:
            continue
        index_urls[url.lower().rstrip('/')] = filepath
        
        # Extract owner/repo
        m = re.search(r'github\.com/([^/]+)/([^/]+)', url.lower())
        if m:
            owner, repo = m.groups()
            repo = repo.replace('.git', '')
            index_owner_repo[f"{owner}/{repo}"] = filepath

def find_in_repo(candidate):
    # Additionally check the actual data/fingerprints directory just in case it's there but not in passports.json.gz yet
    # Or just use passports since the prompt says "cross-reference each candidate against data/fingerprints/ and passports.json.gz"
    
    c_name = candidate.get('name')
    if c_name:
        c_name = c_name.lower()
    else:
        c_name = ''
        
    c_loc = candidate.get('location')
    if c_loc:
        c_loc = c_loc.lower().rstrip('/')
    else:
        c_loc = ''
    
    # 1. Exact URL match
    if c_loc and c_loc in index_urls:
        return index_urls[c_loc]
    
    # 2. Owner/repo match from URL
    if c_loc:
        m = re.search(r'github\.com/([^/]+)/([^/]+)', c_loc)
        if m:
            owner, repo = m.groups()
            repo = repo.replace('.git', '')
            key = f"{owner}/{repo}"
            if key in index_owner_repo:
                return index_owner_repo[key]
            
    # 3. Exact name match
    if c_name and c_name in index_names:
        return index_names[c_name]
    
    # Check data/fingerprints directly
    # Sometimes the filename is derived from the repo name or package name
    if c_name:
        for root, dirs, files in os.walk('data/fingerprints'):
            for f in files:
                if f.endswith('.json'):
                    # Strip .json
                    fname = f[:-5].lower()
                    if c_name == fname or (m and f"{owner}_{repo}".lower() == fname):
                        return os.path.join(root, f)
            
    return None

def analyze_issue(candidate):
    loc = candidate.get('location') or ''
    loc = loc.lower()
    
    name = candidate.get('name') or ''
    name = name.lower()
    
    desc = candidate.get('description') or ''
    desc = desc.lower()
    
    eco = candidate.get('ecosystem') or ''
    eco = eco.lower()

    if 'docker' in loc or 'docker pull' in desc or 'docker' in desc or 'hub.docker.com' in loc:
        return ('BINARY_CONTAINER_ONLY', 'Distributed strictly as Docker Hub image without npm/PyPI manifest.', 'Docker Hub API crawler for docker-mcp tags.')
    if 'glama.ai' in loc or 'pulsemcp' in loc or 'mcp.so' in loc or 'smithery.ai' in loc:
        return ('ALTERNATIVE_REGISTRY_ONLY', 'Listed only on alternative directories without public registry release.', 'Registry crawler additions for Glama.ai/PulseMCP/Mcp.so.')
    if eco in ['swift', 'php', 'elixir', 'ruby']:
        return ('EMERGING_LANGUAGE_ECOSYSTEM', f'Implemented in {eco} lacking language crawlers.', f'{eco.capitalize()} crawler additions or Package Index connectors.')
    if 'uvx' in loc or 'uvx' in desc or 'standalone' in desc or 'script' in loc or 'gist' in loc:
        return ('UVX_STANDALONE_SCRIPT', 'Single-file Python UVX script or script header without pyproject.toml package distribution.', 'Single-file script header parsing recipes.')
    if 'monorepo' in desc or 'monorepo' in loc or '/packages/' in loc or '/servers/' in loc or '/tools/mcp/' in loc or '/tree/' in loc:
        return ('MONOREPO_NESTED_PATH', 'Located within a large monorepo without an independent GitHub repository.', 'Monorepo directory traversal crawler rules.')
    
    # Fallbacks
    if eco == 'python':
        return ('UVX_STANDALONE_SCRIPT', 'Single-file Python UVX script or script header without pyproject.toml package distribution.', 'Single-file script header parsing recipes.')
    elif eco in ['docker', 'go', 'rust', 'c++']:
         return ('BINARY_CONTAINER_ONLY', 'Distributed strictly as Docker Hub image without npm/PyPI manifest.', 'Docker Hub API crawler for docker-mcp tags.')
    elif 'github' in loc and 'mcp' in loc:
         return ('MONOREPO_NESTED_PATH', 'Located within a large monorepo without an independent GitHub repository.', 'Monorepo directory traversal crawler rules.')
    else:
        return ('ALTERNATIVE_REGISTRY_ONLY', 'Listed only on alternative directories without public registry release.', 'Registry crawler additions for Glama.ai/PulseMCP/Mcp.so.')

with open('docs/research/mcp_candidates_by_group.json') as f:
    data = json.load(f)

candidates = data["monorepo_docker_emerging"]

results = []
for c in candidates:
    match = find_in_repo(c)
    
    res = {
        'name': c.get('name', ''),
        'location': c.get('location', ''),
        'ecosystem': c.get('ecosystem', ''),
        'in_repo': bool(match),
        'matched_passport': match if match else None,
    }
    
    if not match:
        issue_type, details, remedy = analyze_issue(c)
        res['issue_type'] = issue_type
        res['issue_details'] = details
        res['remedy'] = remedy
    else:
        res['issue_type'] = None
        res['issue_details'] = None
        res['remedy'] = None
        
    results.append(res)

with open('docs/research/audit_group_5_monorepo_docker_emerging.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Audited {len(results)} candidates. {sum(1 for r in results if r['in_repo'])} matched.")
