"""Unit tests for static AST code parsers (Python FastMCP & TypeScript SDKs)."""

from __future__ import annotations

import unittest

from mcp_fingerprints.ast_parser import (
    parse_mcp_source_code,
    parse_python_mcp_ast,
    parse_typescript_mcp_ast,
)


class TestAstParser(unittest.TestCase):
    """Test AST parsing for FastMCP Python decorated code and TypeScript SDK tool declarations."""

    def test_parse_python_fastmcp_decorators(self) -> None:
        py_code = '''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool()
def search_database(query: str, limit: int = 10) -> str:
    """Execute search query against database."""
    return f"results for {query}"

@mcp.tool(name="custom_calculator", description="Perform math evaluation")
async def calc(expr: str, *, precise: bool = True, num_runs: int) -> float:
    return 42.0
'''
        tools = parse_python_mcp_ast(py_code)
        self.assertEqual(len(tools), 2)

        # First tool
        t1 = tools[0]
        self.assertEqual(t1["name"], "search_database")
        self.assertEqual(t1["description"], "Execute search query against database.")
        self.assertIn("query", t1["property_keys"])
        self.assertIn("limit", t1["property_keys"])
        self.assertEqual(t1["required_keys"], ["query"])

        # Second tool
        t2 = tools[1]
        self.assertEqual(t2["name"], "custom_calculator")
        self.assertEqual(t2["description"], "Perform math evaluation")
        self.assertIn("num_runs", t2["required_keys"])

    def test_parse_python_invalid_syntax(self) -> None:
        bad_code = "def bad_func(:\n    pass"
        tools = parse_python_mcp_ast(bad_code)
        self.assertEqual(tools, [])

    def test_parse_typescript_mcp_sdk(self) -> None:
        ts_code = '''
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const server = new Server({ name: "ts-server", version: "1.0.0" });

server.tool(
  "create_user",
  "Create a new user account in database",
  {
    username: z.string(),
    age: z.number().optional(),
  },
  async ({ username, age }) => {
    return { id: "123" };
  }
);
'''
        tools = parse_typescript_mcp_ast(ts_code)
        self.assertGreaterEqual(len(tools), 1)
        t = tools[0]
        self.assertEqual(t["name"], "create_user")
        self.assertEqual(t["description"], "Create a new user account in database")
        self.assertIn("username", t["property_keys"])

    def test_parse_mcp_source_code_dispatcher(self) -> None:
        py_code = "@mcp.tool()\ndef echo(text: str):\n    '''Echo text'''\n    pass"
        tools = parse_mcp_source_code(py_code, language="python")
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "echo")

        # Unsupported language returns []
        unsupported = parse_mcp_source_code("fn main() {}", language="rust")
        self.assertEqual(unsupported, [])


if __name__ == "__main__":
    unittest.main()
