"""Real-life MCP test suite and parser ground truth."""

import unittest
from mcp_fingerprints.ast_parser import parse_typescript_mcp_ast, parse_python_mcp_ast

class TestAstRealLifeExamples(unittest.TestCase):

    def test_anthropic_ts_sdk_set_request_handler(self):
        # Official Anthropic TS SDK pattern
        ts_code = """
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server({ name: "my-server", version: "1.0.0" });

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "read_file",
        description: "Reads the content of a file",
        inputSchema: {
          type: "object",
          properties: {
            filepath: {
              type: "string",
              description: "The path to the file"
            }
          },
          required: ["filepath"]
        }
      },
      {
        name: "write_file",
        description: "Writes content to a file",
        inputSchema: {
          type: "object",
          properties: {
            filepath: {
              type: "string",
              description: "The path to the file"
            },
            content: {
              type: "string",
              description: "The content to write"
            }
          },
          required: ["filepath", "content"]
        }
      }
    ]
  };
});
"""
        tools = parse_typescript_mcp_ast(ts_code)
        
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["name"], "read_file")
        self.assertEqual(tools[0]["description"], "Reads the content of a file")
        self.assertEqual(tools[0]["property_keys"], ["filepath"])
        self.assertEqual(tools[0]["required_keys"], ["filepath"])
        
        self.assertEqual(tools[1]["name"], "write_file")
        self.assertEqual(tools[1]["description"], "Writes content to a file")
        self.assertEqual(tools[1]["property_keys"], ["content", "filepath"])
        self.assertEqual(tools[1]["required_keys"], ["content", "filepath"])

    def test_modular_export_arrays(self):
        ts_code = """
export const tools = [
  {
    name: "calculator",
    description: "Evaluates a math expression",
    inputSchema: {
      type: "object",
      properties: {
        expression: { type: "string" }
      },
      required: ["expression"]
    }
  },
  {
    name: "fetch_weather",
    description: "Fetches current weather",
    inputSchema: {
      type: "object",
      properties: {
        location: { type: "string" }
      },
      required: ["location"]
    }
  }
];
"""
        tools = parse_typescript_mcp_ast(ts_code)
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["name"], "calculator")
        self.assertEqual(tools[0]["description"], "Evaluates a math expression")
        self.assertEqual(tools[0]["property_keys"], ["expression"])
        self.assertEqual(tools[0]["required_keys"], ["expression"])
        
        self.assertEqual(tools[1]["name"], "fetch_weather")
        self.assertEqual(tools[1]["description"], "Fetches current weather")
        self.assertEqual(tools[1]["property_keys"], ["location"])
        self.assertEqual(tools[1]["required_keys"], ["location"])

    def test_server_method_registration(self):
        ts_code = """
server.registerTool(
  "create_repo",
  {
    title: "Create Repository",
    description: "Creates a new GitHub repository",
    inputSchema: {
      repo_name: z.string(),
      private: z.boolean().optional()
    }
  },
  async ({ repo_name, private }) => {}
);
"""
        tools = parse_typescript_mcp_ast(ts_code)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "create_repo")
        self.assertEqual(tools[0]["description"], "Creates a new GitHub repository")
        self.assertIn("repo_name", tools[0]["property_keys"])
        self.assertIn("private", tools[0]["property_keys"])
        self.assertEqual(tools[0]["required_keys"], ["repo_name"])

    def test_fastmcp_python_decorator(self):
        py_code = '''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool()
def format_code(code: str, indent: int = 4) -> str:
    """Format python code according to PEP8."""
    return code
'''
        tools = parse_python_mcp_ast(py_code)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "format_code")
        self.assertEqual(tools[0]["description"], "Format python code according to PEP8.")
        self.assertIn("code", tools[0]["property_keys"])
        self.assertIn("indent", tools[0]["property_keys"])
        self.assertEqual(tools[0]["required_keys"], ["code"])

    def test_named_fastmcp_decorator(self):
        py_code = '''
from mcp.server.fastmcp import FastMCP

server = FastMCP("demo")

@server.tool(name="execute_sql", description="Run a SQL query against the database")
def run_query(query: str, readonly: bool = True) -> list:
    return []
'''
        tools = parse_python_mcp_ast(py_code)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "execute_sql")
        self.assertEqual(tools[0]["description"], "Run a SQL query against the database")
        self.assertIn("query", tools[0]["property_keys"])
        self.assertIn("readonly", tools[0]["property_keys"])
        self.assertEqual(tools[0]["required_keys"], ["query"])

    def test_low_level_python_sdk(self):
        py_code = '''
from mcp.types import Tool

@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="get_weather",
            description="Get the current weather",
            inputSchema={
                "type": "object", 
                "properties": {"location": {"type": "string"}}, 
                "required": ["location"]
            }
        ),
        types.Tool(
            name="get_time",
            description="Get current time",
            inputSchema={
                "type": "object", 
                "properties": {"timezone": {"type": "string"}}, 
                "required": ["timezone"]
            }
        )
    ]
'''
        tools = parse_python_mcp_ast(py_code)
        self.assertEqual(len(tools), 2)
        
        self.assertEqual(tools[0]["name"], "get_weather")
        self.assertEqual(tools[0]["description"], "Get the current weather")
        self.assertIn("location", tools[0]["property_keys"])
        self.assertEqual(tools[0]["required_keys"], ["location"])

        self.assertEqual(tools[1]["name"], "get_time")
        self.assertEqual(tools[1]["description"], "Get current time")
        self.assertIn("timezone", tools[1]["property_keys"])
        self.assertEqual(tools[1]["required_keys"], ["timezone"])

    def test_false_positive_resistance(self):
        # A server configuration shouldn't be extracted as a tool
        ts_code = """
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const server = new Server({ name: "my-service", version: "1.0.0" }, { capabilities: { tools: {} } });
"""
        tools = parse_typescript_mcp_ast(ts_code)
        # Ensure 'my-service' isn't extracted
        self.assertEqual(len(tools), 0)

if __name__ == "__main__":
    unittest.main()
