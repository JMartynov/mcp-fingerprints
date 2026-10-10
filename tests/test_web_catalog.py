"""Unit tests for the Static Web Catalog Generator."""

import json
from pathlib import Path

from scripts.generate_web_catalog import build_catalog_entry, compile_web_catalog


def test_build_catalog_entry_npm():
    passport = {
        "security_profile": {
            "highest_risk_tier": "low",
            "advisories": [{"id": "CVE-2024-1234", "severity": "HIGH"}],
        },
        "package_name": "@org/sample-mcp",
        "ecosystem": "npm",
        "description": "Sample MCP server for testing",
        "versions": [
            {
                "version": "1.2.0",
                "tool_signatures": [
                    {"name": "tool_one", "description": "Does something useful"}
                ],
                "connections": [
                    {"type": "stdio", "command": "node", "args": ["dist/index.js"]}
                ],
                "capabilities": {"runtime_verified": True},
            }
        ],
    }

    entry = build_catalog_entry(passport)
    assert entry["name"] == "@org/sample-mcp"
    assert entry["ecosystem"] == "npm"
    assert entry["version"] == "1.2.0"
    assert entry["tool_count"] == 1
    assert entry["tools"][0]["name"] == "tool_one"
    assert entry["command"] == "node dist/index.js"
    assert entry["is_verified"] is True
    assert entry["advisory_count"] == 1
    assert entry["advisories"][0]["id"] == "CVE-2024-1234"
    assert entry["risk_tier"] == "high"


def test_compile_web_catalog(tmp_path):
    passports_dir = tmp_path / "passports"
    passports_dir.mkdir(parents=True)
    web_dir = tmp_path / "web"

    p1 = {
        "package_name": "pkg-a",
        "ecosystem": "pypi",
        "versions": [{"version": "1.0.0", "tool_signatures": [{"name": "tool_a"}]}],
    }
    p2 = {
        "package_name": "pkg-b",
        "ecosystem": "npm",
        "versions": [
            {
                "version": "1.0.0",
                "tool_signatures": [{"name": "tool_b1"}, {"name": "tool_b2"}],
            }
        ],
    }

    (passports_dir / "p1.json").write_text(json.dumps(p1), encoding="utf-8")
    (passports_dir / "p2.json").write_text(json.dumps(p2), encoding="utf-8")

    catalog_file = compile_web_catalog(passports_dir, web_dir)
    assert catalog_file.is_file()

    catalog_data = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert len(catalog_data) == 2
    # pkg-b has 2 tools, pkg-a has 1 tool; pkg-b should be sorted first
    assert catalog_data[0]["name"] == "pkg-b"
    assert catalog_data[1]["name"] == "pkg-a"


def test_web_index_html_exists_and_valid():
    index_file = Path("web/index.html")
    assert index_file.is_file()
    html_content = index_file.read_text(encoding="utf-8")
    assert "<title>MCP Passports & Server Directory</title>" in html_content
    assert 'id="searchInput"' in html_content
    assert 'id="serverGrid"' in html_content
    assert "app.js" in html_content


def test_web_index_html_css_classes():
    index_file = Path("web/index.html")
    assert index_file.is_file()
    html_content = index_file.read_text(encoding="utf-8")
    assert ".badge-advisory" in html_content
    assert ".highlight-card" in html_content


def test_web_index_html_multi_server_ui_elements():
    index_file = Path("web/index.html")
    assert index_file.is_file()
    html_content = index_file.read_text(encoding="utf-8")
    assert 'id="bottomDrawer"' in html_content
    assert 'id="selectedCount"' in html_content
    assert 'id="btnBuild"' in html_content
    assert 'id="configModal"' in html_content
    assert 'id="collisionWarning"' in html_content
    assert 'id="configOutput"' in html_content


def test_web_app_js_deep_linking_logic():
    app_file = Path("web/app.js")
    assert app_file.is_file()
    js_content = app_file.read_text(encoding="utf-8")
    assert "URLSearchParams" in js_content
    assert "history.replaceState" in js_content
    assert "window.location.search" in js_content
    assert "badge-advisory" in js_content
    assert "osv.dev/vulnerability" in js_content
    assert "copyShareLink" in js_content


def test_web_app_js_multi_server_logic():
    app_file = Path("web/app.js")
    assert app_file.is_file()
    js_content = app_file.read_text(encoding="utf-8")
    assert "let selectedServers = new Map();" in js_content
    assert "function toggleSelection(name)" in js_content
    assert "function detectCollisions()" in js_content
    assert "function generateCombinedConfig(client)" in js_content
    assert "mcpServers[safeKey] = { command, args };" in js_content
    assert "downloadCombinedConfig" in js_content
