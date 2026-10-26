import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# PR #38 looks for `[".", "AddTool", "(", "&"]` followed by `alias`, `[".", "Tool", "{"]`
# But in `test_block_constants`, the code uses `t1 := mcp.Tool{ ... }` and `server.AddTool(&t1, h)`
# Oh! The old code in ast_parser matched: `(?:server\.AddTool\s*\(\s*&?|&?)mcp\.Tool\s*\{([^\}]+)\}`
# Which means it found `mcp.Tool{` ANYWHERE!
# PR #38 explicitly looks for the exact sequence `. AddTool ( & mcp . Tool {`.
# That misses standalone `mcp.Tool{` initialization.
# Let's fix PR #38's parser to look for `alias . Tool {` instead!
# Or maybe `& mcp . Tool {` or just `mcp . Tool {`.
# The AST parser logic is a bit rigid in PR #38. We need it to match `alias`, `.`, `Tool`, `{` and just parse the literal there!

# To do that without breaking PR 38, we can change the for loop:
# for i in range(len(tokens) - 4):
#   if tokens[i] in aliases and tokens[i+1:i+4] == [".", "Tool", "{"]:
#       literal = _Literal(tokens, i + 4, constants=constants)
# Let's check PR #38's intention. The function says "Extract complete inline Server.AddTool literals". So maybe it intentionally restricted it?
# But if we replace ast_parser's regex with it, we must match `mcp.Tool{` standalone to pass `test_ast_golang_official_sdk.py`.
