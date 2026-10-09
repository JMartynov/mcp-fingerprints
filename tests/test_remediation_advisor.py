import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from mcp_fingerprints.models import (
    ServerPackageSpec,
    ToolContractSignature,
    VersionFingerprint,
)
from mcp_fingerprints.remediation_advisor import (
    RemediationAction,
    RemediationReport,
    evaluate_client_config,
)


def test_evaluate_client_config_clean():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "clean-server": {
                            "command": "npx",
                            "args": ["-y", "clean-pkg@1.0.0"],
                        }
                    }
                }
            )
        )
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        # Mock index
        with patch(
            "mcp_fingerprints.remediation_advisor.FingerprintFastIndex"
        ) as MockIndex:
            instance = MockIndex.return_value
            pkg_spec = ServerPackageSpec(
                package_name="clean-pkg",
                purl="pkg:npm/clean-pkg",
                ecosystem="npm",
                versions=(
                    VersionFingerprint(version="1.0.0", toolset_canonical_hash="abc"),
                ),
                security_profile={"vulnerable_versions": []},
            )
            instance.find_package_by_hint_or_alias.return_value = pkg_spec

            report = evaluate_client_config(config_path, passport_dir)
            assert report.is_clean is True
            assert len(report.actions) == 0


def test_evaluate_client_config_upgrade():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "vuln-server": {"command": "uvx", "args": ["vuln-pkg@1.0.0"]}
                    }
                }
            )
        )
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        with patch(
            "mcp_fingerprints.remediation_advisor.FingerprintFastIndex"
        ) as MockIndex:
            instance = MockIndex.return_value
            pkg_spec = ServerPackageSpec(
                package_name="vuln-pkg",
                purl="pkg:pypi/vuln-pkg",
                ecosystem="pypi",
                versions=(
                    VersionFingerprint(version="1.0.0", toolset_canonical_hash="abc"),
                    VersionFingerprint(version="1.1.0", toolset_canonical_hash="def"),
                ),
                security_profile={
                    "vulnerable_versions": ["1.0.0"],
                    "advisories": [
                        {"id": "CVE-2024-1234", "affected_versions": ["1.0.0"]}
                    ],
                },
            )
            instance.find_package_by_hint_or_alias.return_value = pkg_spec

            report = evaluate_client_config(config_path, passport_dir)
            assert report.is_clean is False
            assert len(report.actions) == 1
            action = report.actions[0]
            assert action.action_type == "upgrade"
            assert action.target_version == "1.1.0"
            assert action.cve_list == ["CVE-2024-1234"]


def test_evaluate_client_config_replace():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "abandoned-server": {
                            "command": "npx",
                            "args": ["-y", "abandoned-pkg@1.0.0"],
                        }
                    }
                }
            )
        )
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        with patch(
            "mcp_fingerprints.remediation_advisor.FingerprintFastIndex"
        ) as MockIndex:
            instance = MockIndex.return_value
            abandoned_spec = ServerPackageSpec(
                package_name="abandoned-pkg",
                purl="pkg:npm/abandoned-pkg",
                ecosystem="npm",
                versions=(
                    VersionFingerprint(
                        version="1.0.0",
                        toolset_canonical_hash="abc",
                        tool_signatures=(
                            ToolContractSignature(name="toolA", canonical_hash="1"),
                            ToolContractSignature(name="toolB", canonical_hash="2"),
                        ),
                    ),
                ),
                security_profile={
                    "vulnerable_versions": ["1.0.0"],
                    "advisories": [
                        {"id": "CVE-2024-5678", "affected_versions": ["1.0.0"]}
                    ],
                },
            )

            # Alternative package that is safe and has same tools
            alt_spec = ServerPackageSpec(
                package_name="safe-alt-pkg",
                purl="pkg:npm/safe-alt-pkg",
                ecosystem="npm",
                versions=(
                    VersionFingerprint(
                        version="2.0.0",
                        toolset_canonical_hash="def",
                        tool_signatures=(
                            ToolContractSignature(name="toolA", canonical_hash="1"),
                            ToolContractSignature(name="toolB", canonical_hash="2"),
                        ),
                    ),
                ),
                security_profile={"vulnerable_versions": []},
            )

            instance.find_package_by_hint_or_alias.return_value = abandoned_spec
            instance.packages = {
                "abandoned-pkg": abandoned_spec,
                "safe-alt-pkg": alt_spec,
            }

            report = evaluate_client_config(config_path, passport_dir)
            assert report.is_clean is False
            assert len(report.actions) == 1
            action = report.actions[0]
            assert action.action_type == "replace"
            assert action.target_package == "safe-alt-pkg"
            assert action.target_version == "2.0.0"
            assert action.similarity_score == 1.0


