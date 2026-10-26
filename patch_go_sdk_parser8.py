import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# Fix 1: description fallback should only fallback to `""` if not missing. But in `test_omitted_description_matches_explicit_empty_description_metadata`, omitted description matches explicit empty.
# If `Description` is omitted, it should be empty `""`, not fallback to `name`.
# Wait, `test_ast_golang_official_sdk.py` has a test `test_block_constants` where:
# `t2 := mcp.Tool{ Name: ToolName2, }`
# "Description fallback to Title or Name. If Title missing, should fall back to Name."
# Ah! In PR #38, `Description` is strictly `""` if omitted. In `ast_parser.py`, it was:
# if not desc or len(desc) < 3: desc = title if title else name
# So the old test in Task 83 required `Description` to fallback to Name if omitted!
# Let's restore that in `go_sdk_parser.py`:
# schema = fields.get("InputSchema", {"type": "object", "properties": {}, "required": []})
# description = fields.get("Description")
# if not description or len(description) < 3:
#    title = fields.get("Title")
#    description = title if title else name
# Let's use exactly that.

# Wait, `test_omitted_description_matches_explicit_empty_description_metadata` requires `""` to match `""`. If we fallback to name, they won't match, right?
# If `description` is omitted, it becomes `""`. But in PR #38 test, `""` is expected!
# "omitted_description_matches_explicit_empty_description_metadata"
# If we change it, PR #38 test will fail, but Task 83 test will pass. We need both.
# But wait, PR #38 test expects `extract_tool_signature` to output `""` and it expects `explicit_signature.description == ""`.
# How can we satisfy both?
# Maybe we only fallback to Name if we are in `parse_golang_mcp_code`? No, let's keep it in `go_sdk_parser`.
# If it's a test for PR 38, maybe I should just update PR 38 test to expect the fallback?
# Actually, Task 83's `test_block_constants` explicitly says:
# "# Description fallback to Title or Name. If Title missing, should fall back to Name."
# And PR 38 test says:
# "assert omitted_signature.description == explicit_signature.description == ''"

# Fix 2: `test_unrelated_or_truncated_declarations_are_not_tools` fails because we relaxed `parse_official_go_tools` loop to `alias . Tool {` anywhere! So it parses tools from `otherMethod(&mcp.Tool{...})`.
# PR #38 specifically wanted to restrict it to `Server.AddTool(&mcp.Tool{...})` via `tokens[i : i + 4] == [".", "AddTool", "(", "&"]`.
# But `test_block_constants` does: `t1 := mcp.Tool{...}; server.AddTool(&t1, h)`
# How do we match BOTH?
# Maybe `test_ast_golang_official_sdk.py` was relying on the ast_parser's old regex which found `mcp.Tool{...}` ANYWHERE! Yes, the old regex was: `(?:server\.AddTool\s*\(\s*&?|&?)mcp\.Tool\s*\{([^\}]+)\}`
# It matched `&mcp.Tool{` or `server.AddTool(&mcp.Tool{`.
# So to pass BOTH, we should allow `mcp.Tool{` anywhere, but why did PR #38 restrict it? PR #38 restricted it to `AddTool` only.
# Let's adjust the regex/check to allow it but in `test_unrelated_or_truncated_declarations_are_not_tools` the test specifically checks that it ignores un-related tools!
# "source().replace("server.AddTool(", "otherMethod(")"
# If it's passed to `otherMethod`, PR 38 wants it ignored!

