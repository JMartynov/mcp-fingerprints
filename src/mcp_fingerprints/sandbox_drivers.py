import abc
import os
import shutil
import uuid
import subprocess
import time
from typing import Any
from mcp_fingerprints.runtime_sandbox import probe_mcp_server_stdio, sanitize_environment

class BaseSandboxRunner(abc.ABC):
    def wrap_command(self, command: list[str]) -> list[str]:
        """Wrap the original command in the necessary sandbox execution command."""
        return command
        
    def prepare(self, command: list[str], timeout: float = 5.0) -> Any:
        """Perform any necessary pre-launch setup (like incus launch) and return a cleanup callback or None."""
        return None

    @abc.abstractmethod
    def run_handshake(
        self, command: list[str], timeout: float = 5.0, env: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        pass

class HostSandboxRunner(BaseSandboxRunner):
    def run_handshake(
        self, command: list[str], timeout: float = 5.0, env: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        return probe_mcp_server_stdio(command, env=env, timeout_seconds=timeout)

class DockerSandboxRunner(BaseSandboxRunner):
    def wrap_command(self, command: list[str]) -> list[str]:
        if not shutil.which("docker"):
            raise EnvironmentError("docker CLI not found in PATH")
        image = command[0]
        cmd_args = command[1:]
        return [
            "docker", "run", "-i", "--rm", "--network", "none", "--memory", "512m",
            image
        ] + cmd_args

    def run_handshake(
        self, command: list[str], timeout: float = 5.0, env: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        docker_cmd = self.wrap_command(command)
        return probe_mcp_server_stdio(docker_cmd, env=env, timeout_seconds=timeout)

class IncusSandboxRunner(BaseSandboxRunner):
    def __init__(self, is_vm: bool = False):
        self.is_vm = is_vm
        self._instance_name = None

    def prepare(self, command: list[str], timeout: float = 5.0) -> Any:
        if not shutil.which("incus"):
            raise EnvironmentError("incus CLI not found in PATH")
        
        image = command[0]
        self._instance_name = f"mcp-probe-{uuid.uuid4().hex[:8]}"
        
        launch_cmd = [
            "incus", "launch", f"docker:{image}", self._instance_name,
            "--ephemeral", "-c", "limits.memory=512MB", "-c", "limits.cpu=1"
        ]
        if self.is_vm:
            launch_cmd.append("--vm")
            
        subprocess.run(launch_cmd, check=True, capture_output=True, timeout=timeout)
        
        def cleanup():
            if self._instance_name:
                try:
                    subprocess.run(["incus", "delete", "-f", self._instance_name], check=False, capture_output=True)
                except Exception:
                    pass
        return cleanup

    def wrap_command(self, command: list[str]) -> list[str]:
        if not self._instance_name:
            # Fallback if prepare was not called
            self._instance_name = f"mcp-probe-{uuid.uuid4().hex[:8]}"
        cmd_args = command[1:]
        return ["incus", "exec", self._instance_name, "--"] + cmd_args

    def run_handshake(
        self, command: list[str], timeout: float = 5.0, env: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        cleanup = None
        try:
            cleanup = self.prepare(command, timeout)
            exec_cmd = self.wrap_command(command)
            return probe_mcp_server_stdio(exec_cmd, env=env, timeout_seconds=timeout)
        except Exception as exc:
            if isinstance(exc, EnvironmentError) and "not found" in str(exc):
                raise
            return []
        finally:
            if cleanup:
                cleanup()

class AutoSandboxRunner(BaseSandboxRunner):
    def __init__(self):
        if shutil.which("incus"):
            self._runner = IncusSandboxRunner()
        elif shutil.which("docker"):
            self._runner = DockerSandboxRunner()
        else:
            self._runner = HostSandboxRunner()

    def _is_host_command(self, command: list[str]) -> bool:
        if not command:
            return True
        first = command[0]
        return bool(os.path.isabs(first) or os.path.exists(first) or first.startswith(("./", "../", "/")))
            
    def prepare(self, command: list[str], timeout: float = 5.0) -> Any:
        if self._is_host_command(command):
            return None
        return self._runner.prepare(command, timeout)
        
    def wrap_command(self, command: list[str]) -> list[str]:
        if self._is_host_command(command):
            return command
        return self._runner.wrap_command(command)

    def run_handshake(
        self, command: list[str], timeout: float = 5.0, env: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        if self._is_host_command(command):
            return HostSandboxRunner().run_handshake(command, timeout, env)
        try:
            return self._runner.run_handshake(command, timeout, env)
        except Exception:
            return HostSandboxRunner().run_handshake(command, timeout, env)


def get_sandbox_runner(mode: str = "auto", **kwargs) -> BaseSandboxRunner:
    if mode == "docker":
        return DockerSandboxRunner()
    elif mode == "incus":
        return IncusSandboxRunner(is_vm=False)
    elif mode == "incus-vm":
        return IncusSandboxRunner(is_vm=True)
    elif mode == "host":
        return HostSandboxRunner()
    else:
        return AutoSandboxRunner()
