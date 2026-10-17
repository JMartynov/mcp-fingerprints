from pathlib import Path
import json
import pytest

def test_passport_dataset_sanitization():
    """Verify all passport JSON files are sanitized of security profile and vulnerability keys."""
    data_dir = Path("data/fingerprints")
    passport_files = list(data_dir.glob("*.json"))
    assert len(passport_files) > 5000, f"Expected >5000 passports, found {len(passport_files)}"
    
    for f in passport_files:
        if f.name in ("sync_state.json", "index.json"):
            continue
        content = json.loads(f.read_text(encoding="utf-8"))
        assert "security_profile" not in content, f"Residual security_profile found in {f.name}"
        assert "vulnerabilities" not in content, f"Residual vulnerabilities found in {f.name}"
        assert "cve" not in content, f"Residual cve found in {f.name}"
        assert "cves" not in content, f"Residual cves found in {f.name}"
        assert "advisories" not in content, f"Residual advisories found in {f.name}"

def test_sync_state_blacklist_reset():
    """Verify stalled zero-tool blacklist arrays in sync_state.json exist as valid lists."""
    sync_state_path = Path("data/fingerprints/sync_state.json")
    assert sync_state_path.exists()
    sync_data = json.loads(sync_state_path.read_text(encoding="utf-8"))
    assert isinstance(sync_data.get("ast_probed_repos"), list)
    assert isinstance(sync_data.get("npm_probed_packages"), list)
    assert isinstance(sync_data.get("pypi_probed_packages"), list)

def test_documentation_purification():
    """Verify README.md and docs/SPECIFICATION.md contain zero mentions of deprecated security terms."""
    forbidden = ["vulnerability", "cve", "risk_tier", "security_classifier", "audit-config"]
    for doc in [Path("README.md"), Path("docs/SPECIFICATION.md")]:
        assert doc.exists(), f"{doc} must exist"
        text = doc.read_text(encoding="utf-8").lower()
        for term in forbidden:
            assert term not in text, f"Forbidden term '{term}' found in {doc}"
