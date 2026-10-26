import re

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

content = content.replace(
    r"""name_match = re.search(r'Name\s*:\s*(?:["']([^"']+)["']|([a-zA-Z0-9_]+))', body)""",
    r"""name_match = re.search(r'Name\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)"""
)
content = content.replace(
    r"""desc_match = re.search(r'Description\s*:\s*(?:["']([^"']+)["']|([a-zA-Z0-9_]+))', body)""",
    r"""desc_match = re.search(r'Description\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)"""
)
content = content.replace(
    r"""title_match = re.search(r'Title\s*:\s*(?:["']([^"']+)["']|([a-zA-Z0-9_]+))', body)""",
    r"""title_match = re.search(r'Title\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)"""
)

with open("src/mcp_fingerprints/ast_parser.py", "w") as f:
    f.write(content)
