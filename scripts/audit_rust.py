import json
from pathlib import Path
import re

def search_repo(name, location, fingerprints, passports):
    # Try exact matches
    for f in fingerprints:
        d = f.get("data", {})
        if d.get("name") == name or d.get("location") == location:
            return f["path"]
        # Check aliases
        aliases = d.get("aliases", [])
        if name in aliases:
            return f["path"]
            
    for p in passports:
        if not isinstance(p, dict):
            continue
        if p.get("name") == name or p.get("location") == location:
            return "passports.json.gz"
            
    return None

def determine_issue(item):
    name = item["name"].lower()
    desc = item.get("description", "").lower()
    
    if "macro" in desc or "derive" in name or "declarative" in desc or "mcp-sdk-rs" in desc or "rmcp" in desc or "#[tool]" in desc:
        return "AST_UNSUPPORTED_SDK_MACRO", "Relies on macros (e.g., rmcp, #[tool]) or custom SDK routers that the static AST parser currently does not extract.", "Enhance parse_rust_mcp_code to correctly extract tool signatures from rust macros."
    if name.endswith("-core") or name.endswith("-transport") or name.endswith("-protocol") or name.endswith("-base") or name.endswith("-db"):
        return "MONOREPO_NESTED_PATH", "Crate is part of a larger Cargo workspace and published separately.", "Implement recursive Cargo workspace scanning to index sub-crates appropriately."
    if "cli" in name or "binary" in desc or "desktop" in desc or "clap" in name or "app" in name:
        return "BINARY_CONTAINER_ONLY", "Distributed as a compiled binary or CLI without clear library AST exports.", "Add binary probing for Rust CLI tools using stdio fallback."
    if "mcp" not in desc and "model-context-protocol" not in desc:
        return "KEYWORD_TAG_MISMATCH", "Does not explicitly use standard tags.", "Expand crawler queries."
        
    return "MISSING_REGISTRY_INDEXER_CRATES_IO", "Present on Crates.io but no crawler exists for the Rust ecosystem in the registry indexer.", "Implement a Crates.io registry crawler targeting the 'mcp' keyword."

def main():
    fingerprints_dir = Path("data/fingerprints")
    fingerprints = []
    for f in fingerprints_dir.rglob("*.json"):
        try:
            with open(f) as fp:
                fingerprints.append({"path": f.as_posix(), "data": json.load(fp)})
        except:
            pass

    passports = []
    import gzip
    if Path("passports.json.gz").exists():
        with gzip.open("passports.json.gz", "rt") as fp:
            try:
                passports = json.load(fp)
            except:
                pass

    with open("docs/research/mcp_candidates_by_group.json") as f:
        data = json.load(f)
    
    rust_systems = data.get("rust_systems", [])
    
    results = []
    for item in rust_systems:
        name = item["name"]
        location = item["location"]
        ecosystem = item.get("ecosystem", "rust")
        
        matched_path = search_repo(name, location, fingerprints, passports)
        
        entry = {
            "name": name,
            "location": location,
            "ecosystem": ecosystem,
            "in_repo": bool(matched_path),
            "matched_passport": matched_path if matched_path else None
        }
        
        if not matched_path:
            issue_type, issue_details, remedy = determine_issue(item)
            entry["issue_type"] = issue_type
            entry["issue_details"] = issue_details
            entry["remedy"] = remedy
            
        results.append(entry)
        
    with open("docs/research/audit_group_1_rust_systems.json", "w") as f:
        json.dump(results, f, indent=2)
        
    # Generate Markdown
    md_lines = [
        "# Audit Group 1: Rust & Systems Polyglot MCPs",
        "",
        "| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |",
        "|---|---|---|---|---|"
    ]
    
    counts = {}
    for r in results:
        present = "Yes" if r["in_repo"] else "No"
        issue_type = r.get("issue_type", "-")
        remedy = r.get("remedy", "-")
        md_lines.append(f"| {r['name']} | {r['location']} | {present} | {issue_type} | {remedy} |")
        
        if not r["in_repo"]:
            counts[issue_type] = counts.get(issue_type, 0) + 1
            
    md_lines.append("")
    md_lines.append("## Category Breakdown Summary")
    for k, v in counts.items():
        md_lines.append(f"- **{k}**: {v}")
        
    with open("docs/research/audit_group_1_rust_systems.md", "w") as f:
        f.write("\n".join(md_lines))

if __name__ == "__main__":
    main()
