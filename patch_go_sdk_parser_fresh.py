import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# 1. Update _Literal init to accept constants
content = content.replace(
    "def __init__(self, tokens: list[str], pos: int = 0) -> None:",
    "def __init__(self, tokens: list[str], pos: int = 0, constants: dict[str, str] | None = None) -> None:\n        self.constants = constants or {}"
)

# 2. Update _Literal value to resolve constants
value_method_orig = """    def value(self, depth: int = 0) -> Any:
        if depth > 32:
            raise ValueError("literal nesting limit")
        token = self.take()
        if token.startswith(('"', "`")):
            return _string(token)
        if token in ("true", "false", "nil"):
            return {"true": True, "false": False, "nil": None}[token]"""

value_method_new = """    def value(self, depth: int = 0) -> Any:
        if depth > 32:
            raise ValueError("literal nesting limit")
        token = self.take()
        if token.startswith(('"', "`")):
            return _string(token)
        if token in self.constants:
            val = self.constants[token]
            if val.startswith(('"', "`")):
                return _string(val)
        if token in ("true", "false", "nil"):
            return {"true": True, "false": False, "nil": None}[token]"""

content = content.replace(value_method_orig, value_method_new)

# 3. Update parse_official_go_tools to extract constants and pass to _Literal
parse_func_orig = """def parse_official_go_tools(code: str) -> list[dict[str, Any]]:
    \"\"\"Extract complete inline Server.AddTool literals; skip unresolved contracts.

    Import aliases are respected. Helpers, constants, inferred schemas and
    variable-based registrations need Go type/data-flow analysis and are omitted.
    \"\"\"
    if "github.com/modelcontextprotocol/go-sdk/mcp" not in code:
        return []
    tokens = [t for t in _TOKEN.findall(code) if not t.startswith(("//", "/*"))]"""

parse_func_new = r"""def parse_official_go_tools(code: str) -> list[dict[str, Any]]:
    \"\"\"Extract complete inline Server.AddTool literals; skip unresolved contracts.

    Import aliases are respected. Helpers, constants, inferred schemas and
    variable-based registrations need Go type/data-flow analysis and are omitted.
    \"\"\"
    if "github.com/modelcontextprotocol/go-sdk/mcp" not in code and "package main" not in code and "mcp.Tool" not in code:
        return []
        
    constants: dict[str, str] = {}
    for match in re.finditer(r'const\s+([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["\'][^"\']+["\']|`[^`]+`)', code):
        constants[match.group(1)] = match.group(2)
        
    for match in re.finditer(r'const\s*\(\s*(.*?)\s*\)', code, re.DOTALL):
        block = match.group(1)
        for line_match in re.finditer(r'([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["\'][^"\']+["\']|`[^`]+`)', block):
            constants[line_match.group(1)] = line_match.group(2)
            
    tokens = [t for t in _TOKEN.findall(code) if not t.startswith(("//", "/*"))]"""

content = content.replace(parse_func_orig, parse_func_new)


init_literal_orig = """        literal = _Literal(tokens, i + 8)"""
init_literal_new = """        literal = _Literal(tokens, i + 8, constants=constants)"""
content = content.replace(init_literal_orig, init_literal_new)

# In order to allow missing import aliases but preserve original behavior:
aliases_orig = """    aliases = set()
    for i, token in enumerate(tokens):
        if token != "import":"""
aliases_new = """    aliases = {"mcp"} # fallback
    for i, token in enumerate(tokens):
        if token != "import":"""
content = content.replace(aliases_orig, aliases_new)

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)
