import pytest
from pathlib import Path
from mcp_fingerprints.prober import ProbeReport
from mcp_fingerprints.auto_passport import generate_auto_passport
import json

def test_generate_auto_passport(tmp_path):
    report = ProbeReport(
        server_command=["dummy"],
        connection_successful=True,
        tools_observed=[
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    },
                    "required": ["param1"]
                }
            }
        ]
    )
    
    spec = generate_auto_passport(report, tmp_path, server_name="test-server")
    assert spec is not None
    assert spec.package_name == "test-server"
    assert len(spec.versions) == 1
    assert len(spec.versions[0].tool_signatures) == 1
    
    saved_file = tmp_path / "test-server.json"
    assert saved_file.exists()
    
    with open(saved_file, "r") as f:
        data = json.load(f)
        assert data["package_name"] == "test-server"
        assert len(data["versions"]) == 1

def test_generate_auto_passport_no_tools(tmp_path):
    report = ProbeReport(
        server_command=["dummy"],
        connection_successful=True,
        tools_observed=[]
    )
    
    spec = generate_auto_passport(report, tmp_path, server_name="no-tools-server")
    assert spec is None
    
    saved_file = tmp_path / "no-tools-server.json"
    assert not saved_file.exists()
