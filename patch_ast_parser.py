import re

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

# Replace the block that matches Official SDK Composite Literals
start_marker = "    # 2. Match Official SDK Composite Literals (mcp.Tool{...})"
end_marker = r"    for match in re.finditer(r'mcp\.(?:NewTool|NewToolWithRawSchema)\s*\(\s*[\"']([^\"']+)[\"']', code):"

start_idx = content.find(start_marker)
end_idx = content.find("    for match in re.finditer(r'mcp\.(?:NewTool|NewToolWithRawSchema)")

if start_idx != -1 and end_idx != -1:
    old_block = content[start_idx:end_idx]
    new_block = """    # 2. Extract Official SDK Composite Literals using go_sdk_parser
    from mcp_fingerprints.go_sdk_parser import parse_official_go_tools
    
    official_tools = parse_official_go_tools(code)
    for t in official_tools:
        name = t.get("name")
        if name and name not in seen_names:
            seen_names.add(name)
            extracted.append(t)

"""
    content = content[:start_idx] + new_block + content[end_idx:]
    
with open("src/mcp_fingerprints/ast_parser.py", "w") as f:
    f.write(content)

