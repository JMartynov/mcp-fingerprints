import re

with open("src/mcp_fingerprints/reindex_sdk_passports.py", "r") as f:
    content = f.read()

# Fix import
content = content.replace(
    "from src.mcp_fingerprints.ast_parser import parse_mcp_source_code",
    "from src.mcp_fingerprints.ast_parser import parse_mcp_source_code\nfrom src.mcp_fingerprints.doc_parser import parse_markdown_tool_docs"
)

# Update fetch_github_tree
old_fetch_tree = """    # We want TS, JS, and Python files typically.
    extensions = (".ts", ".js", ".mjs", ".py")
    return [x["path"] for x in data.get("tree", []) 
            if x.get("type") == "blob" and x["path"].endswith(extensions) and not x["path"].endswith(("_test.py", ".test.ts", ".spec.ts"))]"""

new_fetch_tree = """    # We want TS, JS, Python, Go files and Markdown for docs fallback typically.
    extensions = (".ts", ".js", ".mjs", ".py", ".go", ".md")
    return [x["path"] for x in data.get("tree", []) 
            if x.get("type") == "blob" and x["path"].lower().endswith(extensions) and not x["path"].endswith(("_test.py", ".test.ts", ".spec.ts"))]"""

content = content.replace(old_fetch_tree, new_fetch_tree)

# Update priority
old_priority = """        if "index" in low or "main" in low:
            return 3
        return 4"""
new_priority = """        if "index" in low or "main" in low:
            return 3
        if "readme" in low:
            return 4
        return 5"""

content = content.replace(old_priority, new_priority)

# Update extraction
old_extract = """        # Determine language for parser
        ext = fpath.split(".")[-1].lower()
        if ext in ("py",):
            lang = "python"
        elif ext in ("ts", "js", "mjs"):
            lang = "typescript"
        else:
            lang = None

        extracted = parse_mcp_source_code(code, language=lang)
        for t in extracted:
            tname = t.get("name")
            if tname and tname not in seen_names:
                seen_names.add(tname)
                aggregated_tools.append(t)"""

new_extract = """        # Determine language for parser
        ext = fpath.split(".")[-1].lower()
        
        if ext == "md":
            extracted = parse_markdown_tool_docs(code)
        else:
            if ext in ("py",):
                lang = "python"
            elif ext in ("ts", "js", "mjs"):
                lang = "typescript"
            elif ext in ("go",):
                lang = "go"
            else:
                lang = None

            extracted = parse_mcp_source_code(code, language=lang)
            
        for t in extracted:
            tname = t.get("name")
            if tname and tname not in seen_names:
                seen_names.add(tname)
                aggregated_tools.append(t)"""

content = content.replace(old_extract, new_extract)

with open("src/mcp_fingerprints/reindex_sdk_passports.py", "w") as f:
    f.write(content)
