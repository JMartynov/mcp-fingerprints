import pytest
from mcp_fingerprints.ast_parser import parse_typescript_mcp_ast


def test_typescript_backtick_description():
    code = """
    export const tools = [
      {
        name: "search_repositories",
        description: `Search across all GitHub repositories,
including private and archived ones.`,
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string" },
            limit: { type: "number" }
          },
          required: ["query"]
        }
      }
    ];
    """
    tools = parse_typescript_mcp_ast(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "search_repositories"
    assert "Search across all GitHub repositories" in tools[0]["description"]
    assert "query" in tools[0]["inputSchema"]["properties"]
    assert tools[0]["inputSchema"]["required"] == ["query"]


def test_typescript_description_with_commas():
    code = """
    server.tool(
      "format_code",
      "Format code, organize imports, and remove unused variables",
      {
        file_path: z.string().describe("Path to target file"),
        dry_run: z.boolean().optional()
      },
      async (args) => { return {}; }
    );
    """
    tools = parse_typescript_mcp_ast(code)
    assert len(tools) == 1
    assert tools[0]["name"] == "format_code"
    assert tools[0]["description"] == "Format code, organize imports, and remove unused variables"
    assert "file_path" in tools[0]["inputSchema"]["properties"]
    assert tools[0]["inputSchema"]["required"] == ["file_path"]


def test_typescript_router_switch_cases():
    code = """
    import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      switch (request.params.name) {
        case "execute_sql_query":
          return await handleSql(request.params.arguments);
        case "describe_table_schema":
          return await handleDescribe(request.params.arguments);
        case "export_to_csv":
          return await handleExport(request.params.arguments);
        default:
          throw new Error("Unknown tool");
      }
    });
    """
    tools = parse_typescript_mcp_ast(code)
    tool_names = {t["name"] for t in tools}
    assert tool_names == {"execute_sql_query", "describe_table_schema", "export_to_csv"}


def test_typescript_router_if_branches():
    code = """
    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      if (name === "read_file_contents") {
        return handleRead(args);
      } else if (name === "write_file_contents") {
        return handleWrite(args);
      }
      throw new Error(`Tool ${name} not found`);
    });
    """
    tools = parse_typescript_mcp_ast(code)
    tool_names = {t["name"] for t in tools}
    assert tool_names == {"read_file_contents", "write_file_contents"}


def test_typescript_standalone_tool_helpers():
    code = """
    const readTool = tool("read_resource", "Reads a specific resource by URI", { uri: z.string() });
    const writeTool = createTool("write_resource", { content: z.string() });
    const deleteTool = defineTool("delete_resource");
    """
    tools = parse_typescript_mcp_ast(code)
    tool_names = {t["name"] for t in tools}
    assert "read_resource" in tool_names
    assert "write_resource" in tool_names
    assert "delete_resource" in tool_names
