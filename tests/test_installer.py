import pytest
from pathlib import Path
import json

from mcp_fingerprints.installer import DockerSandboxBuilder, ClientInstaller, SandboxMode, NetworkPolicy
from mcp_fingerprints.models import ServerPackageSpec


def test_docker_sandbox_builder_npm_read_only_bridge():
    spec = ServerPackageSpec.from_dict({
        "package_name": "test-npm-pkg",
        "purl": "pkg:npm/test-npm-pkg",
        "ecosystem": "npm",
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}],
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "required_env_vars": ["API_KEY"]}]
    })
    
    cmd, args, env = DockerSandboxBuilder.build_command(
        spec, 
        sandbox=SandboxMode.DOCKER, 
        network_policy=NetworkPolicy.BRIDGE, 
        read_only=True
    )
    
    assert cmd == "docker"
    assert "run" in args
    assert "-i" in args
    assert "--rm" in args
    assert "--network" in args
    assert "bridge" in args
    assert "--read-only" in args
    assert "--tmpfs" in args
    assert "/tmp:rw,noexec,nosuid,size=64m" in args
    assert "--cap-drop=ALL" in args
    assert "--security-opt=no-new-privileges" in args
    assert "-e" in args
    assert "API_KEY" in args
    assert "node:20-alpine" in args
    assert "npx" in args
    assert "-y" in args
    assert "test-npm-pkg" in args
    
    assert env == {"API_KEY": "${API_KEY}"}

def test_docker_sandbox_builder_pypi_none_network():
    spec = ServerPackageSpec.from_dict({
        "package_name": "test-pypi-pkg",
        "purl": "pkg:pypi/test-pypi-pkg",
        "ecosystem": "pypi",
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}]
    })
    
    cmd, args, env = DockerSandboxBuilder.build_command(
        spec, 
        sandbox=SandboxMode.DOCKER, 
        network_policy=NetworkPolicy.NONE, 
        read_only=False
    )
    
    assert cmd == "docker"
    assert "--network" in args
    assert "none" in args
    assert "--read-only" not in args
    assert "ghcr.io/astral-sh/uv:python3.12-alpine" in args
    assert "uvx" in args
    assert "test-pypi-pkg" in args

def test_docker_sandbox_builder_docker_ecosystem():
    spec = ServerPackageSpec.from_dict({
        "package_name": "my-docker/image",
        "purl": "pkg:docker/my-docker/image",
        "ecosystem": "docker",
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}]
    })
    
    cmd, args, env = DockerSandboxBuilder.build_command(
        spec, 
        sandbox=SandboxMode.DOCKER, 
        network_policy=NetworkPolicy.NONE, 
        read_only=False
    )
    
    assert cmd == "docker"
    # Should not include a second language runtime image
    assert "ghcr.io/astral-sh/uv:python3.12-alpine" not in args
    assert "node:20-alpine" not in args
    assert "my-docker/image" in args

def test_docker_sandbox_builder_no_sandbox():
    spec = ServerPackageSpec.from_dict({
        "package_name": "test-pkg",
        "purl": "pkg:npm/test-pkg",
        "ecosystem": "npm",
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}]
    })
    
    cmd, args, env = DockerSandboxBuilder.build_command(
        spec, 
        sandbox=SandboxMode.NONE
    )
    
    assert cmd == "npx"
    assert args == ["-y", "test-pkg"]

def test_client_installer_lossless_patching(tmp_path):
    config_path = tmp_path / "claude_desktop_config.json"
    
    initial_content = """{
  // User comment
  "mcpServers": {
    /* block comment */
    "existing": {
      "command": "echo",
      "args": ["hello"]
    }
  }
}"""
    config_path.write_text(initial_content, encoding="utf-8")
    
    # Mock resolve passport
    passport_data = {
        "package_name": "new-server",
        "purl": "pkg:npm/new-server",
        "ecosystem": "npm",
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}]
    }
    passport_path = tmp_path / "new-server.json"
    passport_path.write_text(json.dumps(passport_data), encoding="utf-8")
    
    plan = ClientInstaller.install(
        package_or_passport=str(passport_path),
        client="claude",
        sandbox=SandboxMode.DOCKER,
        network_policy=NetworkPolicy.NONE,
        read_only=True,
        dry_run=False,
        config_path=str(config_path)
    )
    
    assert len(plan.patched_files) == 1
    patched_content = plan.patched_files[str(config_path)]
    
    # Check that comments were preserved
    assert "// User comment" in patched_content
    assert "/* block comment */" in patched_content
    assert '"existing":' in patched_content
    
    # Check that the new server was added
    assert '"new-server":' in patched_content
    assert '"docker"' in patched_content
    assert '"--read-only"' in patched_content
    
    # Check that it wrote to disk correctly
    disk_content = config_path.read_text(encoding="utf-8")
    assert disk_content == patched_content

def test_client_installer_zed_format(tmp_path):
    config_path = tmp_path / "zed_settings.json"
    config_path.write_text("{\n  \"context_servers\": {\n  }\n}", encoding="utf-8")
    
    passport_data = {
        "package_name": "zed-server",
        "purl": "pkg:pypi/zed-server",
        "ecosystem": "pypi",
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}]
    }
    passport_path = tmp_path / "zed-server.json"
    passport_path.write_text(json.dumps(passport_data), encoding="utf-8")
    
    plan = ClientInstaller.install(
        package_or_passport=str(passport_path),
        client="zed",
        sandbox=SandboxMode.NONE,
        dry_run=False,
        config_path=str(config_path)
    )
    
    patched_content = plan.patched_files[str(config_path)]
    assert '"context_servers":' in patched_content
    assert '"zed-server":' in patched_content
    assert '"command":' in patched_content
    assert '"path":' in patched_content
    assert '"uvx"' in patched_content

def test_client_installer_dry_run(tmp_path):
    config_path = tmp_path / "dummy.json"
    config_path.write_text("{}", encoding="utf-8")
    
    passport_data = {
        "package_name": "dry-run-server",
        "purl": "pkg:npm/dry-run-server",
        "ecosystem": "npm",
        "versions": [{"version": "1.0.0", "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}]
    }
    passport_path = tmp_path / "dry-run.json"
    passport_path.write_text(json.dumps(passport_data), encoding="utf-8")
    
    plan = ClientInstaller.install(
        package_or_passport=str(passport_path),
        client="claude",
        dry_run=True,
        config_path=str(config_path)
    )
    
    # Ensure file was NOT modified
    assert config_path.read_text(encoding="utf-8") == "{}"
    
    # Ensure patched content is returned
    patched_content = plan.patched_files[str(config_path)]
    assert '"dry-run-server"' in patched_content
