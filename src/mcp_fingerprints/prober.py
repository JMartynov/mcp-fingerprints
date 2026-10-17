"""Live runtime MCP prober connecting via stdio JSON-RPC to inspect and audit servers."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import queue
import threading
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from packaging.version import parse as parse_version

from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.models import FingerprintMatchResult

logger = logging.getLogger("mcp_fingerprints.prober")


@dataclass
class ProbeReport:
    """Consolidated probe and identification report."""

    server_command: list[str]
    connection_successful: bool
    tools_observed: list[dict[str, Any]] = field(default_factory=list)
    prompts_observed: list[dict[str, Any]] = field(default_factory=list)
    resources_observed: list[dict[str, Any]] = field(default_factory=list)
    match_result: FingerprintMatchResult | None = None
    error: str | None = None
    repository_url: str | None = None
    homepage_url: str | None = None
    install_command: str | None = None
    author: str | None = None
    latest_version: str | None = None
    is_outdated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_command": self.server_command,
            "connection_successful": self.connection_successful,
            "tools_count": len(self.tools_observed),
            "prompts_count": len(self.prompts_observed),
            "resources_count": len(self.resources_observed),
            "match": self.match_result.to_dict() if self.match_result else None,
            "error": self.error,
            "repository_url": self.repository_url,
            "homepage_url": self.homepage_url,
            "install_command": self.install_command,
            "author": self.author,
            "latest_version": self.latest_version,
            "is_outdated": self.is_outdated,
        }


class McpStdioProber:
    """Probes a running or launchable MCP server over stdio JSON-RPC 2.0."""

    def __init__(self, matcher: FingerprintMatcher | None = None, **kwargs: Any) -> None:
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

    @staticmethod
    def build_package_command(package_name: str, ecosystem: str = "npm") -> list[str]:
        """Construct standard stdio launch command for package across ecosystems (npm, PyPI)."""
        eco = ecosystem.lower()
        if eco in ("npm", "javascript", "typescript"):
            return ["npx", "-y", package_name]
        elif eco in ("pypi", "python"):
            if package_name.startswith("mcp-server-"):
                mod_name = package_name.replace("-", "_")
                return ["python", "-m", mod_name]
            return ["uvx", package_name]
        elif eco == "docker":
            return ["docker", "run", "-i", "--rm", package_name]
        return ["npx", "-y", package_name]

    def probe_package(
        self,
        package_name: str,
        ecosystem: str = "npm",
        cwd: str | Path | None = None,
        timeout: float = 10.0,
        min_confidence_threshold: float = 0.65,
    ) -> ProbeReport:
        """Construct runner command for package and conduct live stdio probe handshake."""
        cmd = self.build_package_command(package_name, ecosystem=ecosystem)
        return self.probe(
            command=cmd,
            cwd=cwd,
            timeout=timeout,
            server_name_hint=package_name,
            min_confidence_threshold=min_confidence_threshold,
        )

    def probe(
        self,
        command: list[str],
        cwd: str | Path | None = None,
        timeout: float = 10.0,
        server_name_hint: str | None = None,
        min_confidence_threshold: float = 0.65,
        env: dict[str, str] | None = None,
    ) -> ProbeReport:
        """Launch command, conduct MCP handshake, query capabilities, and audit security."""
        proc = None
        try:
            merged_env = os.environ.copy()
            if env:
                merged_env.update(env)
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=merged_env,
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

        report = ProbeReport(
            server_command=command,
            connection_successful=True,
            tools_observed=tools,
            prompts_observed=prompts,
            resources_observed=resources,
            match_result=match_result,
        )

        if match_result.matched and match_result.package_name:
            pkg_spec = self.matcher.fast_index.find_package_by_hint_or_alias(match_result.package_name)
            if pkg_spec:
                report.repository_url = pkg_spec.repository_url
                report.homepage_url = pkg_spec.homepage_url
                report.author = pkg_spec.author
                report.install_command = " ".join(self.build_package_command(pkg_spec.package_name, pkg_spec.ecosystem))
                
                if pkg_spec.versions:
                    try:
                        latest_ver = max(pkg_spec.versions, key=lambda v: parse_version(v.version))
                        report.latest_version = latest_ver.version
                        if match_result.matched_version:
                            report.is_outdated = parse_version(match_result.matched_version) < parse_version(report.latest_version)
                    except Exception:
                        pass
                        
        return report

    def probe_stdio(self, command: list[str], **kwargs: Any) -> ProbeReport:
        """Alias for probe(command=...) for compatibility with config_scanner."""
        return self.probe(command=command, **kwargs)


class McpHttpProber:
    """Probes a running or launchable MCP server over HTTP/HTTPS (SSE or Streamable POST)."""

    def __init__(self, matcher: FingerprintMatcher | None = None, **kwargs: Any) -> None:
        self.matcher = matcher or FingerprintMatcher()

    def probe(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
        server_name_hint: str | None = None,
        min_confidence_threshold: float = 0.65,
    ) -> ProbeReport:
        """Connect to HTTP endpoint, conduct MCP handshake, query capabilities, and audit security."""
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        tools, prompts, resources = [], [], []
        
        # Determine if SSE or Streamable POST
        # We try a POST first. If it responds with JSON, it's streamable HTTP.
        # If it returns 404/405 or requires GET, we try SSE.
        
        is_sse = False
        post_url = url
        sse_response = None
        sse_queue = queue.Queue()
        stop_event = threading.Event()
        
        # Try SSE handshake
        try:
            req = urllib.request.Request(url, headers={"Accept": "text/event-stream", **(headers or {})})
            resp = urllib.request.urlopen(req, timeout=timeout)
            if "text/event-stream" in resp.getheader("Content-Type", ""):
                is_sse = True
                sse_response = resp
            else:
                resp.close()
        except (URLError, HTTPError):
            pass
            
        def sse_reader():
            try:
                for line in sse_response:
                    if stop_event.is_set():
                        break
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        # Might be an endpoint event or jsonrpc response
                        if data_str.startswith("{"):
                            try:
                                data = json.loads(data_str)
                                sse_queue.put(data)
                            except json.JSONDecodeError:
                                pass
                        else:
                            # Usually endpoint URI comes directly in data for endpoint event
                            sse_queue.put({"endpoint": data_str})
            except Exception:
                pass
                
        def send_post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any] | None:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=req_data, headers=req_headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    resp_data = response.read().decode("utf-8")
                    if not is_sse:
                        return json.loads(resp_data)
                    return None
            except (URLError, HTTPError, json.JSONDecodeError):
                return None
                
        def get_response(msg_id: int, wait_timeout: float = 5.0) -> dict[str, Any] | None:
            if not is_sse:
                return None # Should be handled synchronously
            start = time.time()
            while time.time() - start < wait_timeout:
                try:
                    msg = sse_queue.get(timeout=0.1)
                    if msg.get("id") == msg_id:
                        return msg
                    sse_queue.put(msg) # Put back if not matched
                except queue.Empty:
                    pass
            return None

        try:
            if is_sse:
                reader_thread = threading.Thread(target=sse_reader, daemon=True)
                reader_thread.start()
                # Wait for endpoint
                start_wait = time.time()
                while time.time() - start_wait < timeout:
                    try:
                        msg = sse_queue.get(timeout=0.1)
                        if "endpoint" in msg:
                            endpoint_path = msg["endpoint"]
                            if endpoint_path.startswith("http"):
                                post_url = endpoint_path
                            else:
                                parsed_url = urllib.parse.urlparse(url)
                                # resolve relative to base
                                if endpoint_path.startswith("/"):
                                    post_url = f"{parsed_url.scheme}://{parsed_url.netloc}{endpoint_path}"
                                else:
                                    post_url = f"{url.rstrip('/')}/{endpoint_path}"
                            break
                        sse_queue.put(msg)
                    except queue.Empty:
                        pass
                        
            # 1. Initialize
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-fingerprints-prober", "version": "1.0.0"},
                },
            }
            
            init_resp = send_post(post_url, init_req)
            if is_sse:
                init_resp = get_response(1, timeout)
            
            if not init_resp or "result" not in init_resp:
                return ProbeReport(
                    server_command=[url],
                    connection_successful=False,
                    error=f"Failed to receive valid initialize response: {init_resp}",
                )

            # 2. Initialized notification
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            send_post(post_url, notif)

            # 3. Query tools
            tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            tools_resp = send_post(post_url, tools_req)
            if is_sse:
                tools_resp = get_response(2, timeout)
            if tools_resp:
                tools = tools_resp.get("result", {}).get("tools", [])

            # 4. Query prompts
            prompts_req = {"jsonrpc": "2.0", "id": 3, "method": "prompts/list", "params": {}}
            prompts_resp = send_post(post_url, prompts_req)
            if is_sse:
                prompts_resp = get_response(3, timeout)
            if prompts_resp:
                prompts = prompts_resp.get("result", {}).get("prompts", [])

            # 5. Query resources
            res_req = {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}}
            res_resp = send_post(post_url, res_req)
            if is_sse:
                res_resp = get_response(4, timeout)
            if res_resp:
                resources = res_resp.get("result", {}).get("resources", [])

        except Exception as exc:
            return ProbeReport(
                server_command=[url],
                connection_successful=False,
                error=str(exc),
            )
        finally:
            stop_event.set()
            if sse_response:
                sse_response.close()

        match_result = self.matcher.match(
            tools=tools,
            prompts=prompts,
            resources=resources,
            server_name_hint=server_name_hint,
            min_confidence_threshold=min_confidence_threshold,
        )

        return ProbeReport(
            server_command=[url],
            connection_successful=True,
            tools_observed=tools,
            prompts_observed=prompts,
            resources_observed=resources,
            match_result=match_result,
        )

    def probe_http(self, url: str, headers: dict[str, str] | None = None, timeout: float = 10.0, **kwargs: Any) -> ProbeReport:
        """Alias for probe(url=...) for compatibility with config_scanner."""
        return self.probe(url=url, headers=headers, timeout=timeout, **kwargs)

class McpProber:
    """Unified prober routing to either stdio or HTTP depending on target."""

    def __init__(self, matcher: FingerprintMatcher | None = None, **kwargs: Any) -> None:
        self.matcher = matcher or FingerprintMatcher()

    def probe(
        self,
        target: str | list[str],
        headers: dict[str, str] | None = None,
        cwd: str | Path | None = None,
        timeout: float = 10.0,
        server_name_hint: str | None = None,
        min_confidence_threshold: float = 0.65,
    ) -> ProbeReport:
        if isinstance(target, str) and (target.startswith("http://") or target.startswith("https://")):
            prober = McpHttpProber(self.matcher)
            return prober.probe(
                url=target,
                headers=headers,
                timeout=timeout,
                server_name_hint=server_name_hint,
                min_confidence_threshold=min_confidence_threshold,
            )
        else:
            cmd = [target] if isinstance(target, str) else target
            prober = McpStdioProber(self.matcher)
            return prober.probe(
                command=cmd,
                cwd=cwd,
                timeout=timeout,
                server_name_hint=server_name_hint,
                min_confidence_threshold=min_confidence_threshold,
            )