def test_evaluate_client_config_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "doomed-server": {
                            "command": "npx",
                            "args": ["-y", "doomed-pkg@1.0.0"],
                        }
                    }
                }
            )
        )
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        with patch(
            "mcp_fingerprints.remediation_advisor.FingerprintFastIndex"
        ) as MockIndex:
            instance = MockIndex.return_value
            doomed_spec = ServerPackageSpec(
                package_name="doomed-pkg",
                purl="pkg:npm/doomed-pkg",
                ecosystem="npm",
                versions=(
                    VersionFingerprint(
                        version="1.0.0",
                        toolset_canonical_hash="abc",
                        tool_signatures=(
                            ToolContractSignature(
                                name="uniqueTool123", canonical_hash="1"
                            ),
                        ),
                    ),
                ),
                security_profile={
                    "vulnerable_versions": ["1.0.0"],
                    "advisories": [
                        {"id": "CVE-2024-9999", "affected_versions": ["1.0.0"]}
                    ],
                },
            )

            instance.find_package_by_hint_or_alias.return_value = doomed_spec
            instance.packages = {"doomed-pkg": doomed_spec}

            report = evaluate_client_config(config_path, passport_dir)
            assert report.is_clean is False
            assert len(report.actions) == 1
            action = report.actions[0]
            assert action.action_type == "none"
            assert report.unremediated_count == 1


def test_cli_fix_advisories_apply():
    # Test that --apply command actually writes correct JSON schema back
    from mcp_fingerprints.cli import main

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_data = {
            "mcpServers": {
                "vuln-server": {
                    "command": "uvx",
                    "args": ["vuln-pkg@1.0.0", "--some-flag"],
                },
                "other-server": {"command": "node", "args": ["index.js"]},
            }
        }
        config_path.write_text(json.dumps(config_data))
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "fix-advisories",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--apply",
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            mock_eval.return_value = RemediationReport(
                is_clean=False,
                actions=[
                    RemediationAction(
                        package_name="vuln-pkg",
                        current_version="1.0.0",
                        cve_list=["CVE-TEST"],
                        action_type="upgrade",
                        target_package="vuln-pkg",
                        target_version="1.1.0",
                    )
                ],
                unremediated_count=0,
            )

            # run CLI
            try:
                main()
            except SystemExit as e:
                # Expect exit code 0 or 1 depending on whether things were left unremediated
                assert e.code == 0

            # Verify file was updated
            new_conf = json.loads(config_path.read_text())
            assert new_conf["mcpServers"]["vuln-server"]["args"] == [
                "vuln-pkg@1.1.0",
                "--some-flag",
            ]
            assert new_conf["mcpServers"]["other-server"]["args"] == ["index.js"]


def test_cli_fix_advisories_apply_replace():
    import json
    import tempfile
    from pathlib import Path
    from unittest.mock import patch

    from mcp_fingerprints.cli import main
    from mcp_fingerprints.remediation_advisor import (
        RemediationAction,
        RemediationReport,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_data = {
            "mcpServers": {
                "vuln-server": {
                    "command": "uvx",
                    "args": ["vuln-pkg@1.0.0", "--some-flag"],
                },
                "other-server": {"command": "node", "args": ["index.js"]},
            }
        }
        config_path.write_text(json.dumps(config_data))
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "fix-advisories",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--apply",
            "--strategy",
            "replace",
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            mock_eval.return_value = RemediationReport(
                is_clean=False,
                actions=[
                    RemediationAction(
                        package_name="vuln-pkg",
                        current_version="1.0.0",
                        cve_list=["CVE-TEST"],
                        action_type="replace",
                        target_package="safe-pkg",
                        target_version="2.0.0",
                        similarity_score=1.0,
                    )
                ],
                unremediated_count=0,
            )

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            new_conf = json.loads(config_path.read_text())
            assert new_conf["mcpServers"]["vuln-server"]["args"] == [
                "safe-pkg@2.0.0",
                "--some-flag",
            ]
            assert new_conf["mcpServers"]["other-server"]["args"] == ["index.js"]
