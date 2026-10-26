import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# Let's revert the loop logic back to PR #38's to pass its strict checks.
# Wait, if we revert, how does `test_block_constants` pass?
# `test_block_constants` does `t1 := mcp.Tool{...}`.
# PR #38 does not support parsing `mcp.Tool{...}` out of context.
# BUT wait! Task 84 instructions: "In src/mcp_fingerprints/ast_parser.py: call parse_official_go_tools in parse_golang_mcp_code and deduplicate."
# And "Ensure deduplication with existing builder definitions (mcp.NewTool) and composite literals."
# Ah!!!! `parse_golang_mcp_code` should keep its old composite literal regex for `t1 := mcp.Tool`, AND call `parse_official_go_tools` to get PR 38's results, and deduplicate!
# I completely removed the old regex from `ast_parser.py`! That was a mistake!

