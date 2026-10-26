import re

with open("tests/test_ast_golang_official_sdk.py", "r") as f:
    content = f.read()

content = content.replace("package main\n", "package main\nimport \"github.com/modelcontextprotocol/go-sdk/mcp\"\n")
content = content.replace("package main\n    const", "package main\n    import \"github.com/modelcontextprotocol/go-sdk/mcp\"\n    const")
content = content.replace("package main\n    func init() {", "package main\n    import \"github.com/modelcontextprotocol/go-sdk/mcp\"\n    func init() {")

with open("tests/test_ast_golang_official_sdk.py", "w") as f:
    f.write(content)

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

# Fallback description to name if it's ""
content = content.replace(
    """    for t in official_tools:
        if t["name"] not in seen_names:
            seen_names.add(t["name"])
            extracted.append(t)""",
    """    for t in official_tools:
        if t["name"] not in seen_names:
            if not t.get("description") or len(t.get("description", "")) < 3:
                t["description"] = t["name"]
            seen_names.add(t["name"])
            extracted.append(t)"""
)
with open("src/mcp_fingerprints/ast_parser.py", "w") as f:
    f.write(content)

