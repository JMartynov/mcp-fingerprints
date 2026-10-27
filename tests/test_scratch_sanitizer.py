import os
import subprocess
import tempfile
import pytest
from pathlib import Path

def test_scratch_sanitizer_cleans_and_preserves():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some allowed files and directories
        (temp_path / "src").mkdir()
        (temp_path / "src" / "main.py").touch()
        (temp_path / "tests").mkdir()
        (temp_path / "tests" / "test_main.py").touch()
        (temp_path / "docs").mkdir()
        (temp_path / "docs" / "readme.md").touch()
        (temp_path / "data").mkdir()
        (temp_path / "data" / "info.json").touch()
        
        # Create some scratch/temporary files
        (temp_path / "test_experiment.py").touch()
        (temp_path / "tmp_data.py").touch()
        (temp_path / "scratch_test.py").touch()
        (temp_path / "main_scratch.py").touch()
        (temp_path / "module_test.py").touch()
        (temp_path / "helper_tmp.py").touch()
        (temp_path / "script_debug.py").touch()
        
        (temp_path / "tmp").mkdir()
        (temp_path / "tmp" / "tempfile.txt").touch()
        (temp_path / "scratch").mkdir()
        (temp_path / "scratch" / "data.json").touch()
        
        # Resolve the path to the script
        script_path = Path(__file__).parent.parent / "bin" / "sanitize-scratch-files.sh"
        
        # Run the script
        result = subprocess.run([str(script_path)], cwd=temp_dir, capture_output=True, text=True)
        assert result.returncode == 0
        
        # Verify valid files were preserved
        assert (temp_path / "src" / "main.py").exists()
        assert (temp_path / "tests" / "test_main.py").exists()
        assert (temp_path / "docs" / "readme.md").exists()
        assert (temp_path / "data" / "info.json").exists()
        
        # Verify scratch files in root were removed
        assert not (temp_path / "test_experiment.py").exists()
        assert not (temp_path / "tmp_data.py").exists()
        assert not (temp_path / "scratch_test.py").exists()
        assert not (temp_path / "main_scratch.py").exists()
        assert not (temp_path / "module_test.py").exists()
        assert not (temp_path / "helper_tmp.py").exists()
        assert not (temp_path / "script_debug.py").exists()
        
        # Verify tmp/ and scratch/ directories were emptied
        assert (temp_path / "tmp").exists()
        assert not list((temp_path / "tmp").iterdir())
        assert (temp_path / "scratch").exists()
        assert not list((temp_path / "scratch").iterdir())
