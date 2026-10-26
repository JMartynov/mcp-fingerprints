import re

with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

# Let's change the loop to look for `alias . Tool {` anywhere!
new_loop = """    for i in range(len(tokens) - 4):
        alias = tokens[i]
        if alias not in aliases or tokens[i + 1 : i + 4] != [".", "Tool", "{"]:
            continue
        literal = _Literal(tokens, i + 4, constants=constants)
        fields = {}
        try:
            while literal.tokens[literal.pos : literal.pos + 1] != ["}"]:
                field = literal.take()
                literal.take(":")
                if field in ("Name", "Description", "InputSchema"):
                    fields[field] = literal.value()
                else:
                    literal.skip_value()
                if literal.tokens[literal.pos : literal.pos + 1] != ["}"]:
                    literal.take(",")
            literal.take("}")
            # we might not have a trailing comma or ")" immediately here because we aren't in AddTool
            name = fields.get("Name")
            schema = fields.get("InputSchema", {"type": "object", "properties": {}, "required": []})
            description = fields.get("Description", name)
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(description, str)
                or not isinstance(schema, dict)
            ):
                raise ValueError("unresolved name, description or input schema")
        except (ValueError, UnicodeError, OverflowError):
            logger.warning(
                "Unresolved official Go SDK tool literal; extraction does not establish an empty toolset"
            )
            continue
        tools.append({"name": name, "description": description, "inputSchema": schema})
    return tools"""

old_loop_start = "    for i in range(len(tokens) - 8):"
old_loop_end = "    return tools"

start_idx = content.find(old_loop_start)
end_idx = content.find(old_loop_end) + len(old_loop_end)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_loop + content[end_idx:]

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)

