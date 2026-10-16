"""Unit tests for the CLI runtime sandbox probe integration."""

import json
from pathlib import Path
from unittest.mock import patch
from mcp_fingerprints.synchronizer import PassportSynchronizer
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint


def test_probe_runtime_passports_success(tmp_path):
    passport_dir = tmp_path / "passports"
    passport_dir.mkdir(parents=True)

    spec = ServerPackageSpec(
        package_name="test-server",
        purl="pkg:npm/test-server",
        ecosystem="npm",
        versions=(
            VersionFingerprint(
                version="1.0.0",
                toolset_canonical_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                capabilities={"tools": False},
                connections=({"type": "stdio", "command": "npx", "args": ["-y", "test-server"]},),
            ),
        ),
    )
    p_file = passport_dir / "test_server.json"
    p_file.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")

    mock_tools = [
        {
            "name": "runtime_tool_1",
            "description": "Observed during stdio handshake",
            "inputSchema": {"properties": {"arg": {"type": "string"}}},
        }
    ]

    sync = PassportSynchronizer(output_dir=passport_dir)
    with patch("mcp_fingerprints.synchronizer.probe_mcp_server_stdio", return_value=mock_tools):
        count = sync.probe_runtime_passports(limit=10, timeout=2.0)

    assert count == 1
    updated_data = json.loads(p_file.read_text(encoding="utf-8"))
    updated_spec = ServerPackageSpec.from_dict(updated_data)

    latest_v = updated_spec.versions[0]
    assert latest_v.capabilities.get("runtime_verified") is True
    assert latest_v.capabilities.get("verified_tools") is True
    assert len(latest_v.tool_signatures) == 1
    assert latest_v.tool_signatures[0].name == "runtime_tool_1"
    assert "runtime_sandbox" in updated_spec.sources_merged


def test_probe_runtime_passports_unsafe_command_skipped(tmp_path):
    passport_dir = tmp_path / "passports"
    passport_dir.mkdir(parents=True)

    spec = ServerPackageSpec(
        package_name="unsafe-server",
        purl="pkg:generic/unsafe-server",
        ecosystem="generic",
        versions=(
            VersionFingerprint(
                version="1.0.0",
                toolset_canonical_hash="sha256:empty",
                connections=({"type": "stdio", "command": "bash", "args": ["-c", "echo exploit"]},),
            ),
        ),
    )
    p_file = passport_dir / "unsafe_server.json"
    p_file.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")

    sync = PassportSynchronizer(output_dir=passport_dir)
    with patch("mcp_fingerprints.synchronizer.probe_mcp_server_stdio") as mock_probe:
        count = sync.probe_runtime_passports(limit=10, safe_only=True)
        assert count == 0
        assert not mock_probe.called


def test_probe_runtime_passports_timeout_or_empty(tmp_path):
    passport_dir = tmp_path / "passports"
    passport_dir.mkdir(parents=True)

    spec = ServerPackageSpec(
        package_name="failing-server",
        purl="pkg:npm/failing-server",
        ecosystem="npm",
        versions=(
            VersionFingerprint(
                version="1.0.0",
                toolset_canonical_hash="sha256:empty",
                connections=({"type": "stdio", "command": "npx", "args": ["failing"]},),
            ),
        ),
    )
    p_file = passport_dir / "failing.json"
    p_file.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")

    sync = PassportSynchronizer(output_dir=passport_dir)
    with patch("mcp_fingerprints.synchronizer.probe_mcp_server_stdio", return_value=[]):
        count = sync.probe_runtime_passports(limit=10)
        assert count == 0

    data = json.loads(p_file.read_text(encoding="utf-8"))
    assert not data["versions"][0]["capabilities"].get("runtime_verified")
