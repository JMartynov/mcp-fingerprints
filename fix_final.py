import re

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

# For `test_ast_golang_official_sdk.py`, the code uses `server.AddTool(&mcp.Tool{ Name: ..., Description: ... })`.
# Wait, why didn't `parse_official_go_tools` extract them?
# Because `test_inline_string_literal` doesn't have the import `"github.com/modelcontextprotocol/go-sdk/mcp"`!
# And I modified `go_sdk_parser.py` to only allow it if `"mcp.Tool"` is in code AND `package main` is in code AND import is not there.
# Oh! Wait, `go_sdk_parser.py` says:
# if "github.com/modelcontextprotocol/go-sdk/mcp" not in code and "package main" not in code and "mcp.Tool" not in code:
#     return []
# But `test_inline_string_literal` HAS `"package main"` and `"mcp.Tool"`. So it SHOULD not return `[]`.
# So why did it fail to extract?
# Because it says: `Unresolved official Go SDK tool literal; extraction does not establish an empty toolset`
# Why unresolved? Because `InputSchema` is MISSING!
# And in `go_sdk_parser.py`:
# schema = fields.get("InputSchema")
# if schema is not dict, it raises ValueError!
# `fields.get("InputSchema")` returns `None`!
# Let's fix `go_sdk_parser.py` so `schema` defaults to `{"type": "object", "properties": {}, "required": []}` in `go_sdk_parser.py` ONLY when not present!

