import pytest
from unittest.mock import patch, MagicMock
from mcp_fingerprints.sandbox_drivers import (
    DockerSandboxRunner,
    IncusSandboxRunner,
    HostSandboxRunner,
    AutoSandboxRunner,
    get_sandbox_runner
)

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
@patch("mcp_fingerprints.sandbox_drivers.probe_mcp_server_stdio")
def test_docker_command_construction(mock_probe, mock_which):
    mock_which.return_value = "/usr/bin/docker"
    mock_probe.return_value = [{"name": "test_tool", "description": "test", "inputSchema": {}}]
    
    runner = DockerSandboxRunner()
    result = runner.run_handshake(["my-image", "npm", "start"], timeout=5.0)
    
    assert len(result) == 1
    mock_probe.assert_called_once()
    args, kwargs = mock_probe.call_args
    cmd = args[0]
    
    # Assert Docker command line string specifically
    assert cmd[:8] == ["docker", "run", "-i", "--rm", "--network", "none", "--memory", "512m"]
    assert cmd[8] == "my-image"
    assert cmd[9:] == ["npm", "start"]
    assert kwargs.get("timeout_seconds") == 5.0

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
def test_docker_missing_binary(mock_which):
    mock_which.return_value = None
    runner = DockerSandboxRunner()
    
    with pytest.raises(EnvironmentError, match="docker CLI not found in PATH"):
        runner.run_handshake(["test-image"])

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
@patch("mcp_fingerprints.sandbox_drivers.subprocess.run")
@patch("mcp_fingerprints.sandbox_drivers.probe_mcp_server_stdio")
def test_incus_command_construction(mock_probe, mock_run, mock_which):
    mock_which.return_value = "/usr/bin/incus"
    mock_probe.return_value = [{"name": "tool"}]
    
    runner = IncusSandboxRunner(is_vm=False)
    result = runner.run_handshake(["my-image", "npm", "start"], timeout=5.0)
    
    assert len(result) == 1
    
    # Check subprocess.run for launch
    assert mock_run.call_count >= 1
    launch_call = mock_run.call_args_list[0]
    launch_cmd = launch_call[0][0]
    assert launch_cmd[0:3] == ["incus", "launch", "docker:my-image"]
    assert "--ephemeral" in launch_cmd
    assert "-c" in launch_cmd
    assert "limits.memory=512MB" in launch_cmd
    assert "limits.cpu=1" in launch_cmd
    assert "--vm" not in launch_cmd
    
    instance_name = launch_cmd[3]
    
    # Check probe execution
    mock_probe.assert_called_once()
    probe_args, _ = mock_probe.call_args
    exec_cmd = probe_args[0]
    assert exec_cmd == ["incus", "exec", instance_name, "--", "npm", "start"]

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
@patch("mcp_fingerprints.sandbox_drivers.subprocess.run")
@patch("mcp_fingerprints.sandbox_drivers.probe_mcp_server_stdio")
def test_incus_vm_command_construction(mock_probe, mock_run, mock_which):
    mock_which.return_value = "/usr/bin/incus"
    mock_probe.return_value = [{"name": "tool"}]
    
    runner = IncusSandboxRunner(is_vm=True)
    runner.run_handshake(["my-image", "npm", "start"], timeout=5.0)
    
    launch_call = mock_run.call_args_list[0]
    launch_cmd = launch_call[0][0]
    assert "--vm" in launch_cmd

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
def test_auto_sandbox_fallback(mock_which):
    # Test fallback: no incus, no docker -> host
    mock_which.return_value = None
    runner = get_sandbox_runner("auto")
    
    with patch("mcp_fingerprints.sandbox_drivers.HostSandboxRunner.run_handshake") as mock_host:
        runner.run_handshake(["test"])
        mock_host.assert_called_once()

    # Test fallback: docker available
    def which_side_effect(binary):
        if binary == "docker":
            return "/usr/bin/docker"
        return None
    mock_which.side_effect = which_side_effect
    
    runner = get_sandbox_runner("auto")
    with patch("mcp_fingerprints.sandbox_drivers.DockerSandboxRunner.run_handshake") as mock_docker:
        runner.run_handshake(["test"])
        mock_docker.assert_called_once()
        
    # Test fallback: incus available
    def which_side_effect_incus(binary):
        if binary == "incus":
            return "/usr/bin/incus"
        return None
    mock_which.side_effect = which_side_effect_incus
    
    runner = get_sandbox_runner("auto")
    with patch("mcp_fingerprints.sandbox_drivers.IncusSandboxRunner.run_handshake") as mock_incus:
        runner.run_handshake(["test"])
        mock_incus.assert_called_once()

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
def test_incus_missing_binary(mock_which):
    mock_which.return_value = None
    runner = IncusSandboxRunner()
    with pytest.raises(EnvironmentError, match="incus CLI not found in PATH"):
        runner.run_handshake(["test-image"])

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
@patch("mcp_fingerprints.sandbox_drivers.probe_mcp_server_stdio")
def test_docker_timeout_handling(mock_probe, mock_which):
    mock_which.return_value = "/usr/bin/docker"
    mock_probe.return_value = []
    runner = DockerSandboxRunner()
    result = runner.run_handshake(["test-image"], timeout=1.0)
    assert result == []
    mock_probe.assert_called_once()
    _, kwargs = mock_probe.call_args
    assert kwargs.get("timeout_seconds") == 1.0

@patch("mcp_fingerprints.sandbox_drivers.shutil.which")
@patch("mcp_fingerprints.sandbox_drivers.subprocess.run")
def test_incus_timeout_handling(mock_run, mock_which):
    import subprocess
    mock_which.return_value = "/usr/bin/incus"
    mock_run.side_effect = subprocess.TimeoutExpired(cmd=["incus", "launch"], timeout=1.0)
    runner = IncusSandboxRunner()
    result = runner.run_handshake(["test-image"], timeout=1.0)
    assert result == []
