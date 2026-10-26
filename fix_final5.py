with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

content = content.replace("aliases = set() for tests that omit import", "aliases = set() # fallback")
with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)

