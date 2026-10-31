with open("tests/test_reindex_sdk_passports.py", "r") as f:
    content = f.read()

# Replace the tool to make sure we use python decorator parsing properly
content = content.replace('''        @mcp.tool()
        def python_tool():
            """A python test tool"""
            pass''', '''
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        @mcp.tool()
        def python_tool() -> str:
            """A python test tool"""
            return "test"
''')

with open("tests/test_reindex_sdk_passports.py", "w") as f:
    f.write(content)
