import unittest
from mcp_fingerprints.ast_parser import parse_python_mcp_ast

class TestPydanticAstParser(unittest.TestCase):
    def test_pydantic_unpacking(self):
        code = '''
from pydantic import BaseModel

class SearchArgs(BaseModel):
    query: str
    limit: int = 10
    filters: list[str] = []

@mcp.tool()
def search_items(args: SearchArgs):
    pass
'''
        tools = parse_python_mcp_ast(code)
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertIn("query", tool["property_keys"])
        self.assertIn("limit", tool["property_keys"])
        self.assertIn("filters", tool["property_keys"])
        self.assertNotIn("args", tool["property_keys"])
        
        self.assertIn("query", tool["required_keys"])
        self.assertNotIn("limit", tool["required_keys"])
        self.assertNotIn("filters", tool["required_keys"])

    def test_pydantic_unpacking_kwonlyargs(self):
        code = '''
from pydantic import BaseModel

class Pagination(BaseModel):
    page: int = 1
    size: int = 20

@mcp.tool()
def list_items(*, args: Pagination):
    pass
'''
        tools = parse_python_mcp_ast(code)
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertIn("page", tool["property_keys"])
        self.assertIn("size", tool["property_keys"])
        self.assertNotIn("args", tool["property_keys"])
        
        self.assertNotIn("page", tool["required_keys"])
        self.assertNotIn("size", tool["required_keys"])

    def test_class_method_self(self):
        code = '''
class MyService:
    @mcp.tool()
    def do_action(self, target: str):
        pass
'''
        tools = parse_python_mcp_ast(code)
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertNotIn("self", tool["property_keys"])
        self.assertIn("target", tool["property_keys"])
        self.assertIn("target", tool["required_keys"])

    def test_class_method_cls(self):
        code = '''
class MyService:
    @mcp.tool()
    @classmethod
    def do_action(cls, target: str):
        pass
'''
        tools = parse_python_mcp_ast(code)
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertNotIn("cls", tool["property_keys"])
        self.assertIn("target", tool["property_keys"])
        self.assertIn("target", tool["required_keys"])

if __name__ == "__main__":
    unittest.main()
