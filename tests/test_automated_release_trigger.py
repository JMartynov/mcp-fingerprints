import os
import pytest
from pathlib import Path
import re
import sys

# Import bump_version dynamically from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import bump_version


def test_bump_version_logic(tmp_path):
    pyproject_toml = tmp_path / "pyproject.toml"
    pyproject_toml.write_text("""[project]
name = "mcp-fingerprints"
version = "1.0.0"
""")

    init_py = tmp_path / "__init__.py"
    init_py.write_text("""__version__ = "1.0.0"
""")

    # Test reading
    assert bump_version.get_current_version(str(pyproject_toml)) == "1.0.0"

    # Test bump logic
    assert bump_version.bump_patch_version("1.0.0") == "1.0.1"
    assert bump_version.bump_patch_version("2.1.3") == "2.1.4"
    assert bump_version.bump_patch_version("1.0.0a1") == "1.0.1"

    # Test applying
    bump_version.update_version_in_files("1.0.1", str(pyproject_toml), str(init_py))
    
    assert bump_version.get_current_version(str(pyproject_toml)) == "1.0.1"
    assert '__version__ = "1.0.1"' in init_py.read_text()


def test_bump_version_cli(tmp_path, capsys):
    pyproject_toml = tmp_path / "pyproject.toml"
    pyproject_toml.write_text("""[project]
name = "mcp-fingerprints"
version = "1.0.0"
""")

    init_py = tmp_path / "__init__.py"
    init_py.write_text("""__version__ = "1.0.0"
""")

    # Test --dry-run
    ret = bump_version.main(["--dry-run", "--pyproject", str(pyproject_toml), "--init-file", str(init_py)])
    assert ret == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "1.0.1"
    assert bump_version.get_current_version(str(pyproject_toml)) == "1.0.0"

    # Test --apply
    ret = bump_version.main(["--apply", "--pyproject", str(pyproject_toml), "--init-file", str(init_py)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Bumped version from 1.0.0 to 1.0.1" in captured.out
    assert bump_version.get_current_version(str(pyproject_toml)) == "1.0.1"
    assert '__version__ = "1.0.1"' in init_py.read_text()

    # Test error handling on missing file
    ret = bump_version.main(["--dry-run", "--pyproject", str(tmp_path / "nonexistent.toml")])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_repository_version_synchronization():
    repo_root = Path(__file__).parent.parent
    pyproject_toml = repo_root / "pyproject.toml"
    init_py = repo_root / "src" / "mcp_fingerprints" / "__init__.py"

    pyproject_ver = bump_version.get_current_version(str(pyproject_toml))
    
    content = init_py.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "Could not find __version__ in __init__.py"
    init_ver = match.group(1)

    assert pyproject_ver == init_ver, f"Version mismatch: pyproject.toml ({pyproject_ver}) vs __init__.py ({init_ver})"


def test_workflows_have_correct_triggers():
    repo_root = Path(__file__).parent.parent
    release_yml = repo_root / ".github" / "workflows" / "release.yml"
    daily_sync_yml = repo_root / ".github" / "workflows" / "daily_sync.yml"
    
    # Verify release.yml has workflow_call
    release_content = release_yml.read_text()
    assert "workflow_call:" in release_content
    
    # Verify daily_sync.yml has version bump and release logic
    daily_sync_content = daily_sync_yml.read_text()
    assert "scripts/bump_version.py --dry-run" in daily_sync_content
    assert "scripts/bump_version.py --apply" in daily_sync_content
    assert 'git tag "v${NEW_VERSION}"' in daily_sync_content
    assert 'gh release create' in daily_sync_content
    assert 'uses: ./.github/workflows/release.yml' in daily_sync_content
    assert "git status --porcelain data/fingerprints/" in daily_sync_content
    assert "release_created" in daily_sync_content
