import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from mcp_fingerprints.cli import main
from mcp_fingerprints.remediation_advisor import RemediationAction, RemediationReport

def test_audit_config_fix_dry_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_data = {
            "mcpServers": {
                "vuln-server": {
                    "command": "uvx",
                    "args": ["vuln-pkg@1.0.0", "--some-flag"],
                }
            }
        }
        config_path.write_text(json.dumps(config_data))
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "audit-config",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--fix",
            "--dry-run"
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.audit_client_config") as mock_audit,
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            from mcp_fingerprints.conflict_detector import ConflictAuditReport
            mock_audit.return_value = ConflictAuditReport(
                    servers_configured=[],
                    servers_matched_in_passports=[],
                    total_tools_exposed=0,
                    unique_tool_names=0,
                    collisions=[],
                    has_critical_conflicts=False,
                    is_clean=True,
                )
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
                        similarity_score=1.0,
                    )
                ],
                unremediated_count=0,
            )

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # File should not be modified
            read_data = json.loads(config_path.read_text())
            assert read_data["mcpServers"]["vuln-server"]["args"] == ["vuln-pkg@1.0.0", "--some-flag"]
            
            # Backup should not be created
            assert not config_path.with_name("config.json.bak").exists()


def test_audit_config_fix_apply():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_data = {
            "mcpServers": {
                "vuln-server": {
                    "command": "uvx",
                    "args": ["vuln-pkg@1.0.0", "--some-flag"],
                }
            }
        }
        config_path.write_text(json.dumps(config_data))
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "audit-config",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--fix",
            "--backup"
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.audit_client_config") as mock_audit,
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            from mcp_fingerprints.conflict_detector import ConflictAuditReport
            mock_audit.return_value = ConflictAuditReport(
                    servers_configured=[],
                    servers_matched_in_passports=[],
                    total_tools_exposed=0,
                    unique_tool_names=0,
                    collisions=[],
                    has_critical_conflicts=False,
                    is_clean=True,
                )
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
                        similarity_score=1.0,
                    )
                ],
                unremediated_count=0,
            )

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # File should be modified
            read_data = json.loads(config_path.read_text())
            assert read_data["mcpServers"]["vuln-server"]["args"] == ["vuln-pkg@1.1.0", "--some-flag"]
            
            # Backup should be created
            assert config_path.with_name("config.json.bak").exists()
            backup_data = json.loads(config_path.with_name("config.json.bak").read_text())
            assert backup_data["mcpServers"]["vuln-server"]["args"] == ["vuln-pkg@1.0.0", "--some-flag"]

def test_audit_config_fix_clean():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_data = {
            "mcpServers": {
                "safe-server": {
                    "command": "uvx",
                    "args": ["safe-pkg@2.0.0", "--some-flag"],
                }
            }
        }
        config_path.write_text(json.dumps(config_data))
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "audit-config",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--fix"
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.audit_client_config") as mock_audit,
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            from mcp_fingerprints.conflict_detector import ConflictAuditReport
            mock_audit.return_value = ConflictAuditReport(
                    servers_configured=[],
                    servers_matched_in_passports=[],
                    total_tools_exposed=0,
                    unique_tool_names=0,
                    collisions=[],
                    has_critical_conflicts=False,
                    is_clean=True,
                )
            mock_eval.return_value = RemediationReport(
                is_clean=True,
                actions=[],
                unremediated_count=0,
            )

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # File should not be modified
            read_data = json.loads(config_path.read_text())
            assert read_data["mcpServers"]["safe-server"]["args"] == ["safe-pkg@2.0.0", "--some-flag"]

def test_audit_config_fix_apply_replace():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        config_data = {
            "context_servers": {
                "vuln-server": {
                    "command": "uvx",
                    "args": ["vuln-pkg@1.0.0", "--some-flag"],
                }
            }
        }
        config_path.write_text(json.dumps(config_data))
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "audit-config",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--fix",
            "--strategy",
            "replace"
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.audit_client_config") as mock_audit,
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            from mcp_fingerprints.conflict_detector import ConflictAuditReport
            mock_audit.return_value = ConflictAuditReport(
                    servers_configured=[],
                    servers_matched_in_passports=[],
                    total_tools_exposed=0,
                    unique_tool_names=0,
                    collisions=[],
                    has_critical_conflicts=False,
                    is_clean=True,
                )
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
                        similarity_score=0.9,
                    )
                ],
                unremediated_count=0,
            )

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # File should be modified
            read_data = json.loads(config_path.read_text())
            assert read_data["context_servers"]["vuln-server"]["args"] == ["safe-pkg@2.0.0", "--some-flag"]

def test_audit_config_fix_preserves_comments():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_data = '''{
    // A comment
    "mcpServers": {
        "vuln-server": {
            "command": "uvx",
            "args": ["vuln-pkg@1.0.0", "--some-flag"] // Trailing comment
        }
    }
}'''
        config_path.write_text(config_data, encoding="utf-8")
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "audit-config",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--fix",
            "--backup"
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.audit_client_config") as mock_audit,
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            from mcp_fingerprints.conflict_detector import ConflictAuditReport
            mock_audit.return_value = ConflictAuditReport(
                servers_configured=[],
                servers_matched_in_passports=[],
                total_tools_exposed=0,
                unique_tool_names=0,
                collisions=[],
                has_critical_conflicts=False,
                is_clean=True,
            )
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
                        similarity_score=1.0,
                    )
                ],
                unremediated_count=0,
            )

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # File should be modified
            read_data = config_path.read_text(encoding="utf-8")
            assert "vuln-pkg@1.1.0" in read_data
            assert "// A comment" in read_data
            assert "// Trailing comment" in read_data
            
            # Backup should be created
            assert config_path.with_name("config.json.bak").exists()

def test_audit_config_fix_preserves_schema():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_data = '''{
    // A comment
    "context_servers": {
        "vuln-server": {
            "command": "uvx",
            "args": ["vuln-pkg@1.0.0", "--some-flag"] // Trailing comment
        }
    }
}'''
        config_path.write_text(config_data, encoding="utf-8")
        passport_dir = Path(tmpdir) / "fingerprints"
        passport_dir.mkdir()

        test_args = [
            "mcp-fingerprints",
            "audit-config",
            str(config_path),
            "--dir",
            str(passport_dir),
            "--fix",
            "--backup"
        ]

        with (
            patch("sys.argv", test_args),
            patch("mcp_fingerprints.cli.audit_client_config") as mock_audit,
            patch("mcp_fingerprints.cli.evaluate_client_config") as mock_eval,
        ):
            from mcp_fingerprints.conflict_detector import ConflictAuditReport
            mock_audit.return_value = ConflictAuditReport(
                servers_configured=[],
                servers_matched_in_passports=[],
                total_tools_exposed=0,
                unique_tool_names=0,
                collisions=[],
                has_critical_conflicts=False,
                is_clean=True,
            )
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
                        similarity_score=1.0,
                    )
                ],
                unremediated_count=0,
            )

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # File should be modified
            read_data = config_path.read_text(encoding="utf-8")
            assert "vuln-pkg@1.1.0" in read_data
            assert "context_servers" in read_data
            assert "// A comment" in read_data
            assert "// Trailing comment" in read_data
