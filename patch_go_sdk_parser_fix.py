import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# Fix the regex issue
content = content.replace(
    r"""    for match in re.finditer(r'const\s+([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["'][^"']+["']|`[^`]+`)', code):""",
    r"""    for match in re.finditer(r'const\s+([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["\'][^"\']+["\']|`[^`]+`)', code):"""
)

content = content.replace(
    r"""        for line_match in re.finditer(r'([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["'][^"']+["']|`[^`]+`)', block):""",
    r"""        for line_match in re.finditer(r'([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["\'][^"\']+["\']|`[^`]+`)', block):"""
)

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)
