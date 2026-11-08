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


@pytest.mark.integration
def test_demo_script_help():
    """Test that demo.sh --help exits with 0 and prints usage options."""
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo.sh"))
    result = subprocess.run(
        ["bash", script_path, "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage: ./demo.sh [OPTIONS]" in result.stdout
    assert "--all" in result.stdout
    assert "--command" in result.stdout


@pytest.mark.integration
def test_demo_script_single_command():
    """Test that demo.sh --command version runs cleanly and exits 0."""
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo.sh"))
    result = subprocess.run(
        ["bash", script_path, "--command", "version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "mcp-fingerprints" in result.stdout
    assert "Cleanup complete." in result.stdout

