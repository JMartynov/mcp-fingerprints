from mcp_fingerprints.snapshot_diff import (
    InventorySnapshot,
    DiscoveredServer,
    compare_snapshots,
)
from mcp_fingerprints.models import ToolContractSignature


def test_inventory_snapshot_serialization(tmp_path):
    tool = ToolContractSignature(
        name="test_tool",
        canonical_hash="hash1",
        description="A test tool",
        property_keys=("param1",),
        required_keys=("param1",),
        parameter_types={"param1": "string"},
    )
    server = DiscoveredServer(
        server_name="test_server",
        client_name="Cursor",
        package_name="test_pkg",
        version="1.0.0",
        tools=[tool],
        toolset_canonical_hash="thash1",
    )
    snapshot = InventorySnapshot(
        snapshot_version="1.0.0", host_identifier="test-host", servers=[server]
    )

    file_path = tmp_path / "snapshot.json"
    snapshot.save(file_path)

    loaded = InventorySnapshot.load(file_path)
    assert loaded.snapshot_version == "1.0.0"
    assert loaded.host_identifier == "test-host"
    assert len(loaded.servers) == 1
    assert loaded.servers[0].server_name == "test_server"
    assert loaded.servers[0].tools[0].name == "test_tool"
    assert loaded.servers[0].tools[0].parameter_types["param1"] == "string"


def test_inventory_differ_addition_removal():
    server1 = DiscoveredServer(server_name="s1", client_name="c1")
    server2 = DiscoveredServer(server_name="s2", client_name="c1")
    server3 = DiscoveredServer(server_name="s3", client_name="c2")

    baseline = InventorySnapshot(servers=[server1, server2])
    current = InventorySnapshot(servers=[server2, server3])

    diff = compare_snapshots(baseline, current)

    assert diff.has_changes is True
    assert len(diff.added_servers) == 1
    assert diff.added_servers[0].server_name == "s3"

    assert len(diff.removed_servers) == 1
    assert diff.removed_servers[0].server_name == "s1"

    assert len(diff.modified_servers) == 0


def test_inventory_differ_mutation():
    tool_old = ToolContractSignature(
        name="read_query",
        canonical_hash="9a8f",
        description="Old query",
        property_keys=("q",),
        required_keys=("q",),
        parameter_types={"q": "string"},
    )
    server_old = DiscoveredServer(
        server_name="postgres",
        client_name="Claude",
        version="0.6.1",
        toolset_canonical_hash="t_old",
        tools=[tool_old],
    )

    tool_new = ToolContractSignature(
        name="read_query",
        canonical_hash="4b2c",
        description="New query",
        property_keys=("q", "timeout_ms"),
        required_keys=("q",),
        parameter_types={"q": "string", "timeout_ms": "integer"},
    )
    tool_added = ToolContractSignature(name="new_tool", canonical_hash="1111")
    server_new = DiscoveredServer(
        server_name="postgres",
        client_name="Claude",
        version="0.6.2",
        toolset_canonical_hash="t_new",
        tools=[tool_new, tool_added],
    )

    baseline = InventorySnapshot(servers=[server_old])
    current = InventorySnapshot(servers=[server_new])

    diff = compare_snapshots(baseline, current)

    assert diff.has_changes is True
    assert len(diff.added_servers) == 0
    assert len(diff.removed_servers) == 0
    assert len(diff.modified_servers) == 1

    mod = diff.modified_servers[0]
    assert mod.server_name == "postgres"
    assert mod.old_version == "0.6.1"
    assert mod.new_version == "0.6.2"
    assert mod.old_hash == "t_old"
    assert mod.new_hash == "t_new"

    changes = set(mod.changes)
    assert "Tool 'new_tool' added" in changes
    assert "Tool 'read_query': Description changed" in changes
    assert (
        "Tool 'read_query': Parameter 'timeout_ms' added (type: integer, optional)"
        in changes
    )
