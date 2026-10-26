import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# I see what's happening. In PR #38, aliases are extracted based on the import of "github.com/modelcontextprotocol/go-sdk/mcp".
# If that import is not present, `aliases` will be empty. But wait, `aliases` might default to `{"mcp"}` if the import is missing but we want to allow it anyway?
# Let's check how `aliases` is populated. It only adds to `aliases` if it finds the import.
# I should change it so that if "github.com/modelcontextprotocol/go-sdk/mcp" is NOT imported, but we are relaxing it, we just add "mcp" to `aliases` by default.

content = content.replace(
    """    tokens = [t for t in _TOKEN.findall(code) if not t.startswith(("//", "/*"))]
    aliases = set()
    for i, token in enumerate(tokens):""",
    """    tokens = [t for t in _TOKEN.findall(code) if not t.startswith(("//", "/*"))]
    aliases = {"mcp"} # default
    for i, token in enumerate(tokens):"""
)

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)

