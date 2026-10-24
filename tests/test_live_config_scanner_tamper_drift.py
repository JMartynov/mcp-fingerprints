import pytest
from pathlib import Path
import json
import os
import shutil

from mcp_fingerprints.config_scanner import ConfigScanner
from mcp_fingerprints.config_exporter import patch_jsonc
from mcp_fingerprints.drift_detector import compare_passports_for_drift
from mcp_fingerprints.snapshot_diff import InventoryDiffer, InventorySnapshot, DiscoveredServer
from mcp_fingerprints.models import ToolContractSignature

@pytest.fixture
def mock_workstation(tmp_path):
    clients_dir = tmp_path / "clients"
    clients_dir.mkdir()
    
    # 1. Claude
    claude_dir = clients_dir / "claude"
    claude_dir.mkdir()
    with open(claude_dir / "claude_desktop_config.json", "w") as f:
        json.dump({"mcpServers": {"claude_srv": {"command": "echo", "args": ["claude"]}}}, f)
        
    # 2. Cursor (settings.json)
    cursor_dir = clients_dir / "cursor"
    cursor_dir.mkdir()
    with open(cursor_dir / "settings.json", "w") as f:
        f.write('{\n  // A comment\n  "mcpServers": {"cursor_srv": {"command": "echo", "args": ["cursor"]}}\n}')

    # 3. Windsurf
    windsurf_dir = clients_dir / "windsurf"
    windsurf_dir.mkdir()
    with open(windsurf_dir / "mcp.json", "w") as f:
        json.dump({"mcpServers": {"windsurf_srv": {"command": "echo", "args": ["windsurf"]}}}, f)

    # 4. Zed
    zed_dir = clients_dir / "zed"
    zed_dir.mkdir()
    with open(zed_dir / "settings.json", "w") as f:
        json.dump({"context_servers": {"zed_srv": {"command": {"path": "echo", "args": ["zed"]}}}}, f)

    # 5. Cline
    cline_dir = clients_dir / "cline"
    cline_dir.mkdir()
    with open(cline_dir / "cline_mcp_settings.json", "w") as f:
        json.dump({"mcpServers": {"cline_srv": {"command": "echo", "args": ["cline"]}}}, f)

    # 6. Roo
    roo_dir = clients_dir / "roo"
    roo_dir.mkdir()
    with open(roo_dir / "cline_mcp_settings.json", "w") as f:
        json.dump({"mcpServers": {"roo_srv": {"command": "echo", "args": ["roo"]}}}, f)

    # 7. Antigravity
    antigravity_dir = clients_dir / "antigravity"
    antigravity_dir.mkdir()
    with open(antigravity_dir / "mcp_config.json", "w") as f:
        json.dump({"mcpServers": {"antigravity_srv": {"command": "echo", "args": ["antigravity"]}}}, f)

    # 8. OpenHands
    openhands_dir = clients_dir / "openhands"
    openhands_dir.mkdir()
    with open(openhands_dir / "mcp.json", "w") as f:
        json.dump({"mcpServers": {"openhands_srv": {"command": "echo", "args": ["openhands"]}}}, f)
        
    return clients_dir

def test_multi_client_workstation_discovery(mock_workstation):
    scanner = ConfigScanner()
    
    paths_to_scan = [
        mock_workstation / "claude" / "claude_desktop_config.json",
        mock_workstation / "cursor" / "settings.json",
        mock_workstation / "windsurf" / "mcp.json",
        mock_workstation / "zed" / "settings.json",
        mock_workstation / "cline" / "cline_mcp_settings.json",
        mock_workstation / "roo" / "cline_mcp_settings.json",
        mock_workstation / "antigravity" / "mcp_config.json",
        mock_workstation / "openhands" / "mcp.json"
    ]
    
    report = scanner.scan(paths_to_scan, probe_live=False)
    
    servers = {s["name"]: s for s in report.servers}
    
    assert "claude_srv" in servers
    assert "cursor_srv" in servers
    assert "windsurf_srv" in servers
    assert "zed_srv" in servers
    assert "cline_srv" in servers
    assert "roo_srv" in servers
    assert "antigravity_srv" in servers
    assert "openhands_srv" in servers

