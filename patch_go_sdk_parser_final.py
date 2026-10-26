import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# Make the loop more robust. We want to find `.Tool{` where the token before `.` is an alias.
# BUT wait, the PR 38 tests expect un-related definitions to be IGNORED.
# If they expect them to be ignored, they only want tools passed to `server.AddTool`.
# Oh! The PR 38 explicitly tests that `server.AddTool(&mcp.Tool{...})` works and `otherMethod(&mcp.Tool{...})` does NOT!
# BUT `test_ast_golang_official_sdk.py` expects `t1 := mcp.Tool{...}; server.AddTool(&t1, h)` to work!
# BUT wait! Task 84 says: "In src/mcp_fingerprints/ast_parser.py: call parse_official_go_tools in parse_golang_mcp_code and deduplicate. Ensure deduplication with existing builder definitions (mcp.NewTool) and composite literals."
# This means BOTH the PR 38 parser and the existing ast_parser regex should coexist!
# But since PR 38 parser is better at parsing schemas, if BOTH find a tool with the same name, we should prefer the output from PR 38 parser (which has the correct schema) instead of the regex one!

