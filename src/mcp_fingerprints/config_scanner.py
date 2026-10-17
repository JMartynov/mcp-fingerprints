"""Automated configuration discovery and scanning for MCP local developer workstation configurations."""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.prober import McpStdioProber, McpHttpProber

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

class ClientConfigLocator:
    """Resolves standard paths across macOS, Linux, and Windows for known clients."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def get_standard_paths() -> list[Path]:
        """Returns a list of potential configuration file paths for known clients."""
        paths = []
        home = Path.home()
        
        # Claude Desktop
        if sys.platform == "darwin":
            paths.append(home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json")
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                paths.append(Path(appdata) / "Claude" / "claude_desktop_config.json")
        elif sys.platform == "linux":
            paths.append(home / ".config" / "claude-desktop" / "config.json")
            
        # Cursor
        paths.append(home / ".cursor" / "mcp.json")
        # Local project path (requires project dir to be scanned separately, but we add a generic one if running from project)
        paths.append(Path.cwd() / ".cursor" / "mcp.json")
        
        # Windsurf
        paths.append(home / ".codeium" / "windsurf" / "mcp_config.json")
        
        # Zed
        if sys.platform == "darwin":
            paths.append(home / ".config" / "zed" / "settings.json")
        elif sys.platform == "linux":
            paths.append(home / ".config" / "zed" / "settings.json")
            
        # Cline (VSCode extension usually uses globalSettings or workspace settings, but sometimes has its own config)
        if sys.platform == "darwin":
            paths.append(home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json")
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                 paths.append(Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json")
        elif sys.platform == "linux":
            paths.append(home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json")

        return [p for p in paths if p.exists()]

class ConfigScanner:
    """Parses JSON configurations and extracts mcpServers dictionary."""

    def __init__(self, matcher: FingerprintMatcher | None = None) -> None:
        self.matcher = matcher or FingerprintMatcher()
        self.prober_stdio = McpStdioProber(matcher=self.matcher)
        self.prober_http = McpHttpProber(matcher=self.matcher)

    def _extract_servers_from_config(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Extracts mcpServers from a parsed JSON config."""
        # Standard format
        if "mcpServers" in config_data:
            return config_data["mcpServers"]
        return {}

    def scan_file(self, path: Path, probe_live: bool = True) -> LocalInventoryReport:
        """Scans a single configuration file."""
        report = LocalInventoryReport()
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # Simple JSON5/JSONC handling by removing simple single-line comments for standard `json`
                import re
                content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)
                config_data = json.loads(content)
                
            servers = self._extract_servers_from_config(config_data)
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

    def scan(self, paths: Iterable[Path] | None = None, probe_live: bool = True) -> LocalInventoryReport:
        """Scans multiple paths for servers and optionally probes them."""
        report = LocalInventoryReport()
        if paths is None:
            paths = ClientConfigLocator.get_standard_paths()
            
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

