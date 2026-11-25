"""Locked ATDD unit tests for AC-105.8: wizard wired to ~/.mcp_fingerprints.toml and CLI --help."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_fingerprints.cli import main
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.wizard import load_user_config, run_init_wizard


def test_wizard_wired_or_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Verify wizard writes ~/.mcp_fingerprints.toml and CLI loads and applies it."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    # Absent config returns empty dict cleanly.
    assert load_user_config() == {}

    # Run interactive wizard to generate ~/.mcp_fingerprints.toml.
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", side_effect=["y", "n", "n", "n", "n", "y"]),
    ):
        run_init_wizard()

    cfg_path = tmp_path / ".mcp_fingerprints.toml"
    assert cfg_path.is_file()
    loaded = load_user_config()
    assert loaded.get("clients") == ["Claude"]
    assert loaded.get("semantic_search") is True

    # Extend ~/.mcp_fingerprints.toml with default_dir, github_token, concurrency and wire into CLI.
    passports_dir = tmp_path / "custom_passports"
    passports_dir.mkdir()
    spec = ServerPackageSpec(
        package_name="wizard-test-pkg",
        purl="pkg:npm/wizard-test-pkg",
        ecosystem="npm",
        versions=(
            VersionFingerprint(
                version="1.0.0",
                toolset_canonical_hash="sha256:123456",
                connections=[
                    {"type": "stdio", "command": "npx", "args": ["-y", "wizard-test-pkg"]}
                ],
            ),
        ),
    )
    (passports_dir / "wizard-test-pkg.json").write_text(
        json.dumps(spec.to_dict()), encoding="utf-8"
    )

    cfg_path.write_text(
        "[mcp_fingerprints]\n"
        'clients = ["Claude"]\n'
        "semantic_search = true\n"
        f'default_dir = "{passports_dir.as_posix()}"\n'
        'github_token = "tok_task105_test"\n'
        "concurrency = 4\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    capsys.readouterr()

    with patch.object(
        sys,
        "argv",
        ["mcp-fingerprints", "export-config", "--server-id", "wizard-test-pkg"],
    ):
        main()

    captured = capsys.readouterr()
    exported = json.loads(captured.out)
    assert "mcpServers" in exported
    assert "wizard-test-pkg" in exported["mcpServers"]
    assert os.environ.get("GITHUB_TOKEN") == "tok_task105_test"


def test_cli_help_parses(capsys) -> None:
    """Paired benign control: --help output parses as valid usage text matching implemented subcommands."""
    with patch.object(sys, "argv", ["mcp-fingerprints", "--help"]), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    out = capsys.readouterr().out
    assert "usage:" in out
    assert "init" in out
    assert "export-config" in out

    match = re.search(r"\{([^}]+)\}", out)
    assert match is not None, "Expected subcommand list in --help usage output"
    subcommands = [s.strip() for s in match.group(1).split(",") if s.strip()]
    assert "init" in subcommands
    assert "export-config" in subcommands

    cli_source = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "mcp_fingerprints"
        / "cli.py"
    ).read_text(encoding="utf-8")
    for subcmd in subcommands:
        assert f'"{subcmd}"' in cli_source, f"Subcommand {subcmd!r} missing from cli.py"