def test_in_place_config_exporters():
    # Test JSONC with comments
    jsonc = '{\n  // A comment\n  "mcpServers": {\n    "existing": {"command": "echo"}\n  }\n}'
    patched_jsonc = patch_jsonc(jsonc, "mcpServers", "new_server", {"command": "test"})
    assert "// A comment" in patched_jsonc
    assert '"new_server"' in patched_jsonc
    assert '"command": "test"' in patched_jsonc
    assert '"existing"' in patched_jsonc
    
    # Test standard JSON
    standard_json = '{\n  "mcpServers": {\n    "existing": {"command": "echo"}\n  }\n}'
    patched_json = patch_jsonc(standard_json, "mcpServers", "new_server2", {"command": "test2"})
    assert '"new_server2"' in patched_json
    assert '"command": "test2"' in patched_json
    assert '"existing"' in patched_json
    
    # Ensure it's still valid JSON
    parsed = json.loads(patched_json)
    assert parsed["mcpServers"]["new_server2"]["command"] == "test2"
    assert parsed["mcpServers"]["existing"]["command"] == "echo"

def test_supply_chain_tamper_detection_invariants(tmp_path):
    old_map = {
        "test_pkg": {
            "package_name": "test_pkg",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "hash1",
                    "tool_signatures": [{"name": "tool1"}]
                }
            ]
        },
        "test_empty": {
             "package_name": "test_empty",
             "versions": [
                 {
                     "version": "1.0.0",
                     "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                     "tool_signatures": []
                 }
             ]
        }
    }
    
    new_map = {
        "test_pkg": {
            "package_name": "test_pkg",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "hash2", # Hash changed, same version
                    "tool_signatures": [{"name": "tool1"}, {"name": "tool2"}] # Tool added
                }
            ]
        },
        "test_empty": {
             "package_name": "test_empty",
             "versions": [
                 {
                     "version": "1.0.0",
                     "toolset_canonical_hash": "hash3",
                     "tool_signatures": [{"name": "tool1"}]
                 }
             ]
        }
    }
    
    # We pass it as dict directly
    report = compare_passports_for_drift(old_map, new_map)
    
    incidents = report.incidents
    assert len(incidents) >= 1
    
    hash_tamper = [i for i in incidents if i.incident_type == "hash_tamper" and i.package_name == "test_pkg"]
    assert len(hash_tamper) == 1
    assert hash_tamper[0].severity == "critical"
    
    tool_added = [i for i in incidents if i.incident_type == "tool_added" and i.package_name == "test_pkg"]
    assert len(tool_added) == 1
    assert tool_added[0].severity == "high"

    test_empty_tamper = [i for i in incidents if i.package_name == "test_empty"]
    assert len(test_empty_tamper) == 0 # Empty hash transition should be exempted

def test_workstation_baseline_diffing():
    t1 = ToolContractSignature(name="tool1", description="", input_schema={"type": "object"}, canonical_hash="h1")
    t2 = ToolContractSignature(name="tool2", description="", input_schema={"type": "object"}, canonical_hash="h2")
    
    baseline = InventorySnapshot(
        timestamp="2023-01-01T00:00:00Z",
        servers=[
            DiscoveredServer(server_name="s1", client_name="c1", tools=[t1]),
            DiscoveredServer(server_name="s2", client_name="c1", tools=[t1])
        ]
    )
    
    current = InventorySnapshot(
        timestamp="2023-01-02T00:00:00Z",
        servers=[
            DiscoveredServer(server_name="s1", client_name="c1", tools=[t1, t2]), # Modified (tool added)
            DiscoveredServer(server_name="s3", client_name="c1", tools=[t1]) # Added
        ]
    )
    
    diff = InventoryDiffer.compare(baseline, current)
    
    assert len(diff.added_servers) == 1
    assert diff.added_servers[0].server_name == "s3"
    
    assert len(diff.removed_servers) == 1
    assert diff.removed_servers[0].server_name == "s2"
    
    assert len(diff.modified_servers) == 1
    assert diff.modified_servers[0].server_name == "s1"
    assert "Tool 'tool2' added" in diff.modified_servers[0].changes
