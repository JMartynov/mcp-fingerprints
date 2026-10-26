with open("src/mcp_fingerprints/go_sdk_parser.py", "r") as f:
    content = f.read()

content = content.replace(
    """            name = fields.get("Name")
            schema = fields.get("InputSchema")
            description = fields.get("Description", "")
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(description, str)
                or not isinstance(schema, dict)
            ):""",
    """            name = fields.get("Name")
            schema = fields.get("InputSchema", {"type": "object", "properties": {}, "required": []})
            description = fields.get("Description", "")
            if not description or len(description) < 3:
                title = fields.get("Title")
                description = title if title else name
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(description, str)
                or not isinstance(schema, dict)
            ):"""
)

with open("src/mcp_fingerprints/go_sdk_parser.py", "w") as f:
    f.write(content)

