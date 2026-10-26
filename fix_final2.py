import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# 1. Revert `description` fallback. We MUST NOT fallback to `name` if omitted in `go_sdk_parser`, because the PR 38 tests explicitly require it to be `""`!
# BUT wait! If we don't fallback to `name`, `test_block_constants` will fail because it expects fallback to `name`!
# Actually, `test_block_constants` is in `test_ast_golang_official_sdk.py` which was relying on `ast_parser.py`!
# But `ast_parser.py` now uses `go_sdk_parser.py`.
# Does `ast_parser.py` STILL fallback if we do it in `ast_parser.py`? No, because it just takes `t` from `official_tools`.
# Let's fix `go_sdk_parser.py` to NOT fallback to `name` (to pass PR 38 tests), and instead update `ast_parser.py` to fallback to `name` if `t["description"]` is `""`.

content = content.replace(
    """            description = fields.get("Description", "")
            if not description or len(description) < 3:
                title = fields.get("Title")
                description = title if title else name
            if (""",
    """            description = fields.get("Description", "")
            if ("""
)

# 2. Fix the unrelated declarations in `go_sdk_parser.py`.
# Why did it parse them? Because I changed the `tokens[i : i + 4] != [".", "AddTool", "(", "&"]` to `alias = tokens[i]` etc.
# But wait, I reverted it!
# If I reverted it, why does it still match `import "example.com/other/mcp"`?
# Ah! Because I changed the `import` check to relax it:
# if "github.com/modelcontextprotocol/go-sdk/mcp" not in code and "package main" not in code and "mcp.Tool" not in code: return []
# So if `"package main"` is in code, it continues!
# And it finds `server.AddTool(&mcp.Tool{...})`.
# Yes, `test_unrelated_or_truncated_declarations_are_not_tools` replaces the import with `example.com`, but leaves `package main`. So it passes the relaxed check!
# Then it finds `server.AddTool(&mcp.Tool{...})` and parses it!
# So PR #38 expected it to return `[]` because it doesn't have the correct import!
# If we require the import, `test_ast_golang_official_sdk.py` will fail because those code snippets don't have the import!
# Let's just fix the test snippet in `test_ast_golang_official_sdk.py` to include the import, and restore the strict check in `go_sdk_parser.py`!

content = content.replace(
    """    if "github.com/modelcontextprotocol/go-sdk/mcp" not in code and "package main" not in code and "mcp.Tool" not in code:
        return []""",
    """    if "github.com/modelcontextprotocol/go-sdk/mcp" not in code:
        return []"""
)

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)

