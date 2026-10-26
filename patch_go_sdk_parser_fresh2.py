import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

content = content.replace(r'    \"\"\"Extract complete inline Server.AddTool literals; skip unresolved contracts.', '    """Extract complete inline Server.AddTool literals; skip unresolved contracts.')
content = content.replace(r'    \"\"\"', '    """')

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)
