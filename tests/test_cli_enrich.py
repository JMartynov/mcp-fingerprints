import pytest
import argparse
from unittest.mock import patch, MagicMock
from mcp_fingerprints.cli import main

@patch("mcp_fingerprints.cli.argparse.ArgumentParser.parse_args")
@patch("mcp_fingerprints.cli.PassportSynchronizer")
@patch("mcp_fingerprints.cli.build_snapshot")
@patch("mcp_fingerprints.cli.print_ecosystem_health_report")
def test_sync_cli_args(mock_report, mock_build_snapshot, mock_synchronizer, mock_parse_args):
    # Setup mock arguments
    args = argparse.Namespace(
        command="sync",
        output="test_output",
        update_existing=False,
        discover_new=False,
        enrich_ast=True,
        limit=200,
        workers=4,
        all=False,
        snapshot=True,
        report=True
    )
    mock_parse_args.return_value = args
    
    mock_sync_instance = MagicMock()
    mock_synchronizer.return_value = mock_sync_instance
    
    main()
    
    mock_synchronizer.assert_called_once_with(output_dir="test_output")
    mock_sync_instance.enrich_zero_tool_passports.assert_called_once_with(limit=200, max_workers=4)
    mock_build_snapshot.assert_called_once()
    mock_report.assert_called_once_with("test_output")

@patch("mcp_fingerprints.cli.argparse.ArgumentParser.parse_args")
@patch("mcp_fingerprints.cli.PassportSynchronizer")
def test_sync_cli_default_args(mock_synchronizer, mock_parse_args):
    # Setup mock arguments
    args = argparse.Namespace(
        command="sync",
        output="data/fingerprints",
        update_existing=False,
        discover_new=False,
        enrich_ast=False,
        limit=500,
        workers=8,
        all=True,
        snapshot=False,
        report=False
    )
    mock_parse_args.return_value = args
    
    mock_sync_instance = MagicMock()
    mock_synchronizer.return_value = mock_sync_instance
    
    main()
    
    mock_synchronizer.assert_called_once_with(output_dir="data/fingerprints")
    mock_sync_instance.enrich_zero_tool_passports.assert_called_once_with(limit=500, max_workers=8)
    mock_sync_instance.discover_new_mcps.assert_called_once()
    mock_sync_instance.update_existing_passports.assert_called_once()
