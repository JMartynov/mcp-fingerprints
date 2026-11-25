"""Locked ATDD unit tests for AC-105.6: export-config uses FingerprintFastIndex O(1) lookup."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

from mcp_fingerprints.cli import main
from mcp_fingerprints.index import FingerprintFastIndex
from mcp_fingerprints.models import (
    ServerPackageSpec,
    ToolContractSignature,
    VersionFingerprint,
)


def _write_sample_passport(directory: Path, package_name: str = "test-server") -> ServerPackageSpec:
    spec = ServerPackageSpec(
        package_name=package_name,
        purl=f"pkg:npm/{package_name}",
        ecosystem="npm",
        aliases=("test-alias",),
        versions=(
            VersionFingerprint(
                version="1.0.0",
                toolset_canonical_hash="sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                connections=[
                    {"type": "stdio", "command": "npx", "args": ["-y", package_name]}
                ],
                tool_signatures=(
                    ToolContractSignature(
                        name="ping",
                        canonical_hash="sha256:1111111111111111111111111111111111111111111111111111111111111111",
                        description="Ping server",
                    ),
                ),
            ),
        ),
    )
    (directory / f"{package_name}.json").write_text(
        json.dumps(spec.to_dict()), encoding="utf-8"
    )
    return spec


def test_export_config_uses_fast_index(tmp_path: Path, capsys) -> None:
    """Verify export-config does not call Path.rglob and invokes FingerprintFastIndex.lookup once."""
    _write_sample_passport(tmp_path, "test-server")
    # Pre-warm binary index cache so load_from_directory restores in O(1) without rglob.
    warm_idx = FingerprintFastIndex()
    assert warm_idx.load_from_directory(tmp_path) == 1

    with (
        patch.object(
            Path,
            "rglob",
            side_effect=AssertionError("Path.rglob must not be invoked by export-config"),
        ) as mock_rglob,
        patch.object(
            FingerprintFastIndex,
            "lookup",
            autospec=True,
            wraps=FingerprintFastIndex.lookup,
        ) as mock_lookup,
        patch.object(
            sys,
            "argv",
            [
                "mcp-fingerprints",
                "export-config",
                "--server-id",
                "test-server",
                "--dir",
                str(tmp_path),
            ],
        ),
    ):
        main()

    mock_rglob.assert_not_called()
    assert mock_lookup.call_count == 1
    assert mock_lookup.call_args.args[1] == "test-server"

    captured = capsys.readouterr()
    exported = json.loads(captured.out)
    assert "mcpServers" in exported
    assert "test-server" in exported["mcpServers"]


def test_unknown_hash_returns_none(tmp_path: Path) -> None:
    """Paired benign control: unknown passport hash or server id returns None without raising."""
    _write_sample_passport(tmp_path, "known-server")
    idx = FingerprintFastIndex()
    idx.load_from_directory(tmp_path)

    unknown_hash = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    assert idx.lookup(unknown_hash) is None
    assert idx.lookup("nonexistent-package-xyz") is None
    assert idx.lookup("") is None
