
def match_monorepo_subpackage_dir(package_name: str, tree_paths: list[str]) -> str | None:
    """
    Match a package name to a specific subpackage directory in a monorepo structure.
    
    Args:
        package_name: The name of the package (e.g., "@modelcontextprotocol/server-postgres", "postgres").
        tree_paths: A list of file paths in the repository.
        
    Returns:
        The matched subpackage directory prefix (e.g., "packages/server-postgres/"), or None if no match.
    """
    # 1. Strip scope from package name
    clean_name = package_name.split('/')[-1]
    
    # 2. Generate variants
    variants = [clean_name]
    
    # Extract common suffixes or prefixes
    # e.g. server-postgres -> postgres
    # e.g. postgres-server -> postgres
    # e.g. mcp-server-postgres -> postgres
    
    if clean_name.startswith("server-"):
        variants.append(clean_name[len("server-"):])
    elif clean_name.startswith("mcp-server-"):
        variants.append(clean_name[len("mcp-server-"):])
        
    if clean_name.endswith("-server"):
        variants.append(clean_name[:-len("-server")])

    bases = ["packages", "servers", "src", "crates", "pkg"]
    
    # Build candidate prefixes
    candidate_prefixes = []
    for base in bases:
        for variant in variants:
            candidate_prefixes.append(f"{base}/{variant}/")
    
    # Find the most specific (longest) prefix that matches any path in tree_paths
    # Actually, we just need to return the first matching prefix that we find files for.
    # To be precise, if a directory exists, there will be files starting with it.
    
    matched_prefixes = []
    for path in tree_paths:
        for prefix in candidate_prefixes:
            if path.startswith(prefix):
                matched_prefixes.append(prefix)
                
    if not matched_prefixes:
        return None
        
    # Return the longest prefix (most specific) in case of multiple matches, though unlikely
    matched_prefixes = list(set(matched_prefixes))
    matched_prefixes.sort(key=len, reverse=True)
    return matched_prefixes[0]
