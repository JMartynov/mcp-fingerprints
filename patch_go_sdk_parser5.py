import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# Ah, `not isinstance(schema, dict)` is failing because `InputSchema` is not required to be present, or it defaults to empty. Wait! If `schema` is not provided, it will be `None`, which is not a `dict`!
# Let's see how PR #38 handled this. PR #38 had `or not isinstance(schema, dict)`.
# But wait, `test_ast_golang_official_sdk.py` code doesn't have `InputSchema` in the composite literal!
# `tests/test_ast_golang_official_sdk.py` has:
#         server.AddTool(&mcp.Tool{
#             Name: "example_tool",
#             Description: "A control tool",
#         }, handler)
# No `InputSchema`!
# The ast_parser logic handled this by defaulting `InputSchema` to empty object `{}`.
# I need to modify `parse_official_go_tools` to allow `schema = fields.get("InputSchema")` to be missing and default to `{"type": "object", "properties": {}, "required": []}` maybe? Or just `{}` and we fallback.

content = content.replace(
    """            schema = fields.get("InputSchema")
            description = fields.get("Description", "")
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(description, str)
                or not isinstance(schema, dict)
            ):""",
    """            schema = fields.get("InputSchema", {"type": "object", "properties": {}, "required": []})
            description = fields.get("Description", name)
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(description, str)
                or not isinstance(schema, dict)
            ):"""
)

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)

