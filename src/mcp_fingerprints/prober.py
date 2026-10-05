"""Live runtime MCP prober connecting via stdio JSON-RPC to inspect and audit servers."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.models import FingerprintMatchResult

logger = logging.getLogger("mcp_fingerprints.prober")


@dataclass
class ProbeReport:
    """Consolidated probe, identification, and security audit report."""

    server_command: list[str]
    connection_successful: bool
    tools_observed: list[dict[str, Any]] = field(default_factory=list)
    prompts_observed: list[dict[str, Any]] = field(default_factory=list)
    resources_observed: list[dict[str, Any]] = field(default_factory=list)
    match_result: FingerprintMatchResult | None = None
    is_vulnerable: bool = False
    active_advisories: list[dict[str, Any]] = field(default_factory=list)
    max_cvss_score: float = 0.0
    recommended_fixed_version: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_command": self.server_command,
            "connection_successful": self.connection_successful,
            "tools_count": len(self.tools_observed),
            "prompts_count": len(self.prompts_observed),
            "resources_count": len(self.resources_observed),
            "match": self.match_result.to_dict() if self.match_result else None,
            "security": {
                "is_vulnerable": self.is_vulnerable,
                "max_cvss_score": self.max_cvss_score,
                "recommended_fixed_version": self.recommended_fixed_version,
                "active_advisories_count": len(self.active_advisories),
                "advisories": self.active_advisories,
            },
            "error": self.error,
        }


class McpStdioProber:
    """Probes a running or launchable MCP server over stdio JSON-RPC 2.0."""

    def __init__(self, matcher: FingerprintMatcher | None = None) -> None:
        self.matcher = matcher or FingerprintMatcher()

    @staticmethod
    def _read_jsonrpc_response(process: subprocess.Popen, timeout: float = 5.0) -> dict[str, Any] | None:
        """Read a single newline-delimited JSON-RPC message from process stdout."""
        if not process.stdout:
            return None
        start = time.time()
        while time.time() - start < timeout:
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
        return None

    def probe(
        self,
        command: list[str],
        cwd: str | Path | None = None,
        timeout: float = 10.0,
        server_name_hint: str | None = None,
        min_confidence_threshold: float = 0.65,
    ) -> ProbeReport:
        """Launch command, conduct MCP handshake, query capabilities, and audit security."""
        proc = None
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
            )

            # 1. Initialize
            init_req = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-fingerprints-prober", "version": "1.0.0"},
                },
            }) + "\n"
            proc.stdin.write(init_req.encode("utf-8"))
            proc.stdin.flush()

            init_resp = self._read_jsonrpc_response(proc, timeout=timeout)
            if not init_resp or "result" not in init_resp:
                return ProbeReport(
                    server_command=command,
                    connection_successful=False,
                    error=f"Failed to receive valid initialize response: {init_resp}",
                )

            # 2. Initialized notification
            notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
            proc.stdin.write(notif.encode("utf-8"))
            proc.stdin.flush()

            # 3. Query tools
            tools_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n"
            proc.stdin.write(tools_req.encode("utf-8"))
            proc.stdin.flush()
            tools_resp = self._read_jsonrpc_response(proc, timeout=timeout)
            tools = (tools_resp.get("result", {}).get("tools", [])) if tools_resp else []

            # 4. Query prompts
            prompts_req = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "prompts/list", "params": {}}) + "\n"
            proc.stdin.write(prompts_req.encode("utf-8"))
            proc.stdin.flush()
            prompts_resp = self._read_jsonrpc_response(proc, timeout=timeout)
            prompts = (prompts_resp.get("result", {}).get("prompts", [])) if prompts_resp else []

            # 5. Query resources
            res_req = json.dumps({"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}}) + "\n"
            proc.stdin.write(res_req.encode("utf-8"))
            proc.stdin.flush()
            res_resp = self._read_jsonrpc_response(proc, timeout=timeout)
            resources = (res_resp.get("result", {}).get("resources", [])) if res_resp else []

        except Exception as exc:
            return ProbeReport(
                server_command=command,
                connection_successful=False,
                error=str(exc),
            )
        finally:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=1.0)
                except Exception:
                    proc.kill()

        # Match against knowledge base
        match_result = self.matcher.match(
            tools=tools,
            prompts=prompts,
            resources=resources,
            server_name_hint=server_name_hint,
            min_confidence_threshold=min_confidence_threshold,
        )

        is_vulnerable = False
        active_advisories: list[dict[str, Any]] = []
        max_cvss = 0.0
        recommended_fix = None

        if match_result.matched and match_result.package_name:
            pkg_spec = self.matcher._packages.get(match_result.package_name)
            if pkg_spec and pkg_spec.security_profile:
                sec = pkg_spec.security_profile
                vuln_vers = set(sec.get("vulnerable_versions") or [])
                if match_result.matched_version in vuln_vers:
                    is_vulnerable = True
                    max_cvss = float(sec.get("max_cvss_score") or 0.0)
                    for adv in sec.get("advisories") or []:
                        if match_result.matched_version in adv.get("affected_versions", []):
                            active_advisories.append(adv)
                            if not recommended_fix and adv.get("fixed_version"):
                                recommended_fix = adv.get("fixed_version")

        return ProbeReport(
            server_command=command,
            connection_successful=True,
            tools_observed=tools,
            prompts_observed=prompts,
            resources_observed=resources,
            match_result=match_result,
            is_vulnerable=is_vulnerable,
            active_advisories=active_advisories,
            max_cvss_score=max_cvss,
            recommended_fixed_version=recommended_fix,
        )
