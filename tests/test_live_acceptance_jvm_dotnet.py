from mcp_fingerprints.ast_parser import parse_jvm_mcp_code, parse_dotnet_mcp_code
from mcp_fingerprints.schema_validator import PassportSchemaValidator
import json


def test_jvm_spring_ai_mcp_parsing():
    code = """
    package com.example;

    import org.springframework.ai.tool.annotation.Tool;
    import org.springframework.ai.tool.annotation.ToolParam;

    public class WeatherService {

        @Tool(name = "get_weather", description = "Get current weather")
        public String getWeather(
            @ToolParam(description = "The city") String city,
            @ToolParam(description = "Use metric units") boolean metric
        ) {
            return "Sunny";
        }
    }
    """
    tools = parse_jvm_mcp_code(code)
    assert len(tools) == 1
    tool = tools[0]
    assert tool["name"] == "get_weather"
    assert tool["description"] == "Get current weather"
    props = tool["inputSchema"]["properties"]
    assert "city" in props
    assert props["city"]["type"] == "string"
    assert "metric" in props
    assert props["metric"]["type"] == "boolean"


def test_dotnet_mcp_parsing():
    code = """
    using ModelContextProtocol.NET.Server;
    using Microsoft.SemanticKernel;
    using System.ComponentModel;

    public class MathTools {
        
        [McpServerTool(Name = "calculate_sum")]
        [Description("Add two numbers")]
        public async Task<int> CalculateSum(
            [Description("First number")] int a,
            [Description("Second number")] int b = 0
        ) {
            return a + b;
        }

        [KernelFunction, Description("Multiply numbers")]
        public int Multiply(int x, int y) {
            return x * y;
        }
    }
    """
    tools = parse_dotnet_mcp_code(code)
    assert len(tools) == 2

    # Tool 1
    t1 = next(t for t in tools if t["name"] == "calculate_sum")
    assert t1["description"] == "Add two numbers"
    assert "a" in t1["inputSchema"]["properties"]
    assert t1["inputSchema"]["properties"]["a"]["type"] == "number"
    assert "b" in t1["inputSchema"]["properties"]
    assert "a" in t1["inputSchema"]["required"]
    assert "b" not in t1["inputSchema"]["required"]  # has default

    # Tool 2
    t2 = next(t for t in tools if t["name"] == "Multiply")
    assert t2["description"] == "Multiply numbers"
    assert "x" in t2["inputSchema"]["properties"]
    assert "y" in t2["inputSchema"]["properties"]
    assert "x" in t2["inputSchema"]["required"]


def test_enterprise_passport_validation():
    # Will be tested after we add the passport
    with open("data/fingerprints/maven/s/spring-ai-mcp.json") as f:
        data = json.load(f)
    validator = PassportSchemaValidator()
    validator.validate_passport_dict(data)
