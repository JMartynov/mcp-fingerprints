import re

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

# Let's fix deduplication in ast_parser.py!
# We should run go_sdk_parser first, and THEN run the fallback regex, only adding tools if their names aren't already found!

start_marker = "    # 2. Match Official SDK Composite Literals (mcp.Tool{...}) - legacy for var assignments"
end_marker = r"    for match in re.finditer(r'mcp\.(?:NewTool|NewToolWithRawSchema)\s*\(\s*[\"']([^\"']+)[\"']', code):"

start_idx = content.find(start_marker)
end_idx = content.find("    for match in re.finditer(r'mcp\.(?:NewTool|NewToolWithRawSchema)")

if start_idx != -1 and end_idx != -1:
    new_block = """    # 2a. Extract Official SDK Literals (Go SDK parser)
    from mcp_fingerprints.go_sdk_parser import parse_official_go_tools
    official_tools = parse_official_go_tools(code)
    for t in official_tools:
        if t["name"] not in seen_names:
            seen_names.add(t["name"])
            extracted.append(t)

    # 2b. Match Official SDK Composite Literals (mcp.Tool{...}) - legacy for var assignments
    tool_pattern = re.compile(
        r'(?:server\.AddTool\s*\(\s*&?|&?)mcp\.Tool\s*\{([^\}]+)\}',
        re.DOTALL
    )
    for match in tool_pattern.finditer(code):
        body = match.group(1)
        
        name_match = re.search(r'Name\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)
        name = None
        if name_match:
            name = name_match.group(1) if name_match.group(1) else constants.get(name_match.group(2), name_match.group(2))
            
        if not name:
            continue
            
        if name in seen_names:
            continue
            
        desc_match = re.search(r'Description\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)
        desc = None
        if desc_match:
            desc = desc_match.group(1) if desc_match.group(1) else constants.get(desc_match.group(2), desc_match.group(2))
            
        title_match = re.search(r'Title\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)
        title = None
        if title_match:
            title = title_match.group(1) if title_match.group(1) else constants.get(title_match.group(2), title_match.group(2))
            
        if not desc or len(desc) < 3:
            desc = title if title else name
            
        seen_names.add(name)
        extracted.append({
            "name": name,
            "description": desc,
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        })
        
"""
    content = content[:start_idx] + new_block + content[end_idx:]

with open("src/mcp_fingerprints/ast_parser.py", "w") as f:
    f.write(content)

