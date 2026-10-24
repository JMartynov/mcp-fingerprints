from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from mcp_fingerprints.config_exporter import (
    EXPORTER_MAP,
    patch_jsonc,
    extract_base_config,
)
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.data_loader import load_passports
from mcp_fingerprints.config_scanner import ClientConfigLocator


class SandboxMode(str, Enum):
    DOCKER = "docker"
    NONE = "none"


class NetworkPolicy(str, Enum):
    NONE = "none"
    BRIDGE = "bridge"


@dataclass
class InstallPlan:
    server_key: str
    package_name: str
    ecosystem: str
    command: str
    args: List[str]
    env: Dict[str, str]
    target_clients: List[str]
    patched_files: Dict[str, str]


class DockerSandboxBuilder:
    @staticmethod
    def build_command(
        spec: ServerPackageSpec,
        sandbox: SandboxMode = SandboxMode.NONE,
        network_policy: NetworkPolicy = NetworkPolicy.NONE,
        read_only: bool = False,
    ) -> tuple[str, List[str], Dict[str, str]]:
        """
        Constructs the execution command, arguments, and environment variables.
        """
        # Resolve initial command & args based on ecosystem (same logic as ConfigExporter)
        base_cmd = ""
        base_args: List[str] = []
        env: Dict[str, str] = {}
        
        # Prepare environment placeholders
        for key in spec.versions[0].required_env_vars:
            env[key] = f"${{{key}}}"

        # If it's not docker, we need base command
        if spec.ecosystem in ("npm", "typescript", "javascript"):
            base_cmd = "npx"
            base_args = ["-y", spec.package_name]
        elif spec.ecosystem in ("pypi", "python"):
            base_cmd = "uvx"
            base_args = [spec.package_name]
        elif spec.ecosystem == "docker":
            # For docker ecosystem, package_name is usually the image
            base_cmd = "docker"
            base_args = ["run", "-i", "--rm", spec.package_name]
        else:
            base_cmd = spec.package_name

        if sandbox == SandboxMode.NONE:
            return base_cmd, base_args, env

        # Docker sandboxing
        docker_cmd = "docker"
        docker_args = ["run", "-i", "--rm"]
        docker_args.extend(["--network", network_policy.value])

        if read_only:
            docker_args.extend(["--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m"])

        docker_args.extend(["--cap-drop=ALL", "--security-opt=no-new-privileges"])

        for key in env:
            docker_args.extend(["-e", key])

        if spec.ecosystem == "docker" or base_cmd == "docker":
            # Already a docker image, just append the image name (which was in base_args)
            # Remove "run", "-i", "--rm" from base_args if present
            filtered_base_args = [arg for arg in base_args if arg not in ("run", "-i", "--rm")]
            docker_args.extend(filtered_base_args)
        elif spec.ecosystem in ("npm", "typescript", "javascript"):
            docker_args.append("node:20-alpine")
            docker_args.append(base_cmd)
            docker_args.extend(base_args)
        elif spec.ecosystem in ("pypi", "python"):
            docker_args.append("ghcr.io/astral-sh/uv:python3.12-alpine")
            docker_args.append(base_cmd)
            docker_args.extend(base_args)
        else:
            docker_args.append("alpine:latest")
            docker_args.append(base_cmd)
            docker_args.extend(base_args)

        return docker_cmd, docker_args, env


class ClientInstaller:
    @staticmethod
    def install(
        package_or_passport: str,
        client: str = "all",
        sandbox: SandboxMode = SandboxMode.NONE,
        network_policy: NetworkPolicy = NetworkPolicy.NONE,
        read_only: bool = False,
        dry_run: bool = False,
        config_path: Optional[str] = None,
        data_dir: str = "data/fingerprints",
    ) -> InstallPlan:
        # Resolve Passport
        passport_data = ClientInstaller._resolve_passport(package_or_passport, data_dir)
        if not passport_data:
            raise ValueError(f"Could not resolve passport for: {package_or_passport}")

        spec = ServerPackageSpec.from_dict(passport_data)
        
        command, args, env = DockerSandboxBuilder.build_command(
            spec, sandbox, network_policy, read_only
        )

        package_name = spec.package_name
        server_key = package_name.replace("@", "").replace("/", "-").replace("_", "-")

        # Determine target clients
        target_clients = []
        if client == "all":
            target_clients = list(EXPORTER_MAP.keys())
        elif client in EXPORTER_MAP:
            target_clients = [client]
        else:
             raise ValueError(f"Unsupported client: {client}. Must be one of {list(EXPORTER_MAP.keys())} or 'all'")

        patched_files: Dict[str, str] = {}

        for target in target_clients:
            paths_to_patch = []
            if config_path:
                paths_to_patch.append(Path(config_path))
            else:
                 paths_to_patch = ClientConfigLocator.get_standard_paths(client=target)
                 if not paths_to_patch:
                     # Create a default path if none exists
                     if target == "claude":
                         paths_to_patch = [Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"]
                     elif target == "cursor":
                         paths_to_patch = [Path.home() / ".cursor" / "mcp.json"]
                     elif target == "zed":
                         paths_to_patch = [Path.home() / ".config" / "zed" / "settings.json"]
                     elif target == "windsurf":
                         paths_to_patch = [Path.home() / ".codeium" / "windsurf" / "mcp_config.json"]
                     elif target == "cline":
                         paths_to_patch = [Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"]
            
            exporter_cls = EXPORTER_MAP[target]
            root_key = exporter_cls.get_root_key()

            for p in paths_to_patch:
                existing_content = ""
                if p.exists():
                     existing_content = p.read_text(encoding="utf-8")
                
                # Base config structure expected by generators
                base_config = {
                    "type": "stdio",
                    "command": command,
                    "args": args,
                    "env": env
                }
                
                server_config = exporter_cls.generate_server_config(base_config)
                patched = patch_jsonc(existing_content, root_key, server_key, server_config)
                
                patched_files[str(p)] = patched
                
                if not dry_run:
                     p.parent.mkdir(parents=True, exist_ok=True)
                     p.write_text(patched, encoding="utf-8")

        return InstallPlan(
            server_key=server_key,
            package_name=package_name,
            ecosystem=spec.ecosystem,
            command=command,
            args=args,
            env=env,
            target_clients=target_clients,
            patched_files=patched_files,
        )

    @staticmethod
    def _resolve_passport(identifier: str, data_dir: str) -> Optional[Dict[str, Any]]:
        # 1. Try as exact file path
        p = Path(identifier)
        if p.exists() and p.is_file() and p.suffix == ".json":
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 2. Try in data directory
        dir_path = Path(data_dir)
        if dir_path.exists():
             for j_file in sorted(dir_path.rglob("*.json")):
                 if j_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
                     continue
                 try:
                     content = json.loads(j_file.read_text(encoding="utf-8"))
                     if content.get("package_name") == identifier:
                         return content
                 except Exception:
                     pass
        
        # 3. Try fallback to passports.json.gz snapshot loader if available
        passports = load_passports()
        if passports:
             for passport in passports.values():
                  if passport.get("package_name") == identifier:
                       return passport
        return None

