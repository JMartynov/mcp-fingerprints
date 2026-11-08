import subprocess
import os
import pytest

@pytest.mark.integration
def test_demo_script_all():
    """Test that the demo.sh script runs successfully with --all in a sandbox."""
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo.sh"))
    assert os.path.exists(script_path)

    # Run the demo script with --all
    result = subprocess.run(
        ["bash", script_path, "--all"],
        capture_output=True,
        text=True
    )
    
    # Check that it exits cleanly
    assert result.returncode == 0
    assert "Demo Complete" in result.stdout
    assert "Cleaning up sandbox at" in result.stdout

    # Check for expected commands running in output
    assert "Executing:" in result.stdout
