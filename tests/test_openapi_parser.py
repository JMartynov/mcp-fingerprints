import json
import pytest
from mcp_fingerprints.openapi_parser import parse_openapi_spec


def test_parse_openapi_3_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Sample API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUserById",
                    "summary": "Get user details by ID",
                    "parameters": [
                        {
                            "name": "userId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Unique identifier of the user",
                        }
                    ],
                },
                "post": {
                    "operationId": "updateUser",
                    "summary": "Update user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                    },
                                    "required": ["email"],
                                }
                            }
                        }
                    },
                },
            }
        },
    }

    tools = parse_openapi_spec(spec)
    assert len(tools) == 2

    get_tool = next(t for t in tools if t["name"] == "getUserById")
    assert get_tool["description"] == "Get user details by ID"
    assert "userId" in get_tool["inputSchema"]["properties"]
    assert get_tool["inputSchema"]["required"] == ["userId"]

    post_tool = next(t for t in tools if t["name"] == "updateUser")
    assert "email" in post_tool["inputSchema"]["properties"]
    assert "name" in post_tool["inputSchema"]["properties"]
    assert post_tool["inputSchema"]["required"] == ["email"]


def test_parse_swagger_2_spec():
    spec_json = json.dumps({
        "swagger": "2.0",
        "info": {"title": "Legacy Swagger", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "summary": "List items",
                    "parameters": [
                        {"name": "limit", "in": "query", "type": "integer", "required": False}
                    ],
                }
            }
        },
    })

    tools = parse_openapi_spec(spec_json)
    assert len(tools) == 1
    assert tools[0]["name"] == "get_items"
    assert tools[0]["description"] == "List items"
    assert "limit" in tools[0]["inputSchema"]["properties"]


def test_parse_openapi_empty_or_invalid():
    assert parse_openapi_spec("") == []
    assert parse_openapi_spec("{}") == []
    assert parse_openapi_spec({"openapi": "3.0.0"}) == []


def test_parse_openapi_yaml_fallback():
    yaml_content = """
openapi: 3.0.0
info:
  title: Test YAML API
  version: 1.0.0
paths:
  /orders:
    get:
      summary: Retrieve orders
      operationId: getOrders
      parameters:
        - name: status
          in: query
    post:
      summary: Create new order
      operationId: createOrder
"""
    tools = parse_openapi_spec(yaml_content)
    assert len(tools) == 2
    tool_names = {t["name"] for t in tools}
    assert tool_names == {"getOrders", "createOrder"}
    get_tool = next(t for t in tools if t["name"] == "getOrders")
    assert get_tool["description"] == "Retrieve orders"
    assert "status" in get_tool["inputSchema"]["properties"]

