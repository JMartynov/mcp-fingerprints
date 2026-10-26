import re

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

# I see the problem. The ast_parser regex fallback STILL matches the same tools because `seen_names` deduplication expects `name` to be exact.
# BUT wait! If `go_sdk_parser` FAILS (e.g. unresolved schema), it returns `[]` (nothing), so the `ast_parser` fallback regex parses it and adds it with an empty schema `{}`!
# THAT'S why the test "unresolved schema does not become empty schema" fails!
# It is successfully ignored by `go_sdk_parser`, but then picked up by the fallback regex!
# Same for "unrelated or truncated declarations"!
# `otherMethod(&mcp.Tool{...})` is ignored by `go_sdk_parser`, but picked up by fallback regex!
# So we CANNOT have the fallback regex match `mcp.Tool{` everywhere!
# We should just restrict the fallback regex to `t1 := mcp.Tool{` or ONLY `mcp.NewTool`!
# The `test_ast_golang_official_sdk.py` ONLY uses `t1 := mcp.Tool{` and `t2 := mcp.Tool{` for the var assignment!
# Let's restrict the fallback regex to `(?:[a-zA-Z0-9_]+\s*(?:=|:=)\s*&?)mcp\.Tool\s*\{([^\}]+)\}`.
# Wait, if we do that, we miss `server.AddTool(&mcp.Tool{})` entirely if `go_sdk_parser` fails to parse it?
# Yes, because PR #38 specifically says: "Unresolved official Go SDK tool literal; extraction does not establish an empty toolset"! It explicitly wants it to NOT be added.
# So we MUST restrict the fallback regex so it doesn't bypass PR 38's strict rules!
# Let's change the fallback regex to match ONLY var assignment:
new_regex = r"r'(?:[a-zA-Z0-9_]+\s*(?:=|:=)\s*&?)mcp\.Tool\s*\{([^\}]+)\}'"
content = content.replace(r"r'(?:server\.AddTool\s*\(\s*&?|(?:=|:=)\s*&?)mcp\.Tool\s*\{([^\}]+)\}'", new_regex)

with open("src/mcp_fingerprints/ast_parser.py", "w") as f:
    f.write(content)

