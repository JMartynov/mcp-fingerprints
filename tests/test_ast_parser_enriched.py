"""Tests for enriched AST extraction across Python and TypeScript MCP servers (VC-34.1, VC-34.2, VC-34.3)."""

from __future__ import annotations

import unittest
from mcp_fingerprints.ast_parser import (
    AstBundleResult,
    parse_python_mcp_ast,
    parse_python_mcp_ast_bundle,
    parse_typescript_mcp_ast,
)


class TestAstParserEnriched(unittest.TestCase):
    """Verify deep AST extraction features."""

    def test_vc34_1_python_docstring_parameter_descriptions(self) -> None:
        """Verify extraction of Google, Sphinx, and NumPy docstring parameter descriptions."""
        # Google style
        code_google = '''
@mcp.tool()
def search_docs(query: str, limit: int = 10) -> str:
    """Search the documentation repository.

    Args:
        query: The search term to find.
        limit: Max results to return.
    """
    return query
'''
        res_google = parse_python_mcp_ast(code_google)
        self.assertEqual(len(res_google), 1)
        tool = res_google[0]
        self.assertEqual(tool["name"], "search_docs")
        self.assertEqual(
            tool["inputSchema"]["properties"]["query"]["description"],
            "The search term to find.",
        )
        self.assertEqual(
            tool["inputSchema"]["properties"]["limit"]["description"],
            "Max results to return.",
        )
        self.assertEqual(tool["inputSchema"]["properties"]["limit"]["default"], 10)
        self.assertEqual(tool["inputSchema"]["required"], ["query"])

        # Sphinx style
        code_sphinx = '''
@mcp.tool()
def fetch_item(item_id: str) -> str:
    """Fetch an item by ID.

    :param item_id: Unique identifier for the item.
    """
    return item_id
'''
        res_sphinx = parse_python_mcp_ast(code_sphinx)
        self.assertEqual(len(res_sphinx), 1)
        self.assertEqual(
            res_sphinx[0]["inputSchema"]["properties"]["item_id"]["description"],
            "Unique identifier for the item.",
        )

        # NumPy style
        code_numpy = '''
@mcp.tool()
def compute_matrix(rows: int) -> str:
    """Compute matrix dimensions.

    Parameters
    ----------
    rows : int
        Number of rows to generate.
    """
    return str(rows)
'''
        res_numpy = parse_python_mcp_ast(code_numpy)
        self.assertEqual(len(res_numpy), 1)
        self.assertEqual(
            res_numpy[0]["inputSchema"]["properties"]["rows"]["description"],
            "Number of rows to generate.",
        )

    def test_vc34_1_python_pydantic_field_and_annotated(self) -> None:
        """Verify Pydantic Field, Annotated, Literal enum, and List item types."""
        py_code = '''
from typing import Annotated, Literal, List
from pydantic import BaseModel, Field

class FilterModel(BaseModel):
    category: Literal["news", "blog", "paper"] = Field(description="Filter by category", default="news")
    tags: List[str] = Field(default=["tech"], description="Tag filters")
    score_threshold: Annotated[float, Field(description="Minimum confidence score", default=0.75)]

@mcp.tool()
def filter_articles(filters: FilterModel) -> str:
    """Filter articles according to model."""
    return "ok"
'''
        res = parse_python_mcp_ast(py_code)
        self.assertEqual(len(res), 1)
        tool = res[0]
        props = tool["inputSchema"]["properties"]

        self.assertEqual(props["category"]["type"], "string")
        self.assertEqual(props["category"]["description"], "Filter by category")
        self.assertEqual(props["category"]["default"], "news")
        self.assertEqual(props["category"]["enum"], ["news", "blog", "paper"])

        self.assertEqual(props["tags"]["type"], "array")
        self.assertEqual(props["tags"]["description"], "Tag filters")
        self.assertEqual(props["tags"]["items"], {"type": "string"})

        self.assertEqual(props["score_threshold"]["type"], "number")
        self.assertEqual(
            props["score_threshold"]["description"], "Minimum confidence score"
        )
        self.assertEqual(props["score_threshold"]["default"], 0.75)

    def test_vc34_1_cross_file_pydantic_bundle(self) -> None:
        """Verify cross-file Pydantic model resolution in parse_python_mcp_ast_bundle."""
        files = {
            "models.py": """
from pydantic import BaseModel, Field

class DeployConfig(BaseModel):
    env_name: str = Field(description="Deployment environment name")
    replicas: int = Field(default=3, description="Target replica count")
""",
            "server.py": '''
import os
from mcp.server.fastmcp import FastMCP
from models import DeployConfig

mcp = FastMCP("DeployServer")

@mcp.tool()
def deploy_service(config: DeployConfig) -> str:
    """Deploy service using config."""
    token = os.getenv("DEPLOY_TOKEN")
    return f"Deploying to {config.env_name}"

@mcp.prompt()
def review_deployment(env: str) -> str:
    """Prompt for reviewing deployment status."""
    return f"Review {env}"

@mcp.resource("config://status")
def get_status() -> str:
    """Get current status resource."""
    secret = os.environ["STATUS_SECRET"]
    return "ok"
''',
        }
        res = parse_python_mcp_ast_bundle(files)
        self.assertIsInstance(res, AstBundleResult)
        self.assertEqual(len(res.tools), 1)
        tool = res.tools[0]
        self.assertEqual(tool["name"], "deploy_service")
        self.assertIn("env_name", tool["inputSchema"]["properties"])
        self.assertEqual(
            tool["inputSchema"]["properties"]["env_name"]["description"],
            "Deployment environment name",
        )
        self.assertIn("replicas", tool["inputSchema"]["properties"])
        self.assertEqual(tool["inputSchema"]["properties"]["replicas"]["default"], 3)

        # Prompts and resources
        self.assertEqual(len(res.prompts), 1)
        self.assertEqual(res.prompts[0]["name"], "review_deployment")
        self.assertEqual(len(res.resources), 1)
        self.assertEqual(res.resources[0]["uri_template"], "config://status")

        # Environment variables
        self.assertIn("DEPLOY_TOKEN", res.env_vars)
        self.assertIn("STATUS_SECRET", res.env_vars)

    def test_vc34_2_typescript_balanced_zod_parser(self) -> None:
        """Verify balanced Zod schema parser with .describe(), .default(), .enum(), .optional(), z.array(), and nested z.object()."""
        ts_code = """
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({ name: "cloud", version: "1.0.0" });

server.tool(
  "provision_cluster",
  "Provision a new cloud Kubernetes cluster",
  {
    region: z.enum(["us-east-1", "eu-west-1"]).describe("AWS region code"),
    nodeCount: z.number().default(5).describe("Initial node count"),
    vpc: z.object({
      cidr: z.string().describe("CIDR block"),
      enableDns: z.boolean().default(true),
    }).describe("VPC configuration"),
    tags: z.array(z.string()).optional().describe("Resource tags"),
    adminEmail: z.string().optional()
  },
  async (args) => {
    const apiKey = process.env.CLOUD_API_KEY;
    const orgId = process.env['CLOUD_ORG_ID'];
    return { content: [{ type: "text", text: "Cluster created" }] };
  }
);
"""
        res = parse_typescript_mcp_ast(ts_code)
        self.assertIsInstance(res, AstBundleResult)
        self.assertEqual(len(res.tools), 1)
        tool = res.tools[0]
        self.assertEqual(tool["name"], "provision_cluster")
        self.assertEqual(
            tool["description"], "Provision a new cloud Kubernetes cluster"
        )

        props = tool["inputSchema"]["properties"]
        self.assertEqual(props["region"]["type"], "string")
        self.assertEqual(props["region"]["description"], "AWS region code")
        self.assertEqual(props["region"]["enum"], ["us-east-1", "eu-west-1"])

        self.assertEqual(props["nodeCount"]["type"], "number")
        self.assertEqual(props["nodeCount"]["default"], 5)
        self.assertEqual(props["nodeCount"]["description"], "Initial node count")

        self.assertEqual(props["vpc"]["type"], "object")
        self.assertEqual(props["vpc"]["description"], "VPC configuration")
        self.assertIn("cidr", props["vpc"]["properties"])
        self.assertEqual(
            props["vpc"]["properties"]["cidr"]["description"], "CIDR block"
        )
        self.assertIn("enableDns", props["vpc"]["properties"])
        self.assertEqual(props["vpc"]["properties"]["enableDns"]["default"], True)

        self.assertEqual(props["tags"]["type"], "array")
        self.assertEqual(props["tags"]["items"], {"type": "string"})
        self.assertEqual(props["tags"]["description"], "Resource tags")

        # Required fields: region, vpc (nodeCount has default, tags and adminEmail are optional)
        self.assertIn("region", tool["inputSchema"]["required"])
        self.assertIn("vpc", tool["inputSchema"]["required"])
        self.assertNotIn("tags", tool["inputSchema"]["required"])
        self.assertNotIn("adminEmail", tool["inputSchema"]["required"])
        self.assertNotIn("nodeCount", tool["inputSchema"]["required"])

        # Environment variables
        self.assertIn("CLOUD_API_KEY", res.env_vars)
        self.assertIn("CLOUD_ORG_ID", res.env_vars)

    def test_vc34_2_typescript_bundled_js_list_tools(self) -> None:
        """Verify bundled JS ListToolsRequestSchema handler extraction."""
        js_code = """
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "bundled_tool_a",
        description: "Executes bundled action A",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "bundled_tool_b",
        description: "Executes bundled action B"
      }
    ]
  };
});
"""
        res = parse_typescript_mcp_ast(js_code)
        self.assertEqual(len(res.tools), 2)
        names = [t["name"] for t in res.tools]
        self.assertIn("bundled_tool_a", names)
        self.assertIn("bundled_tool_b", names)

    def test_vc34_3_ast_bundle_result_compatibility(self) -> None:
        """Verify AstBundleResult acts as a list of tools for backwards compatibility."""
        res = AstBundleResult(
            tools=[{"name": "tool1"}, {"name": "tool2"}],
            prompts=[{"name": "prompt1"}],
            resources=[{"name": "resource1"}],
            env_vars={"TOKEN_A", "TOKEN_B"},
        )
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["name"], "tool1")
        self.assertEqual(res[1]["name"], "tool2")
        tool_names = [t["name"] for t in res]
        self.assertEqual(tool_names, ["tool1", "tool2"])
        self.assertEqual(len(res.prompts), 1)
        self.assertEqual(len(res.resources), 1)
        self.assertEqual(res.env_vars, ("TOKEN_A", "TOKEN_B"))


if __name__ == "__main__":
    unittest.main()
