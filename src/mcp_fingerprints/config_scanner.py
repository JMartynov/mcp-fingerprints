"""Automated configuration discovery and scanning for MCP local developer workstation configurations."""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Callable

from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.prober import McpStdioProber, McpHttpProber

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

logger = logging.getLogger(__name__)

@dataclass
class LocalInventoryReport:
    """Report generated after scanning local client configuration files."""

    servers: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "servers": self.servers,
            "errors": self.errors,
        }

class ClientRegistry:
    def __init__(self):
        self.clients = []
        self._register_builtins()

    def register(self, name: str, paths: list[Path], parser: Callable[[str, Any], dict[str, Any]]):
        self.clients.append({
            "name": name,
            "paths": paths,
            "parser": parser
        })

    def load_custom_config(self, custom_clients_path: str | Path):
        path = Path(custom_clients_path)
        if not path.exists():
            logger.warning(f"Custom clients file {path} not found.")
            return

        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse custom clients config {path}: {e}")
                return

        def parse_custom(config_data: Any) -> dict[str, Any]:
            if isinstance(config_data, dict) and "mcpServers" in config_data:
                return config_data["mcpServers"]
            return {}

        for client_name, client_config in data.items():
            paths = []
            for p in client_config.get("paths", []):
                expanded = os.path.expanduser(p)
                expanded = os.path.expandvars(expanded)
                paths.append(Path(expanded))

            self.register(client_name, paths, parse_custom)


    def _register_builtins(self):
        home = Path.home()
        cwd = Path.cwd()

        def parse_standard(config_data: Any) -> dict[str, Any]:
            if isinstance(config_data, dict) and "mcpServers" in config_data:
                return config_data["mcpServers"]
            return {}

        def parse_claude_code(config_data: Any) -> dict[str, Any]:
            servers = {}
            if isinstance(config_data, dict):
                if "mcpServers" in config_data:
                    servers.update(config_data["mcpServers"])
                if "projects" in config_data:
                    for proj, proj_data in config_data["projects"].items():
                        if "mcpServers" in proj_data:
                            for name, s_cfg in proj_data["mcpServers"].items():
                                servers[f"{proj}:{name}"] = s_cfg
            return servers

        def parse_zed(config_data: Any) -> dict[str, Any]:
            servers = {}
            if isinstance(config_data, dict) and "context_servers" in config_data:
                for name, s_cfg in config_data["context_servers"].items():
                    cmd = s_cfg.get("command", {})
                    servers[name] = {
                        "command": cmd.get("path"),
                        "args": cmd.get("args", []),
                        "env": cmd.get("env", {})
                    }
            return servers

        def parse_vscode(config_data: Any) -> dict[str, Any]:
            servers = {}
            if isinstance(config_data, dict):
                # sometimes mcp.json, sometimes settings.json
                target = config_data.get("mcpServers", config_data.get("servers", {}))
                if isinstance(target, dict):
                    for name, s_cfg in target.items():
                        cmd = s_cfg.get("command", {})
                        if isinstance(cmd, dict):
                            servers[name] = {
                                "command": cmd.get("command", ""),
                                "args": cmd.get("args", []),
                                "env": cmd.get("env", {})
                            }
                        else:
                             servers[name] = s_cfg
                elif isinstance(target, list):
                     for s_cfg in target:
                         name = s_cfg.get("name", "unknown")
                         servers[name] = s_cfg

            return servers

        def parse_goose(config_data: Any) -> dict[str, Any]:
            servers = {}
            if isinstance(config_data, dict) and "extensions" in config_data:
                for name, s_cfg in config_data["extensions"].items():
                    servers[name] = {
                        "command": s_cfg.get("cmd"),
                        "args": s_cfg.get("args", []),
                        "env": s_cfg.get("envs", {}),
                        "url": s_cfg.get("uri")
                    }
            return servers

        def parse_continue(config_data: Any) -> dict[str, Any]:
            servers = {}
            if isinstance(config_data, dict) and "mcpServers" in config_data:
                mcp_servers = config_data["mcpServers"]
                if isinstance(mcp_servers, list):
                    for s_cfg in mcp_servers:
                        name = s_cfg.get("name", "unknown")
                        servers[name] = s_cfg
                elif isinstance(mcp_servers, dict):
                    servers = mcp_servers
            return servers

        # 1. Claude Desktop
        claude_desktop_paths = []
        if sys.platform == "darwin":
            claude_desktop_paths.append(home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json")
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                claude_desktop_paths.append(Path(appdata) / "Claude" / "claude_desktop_config.json")
        elif sys.platform == "linux":
            claude_desktop_paths.append(home / ".config" / "claude-desktop" / "config.json")
        self.register("claude-desktop", claude_desktop_paths, parse_standard)

        # 2. Claude Code
        claude_code_paths = [home / ".claude.json", cwd / ".mcp.json"]
        self.register("claude-code", claude_code_paths, parse_claude_code)

        # 3. Cursor
        cursor_paths = [home / ".cursor" / "mcp.json", cwd / ".cursor" / "mcp.json"]
        self.register("cursor", cursor_paths, parse_standard)

        # 4. Windsurf
        windsurf_paths = [home / ".codeium" / "windsurf" / "mcp_config.json"]
        self.register("windsurf", windsurf_paths, parse_standard)

        # 5. Zed
        zed_paths = []
        if sys.platform == "darwin":
            zed_paths.append(home / ".config" / "zed" / "settings.json")
        elif sys.platform == "linux":
            zed_paths.append(home / ".config" / "zed" / "settings.json")
        elif sys.platform == "win32":
             appdata = os.environ.get("LOCALAPPDATA", "")
             if appdata:
                 zed_paths.append(Path(appdata) / "Zed" / "settings.json")
        self.register("zed", zed_paths, parse_zed)

        # 6. Cline
        cline_paths = []
        if sys.platform == "darwin":
            cline_paths.append(home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json")
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                 cline_paths.append(Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json")
        elif sys.platform == "linux":
            cline_paths.append(home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json")
        self.register("cline", cline_paths, parse_standard)

        # 7. Roo Code
        roo_paths = []
        if sys.platform == "darwin":
            roo_paths.append(home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_mcp_settings.json")
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                 roo_paths.append(Path(appdata) / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_mcp_settings.json")
        elif sys.platform == "linux":
            roo_paths.append(home / ".config" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_mcp_settings.json")
        self.register("roo-code", roo_paths, parse_standard)

        # 8. Goose
        goose_paths = []
        if sys.platform == "darwin":
            goose_paths.append(home / ".config" / "goose" / "config.yaml")
        elif sys.platform == "linux":
            goose_paths.append(home / ".config" / "goose" / "config.yaml")
        elif sys.platform == "win32":
            appdata = os.environ.get("LOCALAPPDATA", "")
            if appdata:
                goose_paths.append(Path(appdata) / "goose" / "config.yaml")
        self.register("goose", goose_paths, parse_goose)

        # 9. Continue.dev
        continue_paths = [home / ".continue" / "config.json"]
        self.register("continue", continue_paths, parse_continue)

        # 10. JetBrains Junie
        junie_paths = []
        # Junie uses standard settings sometimes in `.idea/mcp.json`
        junie_paths.append(cwd / ".idea" / "mcp.json")
        self.register("junie", junie_paths, parse_standard)

        # 11. VS Code / GitHub Copilot
        vscode_paths = []
        if sys.platform == "darwin":
            vscode_paths.append(home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "github.copilot" / "mcp.json")
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                 vscode_paths.append(Path(appdata) / "Code" / "User" / "globalStorage" / "github.copilot" / "mcp.json")
        elif sys.platform == "linux":
            vscode_paths.append(home / ".config" / "Code" / "User" / "globalStorage" / "github.copilot" / "mcp.json")
        self.register("vscode", vscode_paths, parse_vscode)

        # 12. Antigravity
        antigravity_paths = [home / ".gemini" / "config" / "mcp_config.json"]
        self.register("antigravity", antigravity_paths, parse_standard)

        # 13. OpenHands
        openhands_paths = [home / ".openhands" / "mcp.json"]
        self.register("openhands", openhands_paths, parse_standard)

        # 14. Trae
        trae_paths = [home / ".trae" / "mcp.json"]
        self.register("trae", trae_paths, parse_standard)

        # 15. LM Studio
        lmstudio_paths = [home / ".lmstudio" / "mcp.json"]
        self.register("lmstudio", lmstudio_paths, parse_standard)


class ClientConfigLocator:
    """Resolves standard paths across macOS, Linux, and Windows for known clients."""

    def __init__(self) -> None:
        self.registry = ClientRegistry()

    @staticmethod
    def get_standard_paths(client: str | None = None) -> list[Path]:
        """Returns a list of potential configuration file paths for known clients."""
        registry = ClientRegistry()
        paths = []
        for c in registry.clients:
            if client and c["name"] != client:
                 continue
            paths.extend(c["paths"])
        return [p for p in paths if p.exists()]



class ConfigScanner:
    """Parses JSON configurations and extracts mcpServers dictionary."""

    def __init__(self, matcher: FingerprintMatcher | None = None) -> None:
        self.matcher = matcher or FingerprintMatcher()
        self.prober_stdio = McpStdioProber(matcher=self.matcher)
        self.prober_http = McpHttpProber(matcher=self.matcher)
        self.registry = ClientRegistry()

    def _extract_servers_from_config(self, config_data: Any, path: Path) -> dict[str, Any]:
        """Extracts mcpServers from a parsed JSON/YAML config based on registry."""
        for client in self.registry.clients:
            if any(path.name == p.name and path.parent.name == p.parent.name for p in client["paths"]):
                 return client["parser"](config_data)

        # Fallback to standard
        if isinstance(config_data, dict) and "mcpServers" in config_data:
             return config_data["mcpServers"]
        return {}

    def scan_file(self, path: Path, probe_live: bool = True) -> LocalInventoryReport:
        """Scans a single configuration file."""
        report = LocalInventoryReport()
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            config_data = {}
            if path.suffix in [".yaml", ".yml"]:
                if HAS_YAML:
                    config_data = yaml.safe_load(content) or {}
                else:
                    logger.warning("YAML file detected but pyyaml is not installed.")
            else:
                # Simple JSON5/JSONC handling by removing simple single-line comments for standard `json`
                import re
                content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)
                try:
                    config_data = json.loads(content)
                except json.JSONDecodeError:
                    pass

            servers = self._extract_servers_from_config(config_data, path)
            for server_name, server_config in servers.items():
                server_info = {
                    "name": server_name,
                    "config_source": str(path),
                    "command": server_config.get("command"),
                    "args": server_config.get("args", []),
                    "env": server_config.get("env", {}),
                    "url": server_config.get("url"),
                    "headers": server_config.get("headers", {}),
                }
                
                if probe_live:
                    if server_info.get("command"):
                        try:
                            cmd_list = [server_info["command"]] + server_info["args"]
                            probe_report = self.prober_stdio.probe_stdio(cmd_list, env=server_info["env"])
                            server_info["live_probe"] = probe_report.to_dict()
                        except Exception as e:
                            logger.warning(f"Failed to probe stdio server {server_name}: {e}")
                            server_info["live_probe"] = {"error": str(e), "connection_successful": False}
                    elif server_info.get("url"):
                        try:
                            probe_report = self.prober_http.probe_http(server_info["url"], headers=server_info.get("headers", {}))
                            server_info["live_probe"] = probe_report.to_dict()
                        except Exception as e:
                            logger.warning(f"Failed to probe http server {server_name}: {e}")
                            server_info["live_probe"] = {"error": str(e), "connection_successful": False}
                
                report.servers.append(server_info)
                
        except Exception as e:
            report.errors.append(f"Failed to read/parse {path}: {e}")
            logger.error(f"Failed to read/parse {path}: {e}")
            
        return report

    def scan(self, paths: Iterable[Path] | None = None, probe_live: bool = True, client: str | None = None, custom_clients_path: str | Path | None = None) -> LocalInventoryReport:
        """Scans multiple paths for servers and optionally probes them."""
        report = LocalInventoryReport()
        
        if custom_clients_path:
             self.registry.load_custom_config(custom_clients_path)

        if paths is None:
            paths = ClientConfigLocator.get_standard_paths(client=client)

            
        for path in paths:
            if path.is_dir():
                # For directories, look for project level configs
                cursor_config = path / ".cursor" / "mcp.json"
                if cursor_config.exists():
                    sub_report = self.scan_file(cursor_config, probe_live=probe_live)
                    report.servers.extend(sub_report.servers)
                    report.errors.extend(sub_report.errors)
            elif path.exists():
                sub_report = self.scan_file(path, probe_live=probe_live)
                report.servers.extend(sub_report.servers)
                report.errors.extend(sub_report.errors)
                
        return report
