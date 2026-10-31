with open("tests/test_reindex_sdk_passports.py", "r") as f:
    content = f.read()

# Make sure we don't accidentally fail on empty tool returns
content = content.replace('''
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        @mcp.tool()
        def python_tool() -> str:
            """A python test tool"""
            return "test"
''', '''
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        
        @mcp.tool()
        def python_tool() -> str:
            """A python test tool"""
            return "test"
''')

with open("tests/test_reindex_sdk_passports.py", "w") as f:
    f.write(content)
