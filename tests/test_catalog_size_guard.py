"""Guard: web/catalog.json must stay below GitHub's 50MB hard-warning limit and workflows stay valid."""

from pathlib import Path

MAX_BYTES = 50 * 1024 * 1024


def test_web_catalog_under_50mb():
    path = Path("web/catalog.json")
    assert path.exists(), "web/catalog.json should exist"
    assert path.stat().st_size < MAX_BYTES, f"catalog.json is {path.stat().st_size} bytes"


def test_daily_sync_dispatch_payload_keys():
    text = Path(".github/workflows/daily_sync.yml").read_text(encoding="utf-8")
    assert "upstream_version" in text
    assert "passports_count" in text
    assert "fingerprints_version" not in text
    assert "upstream_fingerprints_updated" in text
    assert "JMartynov/mcp-vulnerabilities" in text
    assert "JMartynov/verityredteam-free" in text
    assert "JMartynov/verityredteam" in text
    assert "REPO_DISPATCH_PAT" in text
    assert "curl -fsSL" in text


def test_e2e_workflow_has_ruff_and_catalog_guard():
    text = Path(".github/workflows/e2e.yml").read_text(encoding="utf-8")
    assert "ruff check src tests scripts --select E9,F63,F7,F82" in text
    assert "52428800" in text
    assert "wc -c < web/catalog.json" in text
