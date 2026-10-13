import sys
from unittest.mock import patch

import pytest

from scripts.sync_embeddings import compute_fingerprints_hash, main


@pytest.fixture
def temp_env(tmp_path):
    passports_dir = tmp_path / "fingerprints"
    passports_dir.mkdir()
    (passports_dir / "test.json").write_text('{"package_name": "test"}')
    output_npz = tmp_path / "embeddings.npz"
    hash_file = tmp_path / ".embeddings_hash"
    
    with patch("sys.argv", ["sync_embeddings.py", 
                            "--passports-dir", str(passports_dir),
                            "--output", str(output_npz),
                            "--hash-file", str(hash_file)]):
        yield {
            "passports_dir": passports_dir,
            "output_npz": output_npz,
            "hash_file": hash_file
        }

def test_sync_embeddings_missing_deps(temp_env):
    with patch("scripts.sync_embeddings.HAS_DEPS", False):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0

@patch("scripts.sync_embeddings.build_index")
def test_sync_embeddings_success(mock_build_index, temp_env):
    with patch("scripts.sync_embeddings.HAS_DEPS", True):
        main()
        mock_build_index.assert_called_once_with(temp_env["passports_dir"], temp_env["output_npz"])
        assert temp_env["hash_file"].exists()

@patch("scripts.sync_embeddings.build_index")
def test_sync_embeddings_no_changes(mock_build_index, temp_env):
    with patch("scripts.sync_embeddings.HAS_DEPS", True):
        # Setup initial hash
        current_hash = compute_fingerprints_hash(temp_env["passports_dir"])
        temp_env["hash_file"].write_text(current_hash)
        
        # Make output npz exist
        temp_env["output_npz"].write_text("mock binary data")
        
        with pytest.raises(SystemExit) as exc:
            main()
        
        # It should exit gracefully
        assert exc.value.code == 0
        mock_build_index.assert_not_called()

@patch("scripts.sync_embeddings.build_index")
def test_sync_embeddings_force(mock_build_index, temp_env):
    with patch("scripts.sync_embeddings.HAS_DEPS", True):
        current_hash = compute_fingerprints_hash(temp_env["passports_dir"])
        temp_env["hash_file"].write_text(current_hash)
        temp_env["output_npz"].write_text("mock binary data")
        
        # Add --force to sys.argv
        sys.argv.append("--force")
        
        main()
        mock_build_index.assert_called_once()
