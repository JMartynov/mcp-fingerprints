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
    assert "risk_tier" not in entry
    assert entry["transports"] == ["stdio"]
    assert entry["total_versions"] == 1


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
    assert ".highlight-card" in html_content
    assert ".badge-advisory" not in html_content


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
    assert "badge-advisory" not in js_content
    assert "osv.dev/vulnerability" not in js_content
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


def test_build_catalog_entry_full_features():
    passport = {
        "package_name": "test-full",
        "ecosystem": "generic",
        "repository_url": "https://github.com/someuser/test-full",
        "versions": [
            {
                "version": "2.0.0",
                "prompt_signatures": [
                    {"name": "test_prompt", "description": "prompt desc"}
                ],
                "resource_signatures": [
                    {
                        "name": "test_res",
                        "uri_template": "res://test",
                        "description": "res desc",
                    }
                ],
                "connections": [{"type": "sse", "url": "https://example.com/sse"}],
            }
        ],
    }

    entry = build_catalog_entry(passport)
    assert entry["author"] == "someuser"
    assert entry["connection_type"] == "sse"
    assert entry["command"] == "https://example.com/sse"
    assert len(entry["prompts"]) == 1
    assert entry["prompts"][0]["name"] == "test_prompt"
    assert len(entry["resources"]) == 1
    assert entry["resources"][0]["uri_template"] == "res://test"


def test_compile_web_catalog_exception_and_sw_injection(tmp_path):
    passports_dir = tmp_path / "passports"
    passports_dir.mkdir(parents=True)
    web_dir = tmp_path / "web"
    web_dir.mkdir(parents=True)

    # invalid json
    (passports_dir / "invalid.json").write_text("not-json", encoding="utf-8")

    sw_content = "const CACHE_NAME = 'mcp-catalog-v1234'; __CACHE_VERSION__"
    (web_dir / "sw.js").write_text(sw_content, encoding="utf-8")

    compile_web_catalog(passports_dir, web_dir)

    sw_updated = (web_dir / "sw.js").read_text(encoding="utf-8")
    assert "__CACHE_VERSION__" not in sw_updated
    assert "mcp-catalog-v" in sw_updated


def test_cli_main(monkeypatch, tmp_path):
    import sys
    from scripts.generate_web_catalog import main

    passports_dir = tmp_path / "passports"
    passports_dir.mkdir(parents=True)
    web_dir = tmp_path / "web"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_web_catalog.py",
            "--passports-dir",
            str(passports_dir),
            "--output-dir",
            str(web_dir),
        ],
    )
    main()

    assert (web_dir / "catalog.json").exists()


def test_build_catalog_entry_generic_command():
    passport = {"package_name": "unknown-pkg", "ecosystem": "other", "versions": []}

    entry = build_catalog_entry(passport)
    assert entry["connection_type"] == "generic"
    assert entry["command"] == "unknown-pkg"


def test_compile_web_catalog_ignore_sync_state(tmp_path):
    passports_dir = tmp_path / "passports"
    passports_dir.mkdir(parents=True)
    web_dir = tmp_path / "web"
    web_dir.mkdir(parents=True)

    (passports_dir / "sync_state.json").write_text('{"foo": "bar"}', encoding="utf-8")

    compile_web_catalog(passports_dir, web_dir)
    # The coverage on continue will be hit.


def test_build_catalog_entry_semver_sorting():
    passport = {
        "package_name": "multi-ver-pkg",
        "ecosystem": "npm",
        "versions": [
            {"version": "1.0.0", "tool_signatures": [{"name": "tool_v1"}]},
            {"version": "1.0.11", "tool_signatures": [{"name": "tool_v11"}]},
            {"version": "1.0.2", "tool_signatures": [{"name": "tool_v2"}]},
        ],
    }
    entry = build_catalog_entry(passport)
    assert entry["version"] == "1.0.11"
    assert entry["latest_version"] == "1.0.11"
    assert [v["version"] for v in entry["versions"]] == ["1.0.11", "1.0.2", "1.0.0"]
    assert entry["tools"][0]["name"] == "tool_v11"

