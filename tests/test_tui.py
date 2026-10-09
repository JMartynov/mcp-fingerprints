import json
from unittest.mock import MagicMock, patch

import pytest

from mcp_fingerprints.tui import MCPCatalogBrowser, run_tui


@pytest.fixture
def mock_data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()

    p1 = {
        "package_name": "test-npm-pkg",
        "ecosystem": "npm",
        "description": "A test npm package",
        "versions": [
            {
                "version": "1.0.0",
                "tool_signatures": [{"name": "npm_tool_1", "description": "tool desc"}],
            }
        ],
    }

    p2 = {
        "package_name": "test-pypi-pkg",
        "ecosystem": "pypi",
        "description": "A test pypi package",
        "versions": [
            {
                "version": "2.0.0",
                "tool_signatures": [
                    {"name": "pypi_tool_1", "description": "pypi tool"}
                ],
            }
        ],
    }

    (d / "p1.json").write_text(json.dumps(p1))
    (d / "p2.json").write_text(json.dumps(p2))

    return d


class MockStdScr:
    def __init__(self):
        self.output = []
        self.height = 24
        self.width = 80

    def clear(self):
        self.output = []

    def getmaxyx(self):
        return self.height, self.width

    def addstr(self, y, x, text, attr=0):
        self.output.append((y, x, text, attr))

    def refresh(self):
        pass

    def timeout(self, t):
        pass

    def attron(self, attr):
        pass

    def attroff(self, attr):
        pass


def test_tui_initialization_and_filtering(mock_data_dir):
    stdscr = MockStdScr()
    browser = MCPCatalogBrowser(stdscr, mock_data_dir, initial_query="")

    assert len(browser.all_passports) == 2
    assert len(browser.filtered_passports) == 2

    # Filter by PyPI
    browser.current_tab = 2  # 0=All, 1=NPM, 2=PyPI, 3=GitHub
    browser.apply_filters()
    assert len(browser.filtered_passports) == 1
    assert browser.filtered_passports[0]["package_name"] == "test-pypi-pkg"

    # Filter by search
    browser.current_tab = 0
    browser.query = "npm_tool"
    browser.apply_filters()
    assert len(browser.filtered_passports) == 1
    assert browser.filtered_passports[0]["package_name"] == "test-npm-pkg"


def test_tui_drawing(mock_data_dir):
    stdscr = MockStdScr()
    browser = MCPCatalogBrowser(stdscr, mock_data_dir, initial_query="")

    browser.draw()
    # Find "test-npm-pkg" in output
    found = False
    for item in stdscr.output:
        if "test-npm-pkg" in item[2]:
            found = True
            break
    assert found


@patch("mcp_fingerprints.tui.copy_to_clipboard")
@patch("mcp_fingerprints.tui.export_client_config")
def test_tui_copy_config(mock_export, mock_copy, mock_data_dir):
    mock_export.return_value = {"mock": "config"}
    mock_copy.return_value = True

    stdscr = MockStdScr()
    browser = MCPCatalogBrowser(stdscr, mock_data_dir, initial_query="")

    # Select first item
    browser.selected_index = 0
    browser.filtered_passports = browser.all_passports

    # Simulate 'c'
    ch = ord("c")

    # Since run() has a while loop, let's just trigger the 'c' logic directly to test the event machine, or mock getch
    # We'll just copy the logic or use a mocked run with a patched getch
    stdscr.getch = MagicMock(side_effect=[ch, ord("q")])

    browser.run()

    mock_export.assert_called_once()
    mock_copy.assert_called_once()
    assert "mock" in mock_copy.call_args[0][0]


@patch("curses.wrapper")
def test_run_tui(mock_wrapper, mock_data_dir):
    run_tui(mock_data_dir, "test")
    mock_wrapper.assert_called_once()
