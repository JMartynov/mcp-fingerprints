import pytest
from unittest.mock import patch
from mcp_fingerprints.cli import main


def test_cli_scan_configs_drift(capsys, tmp_path):
    import mcp_fingerprints.snapshot_diff as snapshot_diff

    # We create a dummy baseline and a dummy current
    baseline_path = tmp_path / "baseline.json"

    server_old = snapshot_diff.DiscoveredServer("s1", "c1", version="1.0")
    baseline = snapshot_diff.InventorySnapshot(servers=[server_old])
    baseline.save(baseline_path)

    server_new = snapshot_diff.DiscoveredServer("s1", "c1", version="2.0")
    current = snapshot_diff.InventorySnapshot(servers=[server_new])

    # We patch sys.argv and scan_local_configs
    test_args = [
        "mcp-fingerprints",
        "scan-configs",
        "--compare-snapshot",
        str(baseline_path),
        "--fail-on-drift",
    ]

    with patch("sys.argv", test_args):
        # We need to ensure the mocked scan_local_configs returns our current
        import mcp_fingerprints

        with patch.object(
            mcp_fingerprints, "scan_local_configs", create=True
        ) as mock_scan:
            mock_scan.return_value = current
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 2

    # Check output
    captured = capsys.readouterr()
    assert "Result: 0 server(s) added, 1 server(s) drifted." in captured.out
