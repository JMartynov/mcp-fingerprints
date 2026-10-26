import re

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

# Why is `test_unrelated_or_truncated_declarations_are_not_tools` failing?
# Because `parse_golang_mcp_code` matches `mcp.Tool{...}` everywhere as a fallback!
# Oh, the ast_parser regex is:
# tool_pattern = re.compile(
#     r'(?:server\.AddTool\s*\(\s*&?|&?)mcp\.Tool\s*\{([^\}]+)\}',
#     re.DOTALL
# )
# And this matches `otherMethod(&mcp.Tool{...})` because it has `&mcp.Tool{` in it!
# PR #38 added stricter checks, but we are running BOTH.
# How about we ONLY run the ast_parser regex if `parse_official_go_tools` returns NOTHING?
# Or better, we just change the ast_parser regex to NOT match `otherMethod(&mcp.Tool{...})` but only `var x = mcp.Tool{...}` or `t1 := mcp.Tool{...}` or `server.AddTool(&mcp.Tool{...})`?
# Wait! In `parse_golang_mcp_code`:
# if `go_sdk_parser` parses a tool, it is added. If not, it falls back to regex.
# The regex parses `otherMethod(&mcp.Tool{...})` because of `|&?mcp\.Tool`.
# We should just let `go_sdk_parser` do the work, and remove `|&?mcp\.Tool`? No, because `t1 := mcp.Tool{` needs to be matched.
# What if we change `ast_parser` regex to:
# r'(?:server\.AddTool\s*\(\s*&?|(?:=|:=)\s*&?)mcp\.Tool\s*\{([^\}]+)\}'
# Let's try that!

new_regex = r"r'(?:server\.AddTool\s*\(\s*&?|(?:=|:=)\s*&?)mcp\.Tool\s*\{([^\}]+)\}'"
content = content.replace(r"r'(?:server\.AddTool\s*\(\s*&?|&?)mcp\.Tool\s*\{([^\}]+)\}'", new_regex)

with open("src/mcp_fingerprints/ast_parser.py", "w") as f:
    f.write(content)

