import sys
import unittest.mock
from pathlib import Path
import json
import pytest

from mcp_fingerprints.hub import (
    ActionRegistry, ActionItem, setup_default_registry, run_interactive_hub, get_status_header, save_baseline
)

def test_action_registry():
    reg = ActionRegistry()
    
    mock_handler = unittest.mock.Mock()
    reg.register("Cat 1", "🐱", "Meow", mock_handler, order=10)
    reg.register("Cat 2", "🐶", "Woof", mock_handler, order=5)
    
    cats = reg.get_categories()
    assert cats == ["Cat 2", "Cat 1"]
    
    actions = reg.get_actions("Cat 1")
    assert len(actions) == 1
    assert actions[0].title == "Meow"

@unittest.mock.patch('sys.stdin.isatty', return_value=True)
@unittest.mock.patch('builtins.input', side_effect=['5'])
def test_run_interactive_hub_exit(mock_input, mock_isatty):
    # Just selecting 5 (Exit)
    run_interactive_hub()
    mock_input.assert_called_once()

@unittest.mock.patch('sys.stdin.isatty', return_value=False)
def test_run_interactive_hub_notty(mock_isatty, capsys):
    with pytest.raises(SystemExit) as e:
        run_interactive_hub()
    
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "Interactive mode requires a TTY" in captured.out

@unittest.mock.patch('mcp_fingerprints.hub.config_scanner.ConfigScanner')
def test_get_status_header(mock_scanner):
    mock_instance = unittest.mock.Mock()
    mock_report = unittest.mock.Mock()
    mock_report.servers = [
        {"server_name": "test1", "client_path": "path1"},
        {"server_name": "test2", "client_path": "path2"},
        {"server_name": "test3", "client_path": "path1"}
    ]
    mock_instance.scan.return_value = mock_report
    mock_scanner.return_value = mock_instance
    
    header = get_status_header()
    assert "Paths Scanned: 2" in header
    assert "Total MCP Servers Configured: 3" in header

@unittest.mock.patch('mcp_fingerprints.hub.config_scanner.ConfigScanner')
def test_save_baseline(mock_scanner, tmp_path):
    mock_instance = unittest.mock.Mock()
    mock_report = unittest.mock.Mock()
    mock_report.servers = [
        {"server_name": "test1", "client_path": "path1"}
    ]
    mock_instance.scan.return_value = mock_report
    mock_scanner.return_value = mock_instance
    
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_file:
        save_baseline()
        mock_file.assert_called_once_with("workstation_baseline.json", "w", encoding="utf-8")
        
        # Check written data
        handle = mock_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written)
        assert data["snapshot_version"] == "1.0.0"
        assert len(data["servers"]) == 1
        assert data["servers"][0]["server_name"] == "test1"


@unittest.mock.patch('mcp_fingerprints.hub.config_scanner.ConfigScanner')
@unittest.mock.patch('mcp_fingerprints.hub.os.path.exists', return_value=True)
def test_diff_baseline(mock_exists, mock_scanner, capsys):
    from mcp_fingerprints.hub import diff_baseline
    
    mock_instance = unittest.mock.Mock()
    mock_report = unittest.mock.Mock()
    mock_report.servers = [
        {"server_name": "test1", "client_path": "path1"}
    ]
    mock_instance.scan.return_value = mock_report
    mock_scanner.return_value = mock_instance
    
    # Baseline with test2 instead of test1
    mock_baseline = {
        "snapshot_version": "1.0.0",
        "timestamp": "2023-10-25T12:00:00",
        "servers": [
            {"server_name": "test2", "client_name": "path2"}
        ]
    }
    
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(mock_baseline))):
        diff_baseline()
        
    captured = capsys.readouterr()
    assert "Added servers: 1" in captured.out
    assert "test1 (path1)" in captured.out
    assert "Removed servers: 1" in captured.out
    assert "test2 (path2)" in captured.out


@unittest.mock.patch('sys.stdin.isatty', return_value=True)
@unittest.mock.patch('builtins.input', side_effect=['1', '2', 'path/to/test.json', '2', 'test_results.json', '5'])
@unittest.mock.patch('mcp_fingerprints.hub.config_scanner.ConfigScanner')
def test_scan_and_save(mock_scanner, mock_input, mock_isatty):
    mock_instance = unittest.mock.Mock()
    mock_report = unittest.mock.Mock()
    mock_report.servers = [
        {"server_name": "test1", "client_path": "path1"}
    ]
    mock_instance.scan.return_value = mock_report
    mock_scanner.return_value = mock_instance
    
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_file:
        run_interactive_hub()
        
        mock_file.assert_called_once_with("test_results.json", "w", encoding="utf-8")
        handle = mock_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written)
        assert len(data) == 1
        assert data[0]["server_name"] == "test1"


@unittest.mock.patch('sys.stdin.isatty', return_value=True)
@unittest.mock.patch('builtins.input', side_effect=['1', '1', '1', '5'])
@unittest.mock.patch('mcp_fingerprints.hub.config_scanner.ConfigScanner')
def test_scan_and_diff_missing(mock_scanner, mock_input, mock_isatty, capsys):
    mock_instance = unittest.mock.Mock()
    mock_report = unittest.mock.Mock()
    mock_report.servers = [
        {"server_name": "test1", "client_path": "path1"}
    ]
    mock_instance.scan.return_value = mock_report
    mock_scanner.return_value = mock_instance
    
    run_interactive_hub()
        
    captured = capsys.readouterr()
    assert "- test1 (path1)" in captured.out

