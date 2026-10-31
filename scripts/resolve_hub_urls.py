import json
import os
import glob
from concurrent.futures import ThreadPoolExecutor
import urllib.error

from mcp_fingerprints.hub_resolver import resolve_pypi_repository, resolve_npm_repository

def needs_resolution(repo_url):
    if not repo_url:
        return True
    if "smithery.ai" in repo_url or "glama.ai" in repo_url:
        return True
    return False

def process_file(filepath):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            
        pkg = data.get("package_name")
        eco = data.get("ecosystem")
        repo = data.get("repository_url")
        
        if pkg and eco in ["pypi", "npm"] and needs_resolution(repo):
            resolved = None
            if eco == "pypi":
                resolved = resolve_pypi_repository(pkg)
            elif eco == "npm":
                resolved = resolve_npm_repository(pkg)
                
            if resolved:
                print(f"[{eco}] Resolved {pkg}: {repo} -> {resolved}")
                data["repository_url"] = resolved
                
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2)
                    f.write("\n")
                return (data.get("name"), resolved)
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return None

def update_catalog(resolved_map):
    if not resolved_map:
        return
        
    catalog_path = "web/catalog.json"
    with open(catalog_path, "r") as f:
        catalog = json.load(f)
        
    updated = 0
    for entry in catalog:
        name = entry.get("name")
        if name in resolved_map:
            entry["repository_url"] = resolved_map[name]
            updated += 1
            
    if updated > 0:
        with open(catalog_path, "w") as f:
            # Compact single-line format as requested for catalog
            json.dump(catalog, f, separators=(',', ':'))
            f.write("\n")
        print(f"Updated {updated} entries in web/catalog.json")

def main():
    files = glob.glob("data/fingerprints/*.json")
    resolved_map = {}
    
    print(f"Scanning {len(files)} passports...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(process_file, files))
        
    for r in results:
        if r:
            name, resolved = r
            resolved_map[name] = resolved
            
    print(f"Resolved {len(resolved_map)} URLs")
    update_catalog(resolved_map)

if __name__ == "__main__":
    main()
