import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from mcp_fingerprints.hub import setup_default_registry, export_sbom_hub
from mcp_fingerprints.tui import MCPCatalogBrowser


@pytest.fixture
def dummy_data_dir(tmp_path):
    data_dir = tmp_path / "data" / "fingerprints"
    data_dir.mkdir(parents=True, exist_ok=True)
    passport_data = {
        "package_name": "test-pkg",
        "ecosystem": "NPM",
        "purl": "pkg:npm/test-pkg",
        "versions": [
            {
                "version": "1.0.0",
                "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "tool_signatures": [
                    {"name": "test-tool"}
                ]
            }
        ]
    }
    (data_dir / "test.json").write_text(json.dumps(passport_data), encoding="utf-8")
    return data_dir

def test_hub_registry_contains_sbom_action():
    registry = setup_default_registry()
    category = "🌐 2. Search Ready Database & Ingest Unknown Local MCPs"
    actions = registry.get_actions(category)
    
    sbom_action = next((a for a in actions if a.title == "Export CycloneDX 1.6 SBOM for Server / Catalog"), None)
    
    assert sbom_action is not None, "SBOM export action not registered in the correct category"
    assert sbom_action.emoji == "📦"
    assert sbom_action.handler == export_sbom_hub
    assert sbom_action.order == 75

@patch("mcp_fingerprints.hub.prompt_choice")
@patch("mcp_fingerprints.hub.prompt_input")
@patch("mcp_fingerprints.hub.Path")
def test_export_sbom_hub_entire_catalog(mock_path, mock_input, mock_choice, tmp_path, dummy_data_dir):
    out_file = tmp_path / "test_catalog_sbom.cdx.json"
    
    mock_choice.return_value = "Entire Catalog Snapshot"
    mock_input.return_value = str(out_file)

    original_path = Path
    def mocked_path(arg, *args, **kwargs):
        if str(arg) == "data/fingerprints":
            return dummy_data_dir
        if str(arg) == str(out_file):
            return original_path(out_file)
        return original_path(arg, *args, **kwargs)
        
    mock_path.side_effect = mocked_path
    
    export_sbom_hub()
    
    assert out_file.exists(), "Output file was not created"
    content = json.loads(out_file.read_text(encoding="utf-8"))
    assert content["bomFormat"] == "CycloneDX"
    assert content["specVersion"] == "1.6"
    assert len(content["components"]) > 0
    assert content["components"][0]["name"] == "test-pkg"


class DummyStdscr:
    def __init__(self, key_sequence):
        self.key_sequence = key_sequence
        self.idx = 0
        self.cleared = False
        self.refreshed = False
        
    def clear(self):
        self.cleared = True
        
    def getmaxyx(self):
        return (24, 80)
        
    def addstr(self, *args, **kwargs):
        pass
        
    def refresh(self):
        self.refreshed = True
        
    def getch(self):
        if self.idx < len(self.key_sequence):
            ch = self.key_sequence[self.idx]
            self.idx += 1
            return ch
        return ord('q')
        
    def timeout(self, val):
        pass
        
    def attron(self, val):
        pass
        
    def attroff(self, val):
        pass

@patch("mcp_fingerprints.tui.copy_to_clipboard")
def test_tui_sbom_export_keybinding(mock_copy, dummy_data_dir, tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        stdscr = DummyStdscr([ord('e'), ord('q')])
        
        browser = MCPCatalogBrowser(stdscr, dummy_data_dir)
        browser.is_test = True
        
        assert len(browser.filtered_passports) == 1
        
        browser.run()
        
        expected_file = Path("export_test-pkg_cyclonedx.json")
        assert expected_file.exists(), f"File {expected_file} was not created. Error: {browser.status_message}"
        
        content = json.loads(expected_file.read_text(encoding="utf-8"))
        assert content["bomFormat"] == "CycloneDX"
        
        assert "Exported CycloneDX SBOM" in browser.status_message
        mock_copy.assert_called_once()
        
    finally:
        os.chdir(original_cwd)
