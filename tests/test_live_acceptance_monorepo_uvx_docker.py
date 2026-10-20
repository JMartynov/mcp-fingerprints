import pytest
from pathlib import Path
import json
from mcp_fingerprints.ast_parser import parse_mcp_source_code
from mcp_fingerprints.crawler.docker_hub import extract_docker_stdio_args
from mcp_fingerprints.schema_validator import PassportSchemaValidator

def test_pep723_script_parsing():
    code = """
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mcp[cli]",
#     "fastmcp",
# ]
# ///

from fastmcp import FastMCP

mcp = FastMCP("test_server")

@mcp.tool()
def hello_world(name: str) -> str:
    \"\"\"Say hello to someone.\"\"\"
    return f"Hello {name}"
"""
    res = parse_mcp_source_code(code, "python")
    assert hasattr(res, "dependencies"), "AstBundleResult missing dependencies attribute"
    assert res.dependencies == ["mcp[cli]", "fastmcp"], "Dependencies not correctly extracted"
    
    assert len(res) == 1
    tool = res[0]
    assert tool["name"] == "hello_world"

def test_docker_command_parsing():
    image, args = extract_docker_stdio_args("docker run -i --rm -e MY_VAR=1 -v /tmp:/tmp my-mcp-server arg1 arg2")
    assert image == "my-mcp-server"
    assert args == ["arg1", "arg2"]
    
    image, args = extract_docker_stdio_args("docker run my-mcp-server")
    assert image == "my-mcp-server"
    assert args == []

def test_representative_passports_conformance():
    file1 = Path("data/fingerprints/pypi/t/test_uvx_script.json")
    is_valid1, errors1 = PassportSchemaValidator.validate_file(file1)
    assert is_valid1, f"UVX script passport invalid: {errors1}"
    
    data1 = json.loads(file1.read_text())
    deps = data1["versions"][0].get("dependencies", {})
    assert "mcp[cli]" in deps, "Dependencies missing in UVX passport"
    assert data1["versions"][0]["connections"][0]["command"] == "uvx"

    file2 = Path("data/fingerprints/docker/t/test_docker_mcp.json")
    is_valid2, errors2 = PassportSchemaValidator.validate_file(file2)
    assert is_valid2, f"Docker MCP passport invalid: {errors2}"
    
    data2 = json.loads(file2.read_text())
    assert data2["versions"][0]["connections"][0]["command"] == "docker"
    assert "test_docker_mcp" in data2["versions"][0]["connections"][0]["args"]

