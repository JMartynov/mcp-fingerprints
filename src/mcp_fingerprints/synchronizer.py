"""Multi-Source Synchronizer, Updater, and Discovery Engine for MCP Passports."""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import re
import concurrent.futures
import ssl
import threading
import urllib.error
import urllib.request
import io
import tarfile
import time

from pathlib import Path
from typing import Any

from mcp_fingerprints.ast_parser import parse_mcp_source_code, parse_typescript_mcp_ast, parse_python_mcp_ast
from mcp_fingerprints.monorepo_prober import match_monorepo_subpackage_dir
from mcp_fingerprints.openapi_parser import parse_openapi_spec
from mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
)
from mcp_fingerprints.crawler import FingerprintGenerator
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.validator import McpServerValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verity.passport.sync")


def _create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_json(
    url: str,
    timeout: float = 8.0,
    headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch JSON from a remote URL with optional HTTP ETag caching.

    Returns (json_data, etag_header). If HTTP 304 Not Modified, returns (None, etag).
    """
    req_headers = {
        "User-Agent": "VerityRedTeam-MCPPassportSync/1.0",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=timeout) as resp:
            etag = resp.headers.get("ETag")
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, dict) else None, etag
    except urllib.error.HTTPError as he:
        if he.code == 304:
            return None, he.headers.get("ETag")
        logger.debug("HTTP %d for %s", he.code, url)
        return None, None
    except Exception as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
        return None, None


class ArchiveNotFoundError(Exception):
    """Raised when a repository or package returns 404 / Not Found."""
    pass


class PassportSynchronizer:
    """Synchronizes, discovers, and updates full-fidelity MCP Server Passports."""

    def _fetch_github_api_with_retry(self, url: str, timeout: float = 3.0, max_retries: int = 5) -> urllib.response.addinfourl:
        """Fetch from GitHub API with exponential backoff on HTTP 403 and 429."""
        backoff = 2.0
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"},
                )
                resp = urllib.request.urlopen(req, context=_create_ssl_context(), timeout=timeout)
                return resp
            except urllib.error.HTTPError as he:
                if he.code in (403, 429) and attempt < max_retries - 1:
                    reset_time_str = he.headers.get("x-ratelimit-reset")
                    if reset_time_str:
                        try:
                            reset_time = int(reset_time_str)
                            sleep_duration = max(1.0, reset_time - time.time() + 1.0)
                        except ValueError:
                            sleep_duration = backoff
                    else:
                        sleep_duration = backoff
                    
                    logger.warning("GitHub API rate limit hit (%d) for %s. Sleeping %.1f seconds...", he.code, url, sleep_duration)
                    time.sleep(sleep_duration)
                    backoff *= 2.0
                else:
                    raise
            except urllib.error.URLError as ue:
                if attempt < max_retries - 1:
                    logger.debug("URL Error %s for %s. Retrying in %.1fs...", ue.reason, url, backoff)
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    raise
        raise urllib.error.URLError("Max retries exceeded")

    def __init__(
        self,
        output_dir: str | Path = "data/fingerprints",
        state_file: str | Path | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = Path(state_file) if state_file else self.output_dir / "sync_state.json"
        self.state: dict[str, Any] = self._load_state()
        self._last_detected_gateway: dict[str, tuple[list[dict[str, Any]], dict[str, bool]]] = {}

    def _load_state(self) -> dict[str, Any]:
        if self.state_file.is_file():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "version": "1.0.0",
            "last_sync_utc": None,
            "total_passports": 0,
            "sources": {
                "smithery": {"last_page": 1, "total_synced": 0},
                "npm": {"total_synced": 0},
                "pypi": {"total_synced": 0},
            },
        }

    def _save_state(self) -> None:
        self.state["last_sync_utc"] = datetime.datetime.now(datetime.UTC).isoformat()
        self.state["total_passports"] = len(list(self.output_dir.rglob("*.json"))) - (
            1 if self.state_file.is_file() else 0
        )
        self.state_file.write_text(
            json.dumps(self.state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )



    def _detect_remote_gateway(self, code: str) -> tuple[list[dict[str, Any]], dict[str, bool]]:
        """Detect remote streamable-HTTP or SSE MCP gateway endpoints in JavaScript/TypeScript code."""
        conns: list[dict[str, Any]] = []
        caps: dict[str, bool] = {}
        if not code:
            return conns, caps

        # Pattern 1: Direct MCP/SSE endpoint URLs
        m1 = re.search(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::[0-9]+)?/(?:mcp|sse|v1/mcp)', code)
        # Pattern 2: Process.env fallbacks (e.g. process.env.MCP_URL || 'https://...')
        m2 = re.search(r'process\.env\.[a-zA-Z0-9_]*URL\s*\|\|\s*[\'"](https?://[^\'"]+)[\'"]', code)

        url = None
        if m1:
            url = m1.group(0)
        elif m2:
            url = m2.group(1)

        if url:
            conns.append({
                "type": "streamable-http",
                "deploymentUrl": url,
                "configSchema": {},
            })
            caps["proxy_gateway"] = True
            caps["remote_endpoint"] = True

        return conns, caps

    def _detect_remote_gateway_from_npm_tarball(
        self, package_name: str, dist_tarball_url: str | None = None
    ) -> tuple[list[dict[str, Any]], dict[str, bool]]:
        """Inspect JS/TS source code inside npm tarball to detect remote streamable-HTTP or SSE MCP endpoints."""
        if package_name in self._last_detected_gateway:
            return self._last_detected_gateway[package_name]

        if not dist_tarball_url:
            encoded_pkg = package_name.replace("/", "%2F")
            url = f"https://registry.npmjs.org/{encoded_pkg}"
            req = urllib.request.Request(
                url, headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0", "Accept": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=5.0) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    latest_version = data.get("dist-tags", {}).get("latest")
                    dist_tarball_url = data.get("versions", {}).get(latest_version, {}).get("dist", {}).get("tarball")
            except Exception as e:
                logger.warning(f"Error fetching npm metadata for gateway probe of {package_name}: {e}")
                return [], {}

        if not dist_tarball_url:
            return [], {}

        req = urllib.request.Request(dist_tarball_url, headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"})
        try:
            with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=2.5) as response:
                tarball_data = bytearray()
                MAX_SIZE = 10 * 1024 * 1024
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    tarball_data.extend(chunk)
                    if len(tarball_data) > MAX_SIZE:
                        return [], {}
        except Exception as e:
            logger.warning(f"Error downloading tarball for gateway probe of {package_name}: {e}")
            return [], {}

        buf = io.BytesIO(tarball_data)
        try:
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                members = [m for m in tar.getmembers() if m.isfile()]
                for member in members:
                    if not member.name.endswith((".js", ".mjs", ".ts", ".cjs")):
                        continue
                    f_obj = tar.extractfile(member)
                    if f_obj:
                        code = f_obj.read(500 * 1024).decode("utf-8", errors="ignore")
                        conns, caps = self._detect_remote_gateway(code)
                        if conns:
                            self._last_detected_gateway[package_name] = (conns, caps)
                            return conns, caps
        except Exception as e:
            logger.warning(f"Tar error inspecting gateway in {package_name}: {e}")
            return [], {}

        return [], {}

    def _extract_tools_from_pypi_package(self, package_name: str) -> list[dict[str, Any]]:
        url = f"https://pypi.org/pypi/{package_name}/json"
        req = urllib.request.Request(
            url, headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0", "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=3.0) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            if he.code in (404, 410):
                raise ArchiveNotFoundError(f"PyPI package {package_name} not found ({he.code})")
            logger.warning(f"Error fetching PyPI metadata for {package_name}: {he}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching PyPI metadata for {package_name}: {e}")
            return []

        urls = data.get("urls", [])
        if not urls:
            return []

        # Prioritize wheel over sdist
        target_url = None
        target_type = None
        for u in urls:
            if u.get("packagetype") == "bdist_wheel":
                target_url = u.get("url")
                target_type = "wheel"
                break
        
        if not target_url:
            for u in urls:
                if u.get("packagetype") == "sdist":
                    target_url = u.get("url")
                    target_type = "sdist"
                    break

        if not target_url:
            return []

        req = urllib.request.Request(target_url, headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"})
        try:
            with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=3.0) as response:
                archive_data = bytearray()
                MAX_SIZE = 10 * 1024 * 1024
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    archive_data.extend(chunk)
                    if len(archive_data) > MAX_SIZE:
                        logger.warning(f"Archive for {package_name} exceeded 10MB limit, skipping.")
                        return []
        except Exception as e:
            logger.warning(f"Error downloading archive for {package_name}: {e}")
            return []

        buf = io.BytesIO(archive_data)
        extracted_tools = []
        seen_tool_names = set()

        if target_type == "wheel":
            import zipfile
            try:
                with zipfile.ZipFile(buf, "r") as zf:
                    for name in zf.namelist():
                        if name.endswith(".py") and not name.split("/")[-1].startswith("test"):
                            code = zf.read(name).decode("utf-8", errors="ignore")
                            tools = parse_python_mcp_ast(code)
                            for t in tools:
                                if t.get("name") not in seen_tool_names:
                                    seen_tool_names.add(t.get("name"))
                                    extracted_tools.append(t)
            except zipfile.BadZipFile as e:
                logger.warning(f"Zip error extracting {package_name}: {e}")
        elif target_type == "sdist":
            import tarfile
            try:
                buf.seek(0)
                with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                    for member in tar.getmembers():
                        if not member.isfile():
                            continue
                        name = member.name
                        if name.endswith(".py") and not name.split("/")[-1].startswith("test"):
                            f_obj = tar.extractfile(member)
                            if f_obj:
                                code = f_obj.read().decode("utf-8", errors="ignore")
                                tools = parse_python_mcp_ast(code)
                                for t in tools:
                                    if t.get("name") not in seen_tool_names:
                                        seen_tool_names.add(t.get("name"))
                                        extracted_tools.append(t)
            except tarfile.TarError as e:
                logger.warning(f"Tar error extracting {package_name}: {e}")

        return extracted_tools

    def _extract_tools_from_npm_tarball(
        self, package_name: str, dist_tarball_url: str | None = None
    ) -> list[dict[str, Any]]:
        if not dist_tarball_url:
            encoded_pkg = package_name.replace("/", "%2F")
            url = f"https://registry.npmjs.org/{encoded_pkg}"
            req = urllib.request.Request(
                url, headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0", "Accept": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=5.0) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    latest_version = data.get("dist-tags", {}).get("latest")
                    dist_tarball_url = data.get("versions", {}).get(latest_version, {}).get("dist", {}).get("tarball")
            except urllib.error.HTTPError as he:
                if he.code in (404, 410):
                    raise ArchiveNotFoundError(f"npm package {package_name} not found ({he.code})")
                logger.warning(f"Error fetching npm metadata for {package_name}: {he}")
                return []
            except Exception as e:
                logger.warning(f"Error fetching npm metadata for {package_name}: {e}")
                return []

        if not dist_tarball_url:
            return []

        req = urllib.request.Request(dist_tarball_url, headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"})
        try:
            with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=2.5) as response:
                tarball_data = bytearray()
                # Enforce 10MB limit
                MAX_SIZE = 10 * 1024 * 1024
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    tarball_data.extend(chunk)
                    if len(tarball_data) > MAX_SIZE:
                        logger.warning(f"Tarball for {package_name} exceeded 10MB limit, skipping.")
                        return []
        except Exception as e:
            logger.warning(f"Error downloading tarball for {package_name}: {e}")
            return []

        buf = io.BytesIO(tarball_data)
        try:
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                members = [m for m in tar.getmembers() if m.isfile()]

                priority_suffixes = [
                    "package/index.js", "package/index.ts", "package/index.mjs",
                    "package/dist/index.js", "package/dist/index.ts", "package/dist/index.mjs",
                    "package/build/index.js", "package/build/index.ts", "package/build/index.mjs",
                    "package/lib/index.js", "package/lib/index.ts", "package/lib/index.mjs",
                    "package/bin/index.js", "package/bin/index.ts", "package/bin/index.mjs",
                    "package/server.js", "package/server.ts", "package/server.mjs",
                    "package/dist/server.js", "package/dist/server.ts", "package/dist/server.mjs"
                ]
                
                def member_priority(m: tarfile.TarInfo) -> tuple[int, int]:
                    if m.name in priority_suffixes:
                        return (0, priority_suffixes.index(m.name))
                    return (1, 0)

                members.sort(key=member_priority)
                
                extracted_tools = []
                seen_tool_names = set()

                for member in members:
                    name = member.name
                    if not name.endswith((".js", ".mjs", ".ts")):
                        continue
                    parts = name.split("/")
                    if len(parts) >= 2 and parts[0] == "package":
                        if parts[1] in ("dist", "build", "src", "lib", "bin") or len(parts) == 2:
                            f_obj = tar.extractfile(member)
                            if f_obj:
                                code = f_obj.read(500 * 1024).decode("utf-8", errors="ignore")
                                g_conns, g_caps = self._detect_remote_gateway(code)
                                if g_conns and package_name not in self._last_detected_gateway:
                                    self._last_detected_gateway[package_name] = (g_conns, g_caps)
                                tools = parse_typescript_mcp_ast(code)
                                for t in tools:
                                    t_name = t.get("name")
                                    if t_name not in seen_tool_names:
                                        seen_tool_names.add(t_name)
                                        extracted_tools.append(t)
                                if extracted_tools:
                                    return extracted_tools

                if not extracted_tools:
                    spec_suffixes = (
                        "openapi.json", "swagger.json", "openapi.yaml", "openapi.yml", "swagger.yaml", "swagger.yml"
                    )
                    for member in members:
                        lower_name = member.name.lower()
                        if any(lower_name.endswith(suffix) for suffix in spec_suffixes):
                            f_obj = tar.extractfile(member)
                            if f_obj:
                                spec_content = f_obj.read(1024 * 1024).decode("utf-8", errors="ignore")
                                tools = parse_openapi_spec(spec_content)
                                for t in tools:
                                    t_name = t.get("name")
                                    if t_name not in seen_tool_names:
                                        seen_tool_names.add(t_name)
                                        extracted_tools.append(t)
                                if extracted_tools:
                                    return extracted_tools
        except tarfile.TarError as e:
            logger.warning(f"Tar error extracting {package_name}: {e}")
            return []

        return []

    def _extract_ast_tools_from_github(
        self,
        package_name: str,
        repo_url: str | None = None,
    ) -> list[dict[str, Any]]:
        """Attempt to statically extract MCP tool signatures from GitHub repository entrypoints."""
        owner = None
        repo = None

        if repo_url:
            m = re.search(r"github\.com/([^/]+)/([^/#?]+)", repo_url)
            if m:
                owner = m.group(1)
                repo = m.group(2).removesuffix(".git")

        if not owner and "/" in package_name and not package_name.startswith("@"):
            parts = package_name.split("/")
            if len(parts) == 2:
                owner, repo = parts[0], parts[1]

        if not owner or not repo:
            return []

        for branch in ("main", "master"):
            aggregated_tools = []
            seen_tool_names = set()
            tree_api_success = False

            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            try:
                with self._fetch_github_api_with_retry(tree_url) as resp:
                    if resp.status == 200:
                        import json
                        tree_data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                        tree_api_success = True
                        
                        target_filenames = {
                            "server.py", "main.py", "app.py", "index.ts", "server.ts", "index.js",
                            "cli.ts", "mcp.py", "tools.ts", "tools.py", "tool.ts", "tool.py",
                            "main.go", "server.go", "mcp.go", "main.rs", "lib.rs", "server.rs",
                            "Program.cs", "Server.cs", "Tools.cs", "McpServer.cs",
                            "McpTools.java", "Server.java", "Tools.java", "App.java",
                            "Server.kt", "Tools.kt", "Main.kt",
                            "openapi.json", "swagger.json", "openapi.yaml", "openapi.yml", "swagger.yaml", "swagger.yml"
                        }
                        all_tree_paths = [
                            entry.get("path", "") 
                            for entry in tree_data.get("tree", []) 
                            if entry.get("type") == "blob"
                        ]
                        subpackage_prefix = match_monorepo_subpackage_dir(package_name, all_tree_paths)

                        candidate_files = []
                        for entry in tree_data.get("tree", []):
                            if entry.get("type") == "blob":
                                p = entry.get("path", "")
                                
                                if subpackage_prefix and not p.startswith(subpackage_prefix):
                                    continue
                                parts = p.split("/")
                                if len(parts) > 4:
                                    continue
                                filename = parts[-1]
                                match1 = re.search(r'(^|/)tools/.*\.(ts|js|mjs|py|go|rs|java|kt|cs)$', p)
                                match2 = re.search(r'(^|/)mcp/.*\.(py|ts|js|go|rs|java|kt|cs)$', p)
                                match3 = re.search(r'^src/handlers/.*\.(ts|js|go|rs|java|kt|cs)$', p)
                                match4 = re.search(r'.*tool.*\.(py|java|kt|cs)$', filename, re.IGNORECASE)
                                match5 = re.search(r'(openapi|swagger).*\.(json|yaml|yml)$', filename, re.IGNORECASE)
                                if filename in target_filenames or match1 or match2 or match3 or match4 or match5:
                                    score = 10
                                    if "packages/" in p or "servers/" in p or "src/" in p:
                                        score -= 2
                                    pkg_last_part = package_name.split("/")[-1]
                                    if pkg_last_part and pkg_last_part in p:
                                        score -= 3
                                    if "/tools/" in f"/{p}":
                                        score -= 2
                                    candidate_files.append((score, p))
                                    
                        candidate_files.sort(key=lambda x: x[0])
                        candidate_files = [p for _, p in candidate_files]
                        candidate_files = candidate_files[:5]
                        
                        for p in candidate_files:
                            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{p}"
                            try:
                                req_raw = urllib.request.Request(
                                    raw_url,
                                    headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"},
                                )
                                with urllib.request.urlopen(req_raw, context=_create_ssl_context(), timeout=3.0) as raw_resp:
                                    if raw_resp.status == 200:
                                        code = raw_resp.read(500 * 1024).decode("utf-8", errors="ignore")
                                        if p.endswith((".json", ".yaml", ".yml")):
                                            extracted = parse_openapi_spec(code)
                                        else:
                                            lang = p.split('.')[-1]
                                            if lang == "mjs": lang = "js"
                                            extracted = parse_mcp_source_code(code, language=lang)
                                        for tool in extracted:
                                            if tool.get("name") not in seen_tool_names:
                                                seen_tool_names.add(tool.get("name"))
                                                aggregated_tools.append(tool)
                            except Exception:
                                continue
            except urllib.error.HTTPError as e:
                pass
            except Exception:
                pass

            if tree_api_success:
                if aggregated_tools:
                    return aggregated_tools
                # If tree API succeeded but found no tools on this branch, we should try the next branch.
                continue
                
            # If tree API didn't succeed (e.g. 403, 404), fall back to existing logic

            candidates = []
            
            # Dynamic probe package.json
            pkg_json_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/package.json"
            try:
                req = urllib.request.Request(
                    pkg_json_url,
                    headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"},
                )
                with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=2.5) as resp:
                    if resp.status == 200:
                        import json
                        pj = json.loads(resp.read().decode("utf-8", errors="ignore"))
                        
                        dynamic_paths = []
                        for field in ("main", "module", "source"):
                            if isinstance(pj.get(field), str):
                                dynamic_paths.append(pj[field])
                        
                        if "bin" in pj:
                            if isinstance(pj["bin"], str):
                                dynamic_paths.append(pj["bin"])
                            elif isinstance(pj["bin"], dict):
                                dynamic_paths.extend(pj["bin"].values())
                        
                        if "exports" in pj:
                            exports = pj["exports"]
                            if isinstance(exports, str):
                                dynamic_paths.append(exports)
                            elif isinstance(exports, dict):
                                def get_export_paths(d):
                                    for v in d.values():
                                        if isinstance(v, str):
                                            dynamic_paths.append(v)
                                        elif isinstance(v, dict):
                                            get_export_paths(v)
                                get_export_paths(exports)
                        
                        for p in dynamic_paths:
                            if not isinstance(p, str):
                                continue
                            p = p.lstrip("./")
                            # Map compiled path to source equivalents
                            m_path = re.sub(r'^(dist|build|lib)/', 'src/', p)
                            m_path = re.sub(r'\.(js|cjs|mjs|d\.ts)$', '', m_path)
                            if m_path != p:
                                candidates.append((f"{m_path}.ts", "ts"))
                                candidates.append((f"{m_path}.js", "js"))
                                # Also try root without src/
                                root_path = m_path.removeprefix("src/")
                                if root_path != m_path:
                                    candidates.append((f"{root_path}.ts", "ts"))
                                    candidates.append((f"{root_path}.js", "js"))
            except Exception:
                pass

            candidates.extend([
                ("src/tools.ts", "ts"),
                ("src/index.ts", "ts"),
                ("src/server.ts", "ts"),
                ("index.ts", "ts"),
                ("server.ts", "ts"),
                ("server.py", "py"),
                ("src/server.py", "py"),
                ("main.py", "py"),
                ("src/tools.js", "js"),
                ("src/index.js", "js"),
                ("src/tools/index.ts", "ts"),
                ("src/tools/index.js", "js"),
                ("src/handlers.ts", "ts"),
                ("src/handlers/index.ts", "ts"),
                ("src/server/index.ts", "ts"),
                ("src/mcp/server.ts", "ts"),
                ("main.go", "go"),
                ("server.go", "go"),
                ("mcp.go", "go"),
                ("src/main.rs", "rs"),
                ("src/lib.rs", "rs"),
                ("Program.cs", "cs"),
                ("src/Program.cs", "cs"),
                ("Server.cs", "cs"),
                ("src/Server.cs", "cs"),
                ("src/main/java/Server.java", "java"),
                ("src/main/kotlin/Server.kt", "kt"),
                ("openapi.json", "json"),
                ("swagger.json", "json"),
                ("openapi.yaml", "yaml"),
                ("swagger.yaml", "yaml"),
            ])

            # Deduplicate preserving order
            seen = set()
            unique_candidates = []
            for path, lang in candidates:
                if path not in seen:
                    seen.add(path)
                    unique_candidates.append((path, lang))

            for path, lang in unique_candidates:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                try:
                    req = urllib.request.Request(
                        raw_url,
                        headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"},
                    )
                    with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=2.5) as resp:
                        if resp.status == 200:
                            code = resp.read().decode("utf-8", errors="ignore")
                            extracted = parse_mcp_source_code(code, language=lang)
                            if extracted:
                                return extracted
                except Exception:
                    continue

        # If zero tools were found, check if repository itself is 404 / deleted / inaccessible
        repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            with self._fetch_github_api_with_retry(repo_api_url) as resp:
                pass
        except urllib.error.HTTPError as he:
            if he.code in (404, 410):
                raise ArchiveNotFoundError(f"GitHub repository {owner}/{repo} not found ({he.code})")
        except Exception:
            pass

        return []

    def _extract_tools_from_github_readme(
        self,
        package_name: str,
        repo_url: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fallback tool extraction by parsing README.md documentation."""
        owner = None
        repo = None

        if repo_url:
            m = re.search(r"github\.com/([^/]+)/([^/#?]+)", repo_url)
            if m:
                owner = m.group(1)
                repo = m.group(2).removesuffix(".git")

        if not owner and "/" in package_name and not package_name.startswith("@"):
            parts = package_name.split("/")
            if len(parts) == 2:
                owner, repo = parts[0], parts[1]

        if not owner or not repo:
            return []

        for branch in ("main", "master"):
            for filename in ("README.md", "readme.md"):
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
                try:
                    req = urllib.request.Request(
                        raw_url,
                        headers={"User-Agent": "VerityRedTeam-MCPPassportSync/1.0"},
                    )
                    with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=3.0) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="ignore")
                            tools = parse_markdown_tool_docs(content)
                            if tools:
                                return tools
                except Exception:
                    continue
        return []

    def merge_and_enrich_passport(
        self,
        package_name: str,
        ecosystem: str = "npm",
        smithery_data: dict[str, Any] | None = None,
        npm_data: dict[str, Any] | None = None,
        pypi_data: dict[str, Any] | None = None,
        official_registry_data: dict[str, Any] | None = None,
        existing_spec: ServerPackageSpec | None = None,
        is_curated_source: bool = False,
        auto_cross_resolve: bool = True,
        pre_extracted_tools: list[dict[str, Any]] | None = None,
        pre_extracted_connections: list[dict[str, Any]] | None = None,
        pre_extracted_capabilities: dict[str, bool] | None = None,
        pre_extracted_source: str | None = None,
    ) -> ServerPackageSpec | None:
        """Merge complementary metadata from Smithery, npm, and PyPI into one Passport."""
        sources: list[str] = list(existing_spec.sources_merged) if existing_spec else []
        if pre_extracted_source and pre_extracted_source not in sources:
            sources.append(pre_extracted_source)

        # Auto cross-resolve runtime tool contracts from Smithery if not provided
        if not smithery_data and auto_cross_resolve:
            s_names = [package_name]
            if "/" in package_name:
                s_names.append(package_name.split("/")[-1])
            for s_name in s_names:
                s_detail, _ = fetch_json(f"https://api.smithery.ai/servers/{s_name}")
                if s_detail and isinstance(s_detail, dict) and "tools" in s_detail:
                    smithery_data = s_detail
                    break
        tools: list[dict[str, Any]] = list(pre_extracted_tools or [])
        prompts: list[dict[str, Any]] = []
        resources: list[dict[str, Any]] = []
        connections: list[dict[str, Any]] = list(pre_extracted_connections or [])
        extra_capabilities: dict[str, bool] = dict(pre_extracted_capabilities or {})
        desc = ""
        repo_url = None
        license_str = None
        keywords: list[str] = []
        aliases: list[str] = [package_name]
        dist_tags: dict[str, str] = {}
        all_versions: list[VersionFingerprint] = []

        # 0. Index existing version fingerprints to preserve exact historical hashes
        existing_version_map: dict[str, VersionFingerprint] = {}
        if existing_spec:
            for v in existing_spec.versions:
                existing_version_map[v.version] = v

        # 1. Ingest Smithery runtime tools
        is_simulated = False
        if smithery_data:
            if not smithery_data.get("_is_simulated"):
                sources.append("smithery")
            else:
                is_simulated = True
            if smithery_data.get("tools"):
                tools = [t for t in (smithery_data.get("tools") or []) if isinstance(t, dict)]
            prompts = [p for p in (smithery_data.get("prompts") or []) if isinstance(p, dict)]
            resources = [r for r in (smithery_data.get("resources") or []) if isinstance(r, dict)]
            if smithery_data.get("connections"):
                connections = [
                    c for c in (smithery_data.get("connections") or []) if isinstance(c, dict)
                ]
            desc = smithery_data.get("description") or smithery_data.get("displayName") or ""
            repo_url = (
                smithery_data.get("deploymentUrl") or f"https://smithery.ai/servers/{package_name}"
            )
            q_name = smithery_data.get("qualifiedName")
            if q_name and q_name not in aliases:
                aliases.append(q_name)

        # 2. Ingest npm timeline & dependencies
        if npm_data:
            sources.append("npm_registry")
            dist_tags = npm_data.get("dist-tags", {})
            if not desc:
                desc = npm_data.get("description", "")
            license_str = npm_data.get("license")
            author_obj = npm_data.get("author")
            (author_obj.get("name") if isinstance(author_obj, dict) else str(author_obj or ""))
            repo_raw = npm_data.get("homepage") or npm_data.get("bugs", {}).get("url")
            if repo_raw:
                repo_url = repo_raw
            keywords.extend(npm_data.get("keywords", []))

            # Build versions from npm
            time_map = npm_data.get("time", {})
            versions_dict = npm_data.get("versions", {})
            for v_str, v_info in versions_dict.items():
                if not re.match(r"^\d+\.\d+", v_str):
                    continue
                v_deps = v_info.get("dependencies", {})
                v_date = time_map.get(v_str)

                # If version already exists in existing_spec with signatures, preserve it
                if v_str in existing_version_map and existing_version_map[v_str].tool_signatures:
                    all_versions.append(existing_version_map[v_str])
                    continue

                v_tools = tools if v_str == dist_tags.get("latest", v_str) else []
                v_caps = {
                    "tools": bool(v_tools),
                    "prompts": bool(prompts),
                    "resources": bool(resources),
                    **extra_capabilities,
                }
                if v_tools and is_simulated:
                    v_caps["inherited_tools"] = True
                elif v_tools:
                    v_caps["verified_tools"] = True

                v_fp = build_version_fingerprint(
                    version=v_str,
                    tools=v_tools,
                    prompts=prompts if v_tools else None,
                    resources=resources if v_tools else None,
                    release_date=v_date,
                    capabilities=v_caps,
                )
                v_fp_dict = v_fp.to_dict()
                v_fp_dict["dependencies"] = v_deps
                v_fp_dict["connections"] = connections if (v_tools or extra_capabilities.get("proxy_gateway")) else []
                all_versions.append(VersionFingerprint.from_dict(v_fp_dict))

        # 3. Ingest PyPI timeline & dependencies
        if pypi_data:
            sources.append("pypi")
            info = pypi_data.get("info", {})
            if not desc:
                desc = info.get("summary", "")
            license_str = info.get("license")
            info.get("author")
            repo_url = info.get("home_page") or info.get("project_url")
            releases = pypi_data.get("releases", {})
            latest_v = info.get("version", "1.0.0")
            for v_str, r_list in releases.items():
                if not re.match(r"^\d+\.\d+", v_str):
                    continue
                # If version already exists in existing_spec with signatures, preserve it
                if v_str in existing_version_map and existing_version_map[v_str].tool_signatures:
                    all_versions.append(existing_version_map[v_str])
                    continue
                v_date = r_list[0].get("upload_time_iso_8601") if r_list else None
                v_tools = tools if v_str == latest_v else []
                v_caps = {
                    "tools": bool(v_tools),
                    "prompts": bool(prompts),
                    "resources": bool(resources),
                }
                if v_tools and is_simulated:
                    v_caps["inherited_tools"] = True
                elif v_tools:
                    v_caps["verified_tools"] = True
                v_fp = build_version_fingerprint(
                    version=v_str,
                    tools=v_tools,
                    prompts=prompts if v_tools else None,
                    resources=resources if v_tools else None,
                    release_date=v_date,
                    capabilities=v_caps,
                )
                all_versions.append(v_fp)

        # 3.5. Ingest GitHub / Curated metadata
        if is_curated_source and "github" not in sources:
            sources.append("github")

        # 4. Ingest Official MCP Registry metadata
        if official_registry_data:
            sources.append("official_registry")
            srv = official_registry_data.get("server", {})
            if not desc:
                desc = srv.get("description", "")
            title = srv.get("title")
            if title and title not in aliases:
                aliases.append(title)
            repo_info = srv.get("repository", {})
            if repo_info and isinstance(repo_info, dict) and repo_info.get("url"):
                repo_url = repo_info.get("url")
            website = srv.get("websiteUrl")
            if website and not repo_url:
                repo_url = website
            remotes = srv.get("remotes", [])
            for rem in remotes:
                if isinstance(rem, dict):
                    connections.append(
                        {
                            "type": rem.get("type", "http"),
                            "deploymentUrl": rem.get("url"),
                            "configSchema": {},
                        }
                    )

        # Auto cross-resolve runtime tool contracts from GitHub AST if Smithery yielded no tools
        if not tools and auto_cross_resolve:
            check_repo = repo_url or (existing_spec.repository_url if existing_spec else None)
            try:
                ast_tools = self._extract_ast_tools_from_github(package_name, check_repo)
                if ast_tools:
                    tools = ast_tools
                    if "github_ast" not in sources:
                        sources.append("github_ast")
            except ArchiveNotFoundError:
                extra_capabilities["is_archived"] = True
                extra_capabilities["http_status"] = 404
                extra_capabilities["archival_reason"] = "Repository or package returned HTTP 404/Not Found"

        if official_registry_data:
            srv = official_registry_data.get("server", {})
            reg_v = srv.get("version", "1.0.0")
            if not all_versions:
                v_fp = build_version_fingerprint(
                    version=reg_v,
                    tools=tools,
                    prompts=prompts,
                    resources=resources,
                    capabilities={
                        "tools": bool(tools),
                        "prompts": bool(prompts),
                        "resources": bool(resources),
                        **extra_capabilities,
                    },
                )
                v_fp_dict = v_fp.to_dict()
                v_fp_dict["connections"] = connections
                all_versions.append(VersionFingerprint.from_dict(v_fp_dict))

        # If no multi-version releases (e.g. standalone Smithery/catalog server), preserve existing versions and add/update target version
        if not all_versions:
            if existing_spec and existing_spec.versions:
                all_versions.extend(existing_spec.versions)
            s_ver = (smithery_data.get("version") if smithery_data else None) or "1.0.0"
            existing_target = next((v for v in all_versions if v.version == s_ver), None)
            if not existing_target:
                v_caps = {
                    "tools": bool(tools),
                    "prompts": bool(prompts),
                    "resources": bool(resources),
                    **extra_capabilities,
                }
                if tools:
                    v_caps["verified_tools"] = not is_simulated
                    if is_simulated:
                        v_caps["inherited_tools"] = True
                ver_fp = build_version_fingerprint(
                    version=s_ver,
                    tools=tools,
                    prompts=prompts,
                    resources=resources,
                    capabilities=v_caps,
                )
                v_fp_dict = ver_fp.to_dict()
                v_fp_dict["connections"] = connections
                all_versions.append(VersionFingerprint.from_dict(v_fp_dict))
            elif (tools or connections or extra_capabilities) and (
                (not existing_target.tool_signatures and not existing_target.connections)
                or extra_capabilities
            ):
                # Target version exists, hydrate with new tools/connections/capabilities
                all_versions.remove(existing_target)
                v_caps = dict(existing_target.capabilities)
                if tools:
                    v_caps["tools"] = bool(tools)
                    v_caps["verified_tools"] = not is_simulated
                v_caps.update(extra_capabilities)
                ver_fp = build_version_fingerprint(
                    version=s_ver,
                    tools=tools or [t.to_dict() for t in existing_target.tool_signatures],
                    prompts=prompts or [p.to_dict() for p in existing_target.prompt_signatures],
                    resources=resources or [r.to_dict() for r in existing_target.resource_signatures],
                    release_date=existing_target.release_date,
                    capabilities=v_caps,
                )
                v_fp_dict = ver_fp.to_dict()
                v_fp_dict["connections"] = connections or existing_target.connections
                v_fp_dict["dependencies"] = existing_target.dependencies
                all_versions.append(VersionFingerprint.from_dict(v_fp_dict))

        # Hydrate existing versions if tools/connections/capabilities were newly discovered and existing versions lacked them
        if (tools or connections or extra_capabilities) and all_versions and (
            (tools and not any(bool(v.tool_signatures) for v in all_versions))
            or (connections and not any(bool(v.connections) for v in all_versions))
            or bool(extra_capabilities)
        ):
            latest_idx = len(all_versions) - 1
            if dist_tags.get("latest"):
                for idx, v in enumerate(all_versions):
                    if v.version == dist_tags["latest"]:
                        latest_idx = idx
                        break
            old_target = all_versions[latest_idx]
            v_caps = dict(old_target.capabilities)
            if tools:
                v_caps["tools"] = True
                v_caps["verified_tools"] = not is_simulated
            v_caps.update(extra_capabilities)
            hydrated_fp = build_version_fingerprint(
                version=old_target.version,
                tools=tools or [t.to_dict() for t in old_target.tool_signatures],
                prompts=prompts or [p.to_dict() for p in old_target.prompt_signatures],
                resources=resources or [r.to_dict() for r in old_target.resource_signatures],
                release_date=old_target.release_date,
                capabilities=v_caps,
            )
            h_dict = hydrated_fp.to_dict()
            h_dict["connections"] = connections or old_target.connections
            h_dict["dependencies"] = old_target.dependencies
            all_versions[latest_idx] = VersionFingerprint.from_dict(h_dict)

        # Validate with McpServerValidator
        all_deps = {}
        for v in all_versions:
            if v.dependencies:
                all_deps.update(v.dependencies)

        clean_pkg_name = package_name.strip()
        is_valid, reason = McpServerValidator.is_valid_mcp_server(
            package_name=clean_pkg_name,
            ecosystem=ecosystem,
            dependencies=all_deps if all_deps else None,
            keywords=keywords,
            description=desc,
            has_tools_declared=bool(tools) or any(bool(v.tool_signatures) for v in all_versions) or bool(connections) or any(bool(v.connections) for v in all_versions) or bool(existing_spec),
            is_curated_source=is_curated_source,
        )
        if not is_valid:
            logger.info("Skipping invalid/non-MCP package %s (%s)", clean_pkg_name, reason)
            return None

        # Ensure all versions have a valid version string
        sanitized_versions = []
        for v in all_versions:
            if not v.version or not str(v.version).strip():
                v_dict = v.to_dict()
                v_dict["version"] = "1.0.0"
                sanitized_versions.append(VersionFingerprint.from_dict(v_dict))
            else:
                sanitized_versions.append(v)

        purl = f"pkg:{ecosystem.lower()}/{clean_pkg_name.replace('/', '%2F')}"
        return ServerPackageSpec(
            package_name=clean_pkg_name,
            purl=purl,
            ecosystem=ecosystem,
            display_name=clean_pkg_name,
            description=desc,
            repository_url=repo_url,
            license=license_str,
            keywords=tuple(sorted(set(keywords))),
            aliases=tuple(sorted(set(aliases))),
            sources_merged=tuple(sorted(set(sources))),
            dist_tags=dist_tags,
            versions=tuple(sorted(sanitized_versions, key=lambda x: x.version)),
        )

    @staticmethod
    def _extract_prior_tools(
        spec: ServerPackageSpec,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        existing_tools: list[dict[str, Any]] = []
        existing_prompts: list[dict[str, Any]] = []
        existing_resources: list[dict[str, Any]] = []
        for v in reversed(spec.versions):
            if v.tool_signatures and not existing_tools:
                existing_tools = [t.to_dict() for t in v.tool_signatures]
            if v.prompt_signatures and not existing_prompts:
                existing_prompts = [p.to_dict() for p in v.prompt_signatures]
            if v.resource_signatures and not existing_resources:
                existing_resources = [r.to_dict() for r in v.resource_signatures]
        return existing_tools, existing_prompts, existing_resources

    def update_existing_passports(self) -> int:
        """Scan all passport files in data/fingerprints/ and check for upstream version updates across npm, PyPI, and Smithery."""
        updated_count = 0
        for j_file in sorted(self.output_dir.rglob("*.json")):
            if j_file.name in ("sync_state.json", "index.json"):
                continue
            try:
                spec = ServerPackageSpec.from_dict(json.loads(j_file.read_text(encoding="utf-8")))
                pkg_name = spec.package_name
                eco = spec.ecosystem.lower()

                # Check upstream for new versions
                if eco == "npm" or "npm_registry" in spec.sources_merged:
                    npm_meta, _ = fetch_json(
                        f"https://registry.npmjs.org/{pkg_name}",
                        headers={"Accept": "application/vnd.npm.install-v1+json"},
                    )
                    if npm_meta and "dist-tags" in npm_meta:
                        latest_dist = npm_meta["dist-tags"].get("latest")
                        known_versions = {v.version for v in spec.versions}
                        if latest_dist and latest_dist not in known_versions:
                            logger.info(
                                "Found NEW version for npm %s: %s (was %s)",
                                pkg_name,
                                latest_dist,
                                known_versions,
                            )
                            e_tools, e_prompts, e_resources = self._extract_prior_tools(spec)
                            smithery_simulated = (
                                {
                                    "tools": e_tools,
                                    "prompts": e_prompts,
                                    "resources": e_resources,
                                    "_is_simulated": True,
                                }
                                if e_tools
                                else None
                            )
                            merged_spec = self.merge_and_enrich_passport(
                                package_name=pkg_name,
                                ecosystem="npm",
                                npm_data=npm_meta,
                                smithery_data=smithery_simulated,
                                existing_spec=spec,
                            )
                            if merged_spec:
                                FingerprintGenerator.save_spec_to_file(merged_spec, j_file)
                                updated_count += 1
                elif eco in ("pypi", "python") or "pypi" in spec.sources_merged:
                    pypi_meta, _ = fetch_json(f"https://pypi.org/pypi/{pkg_name}/json")
                    if pypi_meta and "info" in pypi_meta:
                        latest_dist = pypi_meta["info"].get("version")
                        known_versions = {v.version for v in spec.versions}
                        if latest_dist and latest_dist not in known_versions:
                            logger.info(
                                "Found NEW version for PyPI %s: %s (was %s)",
                                pkg_name,
                                latest_dist,
                                known_versions,
                            )
                            e_tools, e_prompts, e_resources = self._extract_prior_tools(spec)
                            smithery_simulated = (
                                {
                                    "tools": e_tools,
                                    "prompts": e_prompts,
                                    "resources": e_resources,
                                    "_is_simulated": True,
                                }
                                if e_tools
                                else None
                            )
                            merged_spec = self.merge_and_enrich_passport(
                                package_name=pkg_name,
                                ecosystem="pypi",
                                pypi_data=pypi_meta,
                                smithery_data=smithery_simulated,
                                existing_spec=spec,
                            )
                            if merged_spec:
                                FingerprintGenerator.save_spec_to_file(merged_spec, j_file)
                                updated_count += 1
                elif eco == "smithery" or "smithery" in spec.sources_merged:
                    s_detail, _ = fetch_json(f"https://api.smithery.ai/servers/{pkg_name}")
                    if s_detail and isinstance(s_detail, dict):
                        s_ver = s_detail.get("version")
                        known_versions = {v.version for v in spec.versions}
                        if s_ver and s_ver not in known_versions:
                            logger.info(
                                "Found NEW version for Smithery %s: %s (was %s)",
                                pkg_name,
                                s_ver,
                                known_versions,
                            )
                            merged_spec = self.merge_and_enrich_passport(
                                package_name=pkg_name,
                                ecosystem="smithery",
                                smithery_data=s_detail,
                                existing_spec=spec,
                            )
                            if merged_spec:
                                FingerprintGenerator.save_spec_to_file(merged_spec, j_file)
                                updated_count += 1
            except Exception as exc:
                logger.debug("Error checking updates for %s: %s", j_file.name, exc)
        logger.info("Updated %d existing passports with new release versions", updated_count)
        self._save_state()
        return updated_count

    def enrich_zero_tool_passports(self, limit: int = 500, max_workers: int = 12) -> int:
        """Scan passports with zero tool signatures and attempt static AST enrichment via GitHub or npm tarball."""
        enriched_count = 0
        
        # State cleanup: sanitize `ast_probed_repos` to remove non-github strings
        ast_probed_repos_list = self.state.get("ast_probed_repos", [])
        cleaned_ast_probed_repos = [repo for repo in ast_probed_repos_list if "github.com" in repo]
        ast_probed_repos = set(cleaned_ast_probed_repos)
        self.state["ast_probed_repos"] = list(ast_probed_repos)
        

        npm_probed_packages = set(self.state.get("npm_probed_packages", []))
        pypi_probed_packages = set(self.state.get("pypi_probed_packages", []))

        

        npm_candidates = []
        github_candidates = []
        pypi_candidates = []

        
        for j_file in sorted(self.output_dir.rglob("*.json")):
            if j_file.name in ("sync_state.json", "index.json"):
                continue
            try:
                spec = ServerPackageSpec.from_dict(json.loads(j_file.read_text(encoding="utf-8")))
                has_tools = any(bool(v.tool_signatures) for v in spec.versions)
                is_dead = any(v.capabilities.get("is_archived") or v.capabilities.get("is_unpublished") for v in spec.versions)
                if has_tools or is_dead:
                    continue
                
                check_repo = spec.repository_url
                
                if spec.ecosystem == "npm" or "npm_registry" in spec.sources_merged:
                    if spec.package_name not in npm_probed_packages:
                        npm_candidates.append((j_file, spec, check_repo, "npm"))
                elif spec.ecosystem in ("pypi", "python") or "pypi" in spec.sources_merged:
                    if spec.package_name not in pypi_probed_packages:
                        pypi_candidates.append((j_file, spec, check_repo, "pypi"))
                elif check_repo and "github.com" in check_repo:

                    if check_repo not in ast_probed_repos:
                        github_candidates.append((j_file, spec, check_repo, "github"))
            except Exception as exc:
                logger.debug("Error loading potential AST candidate %s: %s", j_file.name, exc)


        candidates_to_probe = npm_candidates + pypi_candidates + github_candidates

        if not candidates_to_probe:
            return 0
        
        candidates_to_probe = candidates_to_probe[:limit]
        state_lock = threading.Lock()
        
        def _process_candidate(item: tuple[Path, ServerPackageSpec, str | None, str]) -> bool:
            j_file, spec, check_repo, strategy = item
            tools = []
            gateway_conns, gateway_caps = [], {}
            try:
                if strategy == "npm":
                    try:
                        tools = self._extract_tools_from_npm_tarball(spec.package_name)
                    except ArchiveNotFoundError:
                        gateway_caps["is_unpublished"] = True
                        gateway_caps["http_status"] = 404
                        gateway_caps["archival_reason"] = "Repository or package returned HTTP 404/Not Found"
                        tools = []
                    if not tools and not gateway_caps.get("is_unpublished"):
                        gateway_conns, gateway_caps = self._detect_remote_gateway_from_npm_tarball(spec.package_name)
                    with state_lock:
                        npm_probed_packages.add(spec.package_name)
                        self.state["npm_probed_packages"] = list(npm_probed_packages)
                elif strategy == "pypi":
                    try:
                        tools = self._extract_tools_from_pypi_package(spec.package_name)
                    except ArchiveNotFoundError:
                        gateway_caps["is_unpublished"] = True
                        gateway_caps["http_status"] = 404
                        gateway_caps["archival_reason"] = "Repository or package returned HTTP 404/Not Found"
                        tools = []
                    with state_lock:
                        pypi_probed_packages.add(spec.package_name)
                        self.state["pypi_probed_packages"] = list(pypi_probed_packages)
                elif strategy == "github":
                    try:
                        tools = self._extract_ast_tools_from_github(spec.package_name, check_repo)
                    except ArchiveNotFoundError:
                        gateway_caps["is_archived"] = True
                        gateway_caps["http_status"] = 404
                        gateway_caps["archival_reason"] = "Repository or package returned HTTP 404/Not Found"
                        tools = []
                    if not tools and not gateway_caps.get("is_archived"):
                        tools = self._extract_tools_from_github_readme(spec.package_name, check_repo)
                        if tools:
                            gateway_caps["documentation_extracted_tools"] = True
                    with state_lock:
                        ast_probed_repos.add(check_repo)
                        self.state["ast_probed_repos"] = list(ast_probed_repos)

                if tools or gateway_conns or gateway_caps.get("is_archived") or gateway_caps.get("is_unpublished"):
                    kwargs: dict[str, Any] = {
                        "package_name": spec.package_name,
                        "ecosystem": spec.ecosystem,
                        "existing_spec": spec,
                    }
                    if gateway_conns or gateway_caps:
                        kwargs["pre_extracted_connections"] = gateway_conns
                        kwargs["pre_extracted_capabilities"] = gateway_caps
                    if strategy == "github" and "documentation_extracted_tools" in gateway_caps:
                        kwargs["pre_extracted_tools"] = tools
                        kwargs["pre_extracted_source"] = "github_readme"
                    elif strategy != "github" and tools:
                        kwargs["pre_extracted_tools"] = tools
                        kwargs["pre_extracted_source"] = strategy
                    merged_spec = self.merge_and_enrich_passport(**kwargs)
                    if merged_spec and (
                        any(bool(v.tool_signatures) for v in merged_spec.versions)
                        or any(bool(v.connections) for v in merged_spec.versions)
                        or any(v.capabilities.get("is_archived") or v.capabilities.get("is_unpublished") for v in merged_spec.versions)
                    ):
                        with state_lock:
                            FingerprintGenerator.save_spec_to_file(merged_spec, j_file)
                        logger.info(
                            "Enriched zero-tool passport with %s: %s (%d tools, %d conns, archived=%s)",
                            strategy,
                            spec.package_name,
                            len(tools),
                            len(gateway_conns),
                            bool(gateway_caps.get("is_archived") or gateway_caps.get("is_unpublished")),
                        )
                        return True
            except Exception as exc:
                logger.debug("Error during %s tool enrichment for %s: %s", strategy, j_file.name, exc)
                with state_lock:
                    if strategy == "npm":
                        npm_probed_packages.add(spec.package_name)
                        self.state["npm_probed_packages"] = list(npm_probed_packages)
                    elif strategy == "pypi":
                        pypi_probed_packages.add(spec.package_name)
                        self.state["pypi_probed_packages"] = list(pypi_probed_packages)
                    elif strategy == "github" and check_repo:

                        ast_probed_repos.add(check_repo)
                        self.state["ast_probed_repos"] = list(ast_probed_repos)
            return False

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_process_candidate, c) for c in candidates_to_probe]
                probed_count = 0
                for future in concurrent.futures.as_completed(futures):
                    probed_count += 1
                    if future.result():
                        enriched_count += 1
                        
                    # Ensure we save state periodically based on probes
                    if probed_count % 50 == 0:
                        self._save_state()
                        
                    if enriched_count >= limit:
                        break
        except KeyboardInterrupt:
            logger.info("Interrupted. Saving state...")
        finally:
            logger.info("Enriched %d passports with static AST tools", enriched_count)
            self._save_state()
            return enriched_count

    def discover_new_mcps(self, limit: int = 500) -> int:
        """Query search feeds, full Smithery directory, PyPI registry, and awesome-mcp-servers."""
        discovered_count = 0

        # 1. Query ALL Smithery Public Directory Pages
        logger.info("Crawling Smithery Public Registry directory...")
        for page in range(1, 15):
            smithery_url = f"https://api.smithery.ai/servers?page={page}&pageSize=50"
            smithery_list, _ = fetch_json(smithery_url)
            if not smithery_list or "servers" not in smithery_list or not smithery_list["servers"]:
                break
            for s in smithery_list["servers"]:
                q_name = s.get("qualifiedName")
                if not q_name:
                    continue
                clean_name = q_name.replace("/", "_") + ".json"
                if (self.output_dir / clean_name).is_file():
                    continue

                # Fetch full server details from Smithery
                s_detail, _ = fetch_json(f"https://api.smithery.ai/servers/{q_name}")
                if s_detail and "tools" in s_detail:
                    merged = self.merge_and_enrich_passport(
                        package_name=q_name,
                        ecosystem="npm",
                        smithery_data=s_detail,
                    )
                    if merged:
                        target_file = self.output_dir / clean_name
                        FingerprintGenerator.save_spec_to_file(merged, target_file)
                        discovered_count += 1
                        logger.info("Discovered and created NEW passport from Smithery: %s", q_name)

        # 2. Query PyPI for Official & Community Python MCP Servers
        logger.info("Crawling PyPI Registry for Python MCP packages...")
        pypi_candidates = [
            "mcp-server-git",
            "mcp-server-sqlite",
            "mcp-server-time",
            "mcp-server-fetch",
            "mcp-server-memory",
            "mcp-server-brave-search",
            "mcp-server-duckdb",
            "mcp-server-redis",
            "mcp-server-elasticsearch",
            "mcp-server-couchdb",
            "mcp-server-neo4j",
            "mcp-server-mysql",
            "mcp-server-postgres",
            "fastmcp",
            "mcp-agent",
            "mcp-proxy",
        ]
        for pkg in pypi_candidates:
            clean_name = f"{pkg}.json"
            if (self.output_dir / clean_name).is_file():
                continue
            pypi_data, _ = fetch_json(f"https://pypi.org/pypi/{pkg}/json")
            if pypi_data:
                merged = self.merge_and_enrich_passport(
                    package_name=pkg,
                    ecosystem="PyPI",
                    pypi_data=pypi_data,
                )
                if merged:
                    target_file = self.output_dir / clean_name
                    FingerprintGenerator.save_spec_to_file(merged, target_file)
                    discovered_count += 1
                    logger.info("Discovered and created NEW passport from PyPI: %s", pkg)

        # 3. Query npm search for MCP keywords
        logger.info("Crawling npm registry for MCP keyword packages...")
        search_url = f"https://registry.npmjs.org/-/v1/search?text=keywords:modelcontextprotocol,mcp-server&size={limit}"
        search_data, _ = fetch_json(search_url)
        if search_data and "objects" in search_data:
            for item in search_data["objects"]:
                pkg_name = item["package"]["name"]
                clean_name = pkg_name.replace("/", "_") + ".json"
                if (self.output_dir / clean_name).is_file() or (
                    self.output_dir / pkg_name
                ).with_suffix(".json").is_file():
                    continue

                # Fetch full metadata
                npm_meta, _ = fetch_json(f"https://registry.npmjs.org/{pkg_name}")
                if npm_meta:
                    merged = self.merge_and_enrich_passport(
                        package_name=pkg_name,
                        ecosystem="npm",
                        npm_data=npm_meta,
                    )
                    if merged:
                        target_file = self.output_dir / clean_name
                        FingerprintGenerator.save_spec_to_file(merged, target_file)
                        discovered_count += 1
                        logger.info("Discovered and created NEW passport from npm: %s", pkg_name)

        # 4. Query Official MCP Registry API (/v0.1/servers)
        logger.info("Crawling Official MCP Registry (/v0.1/servers)...")
        cursor = None
        for _ in range(15):
            reg_url = "https://registry.modelcontextprotocol.io/v0.1/servers"
            if cursor:
                reg_url += f"?cursor={urllib.parse.quote(cursor)}"
            reg_data, _ = fetch_json(reg_url)
            if not reg_data or "servers" not in reg_data:
                break
            srv_list = reg_data.get("servers", [])
            for entry in srv_list:
                srv = entry.get("server", {})
                srv_name = srv.get("name")
                if not srv_name:
                    continue
                clean_name = srv_name.replace("/", "_") + ".json"
                if (self.output_dir / clean_name).is_file():
                    continue

                merged = self.merge_and_enrich_passport(
                    package_name=srv_name,
                    ecosystem="generic",
                    official_registry_data=entry,
                )
                if merged:
                    target_file = self.output_dir / clean_name
                    FingerprintGenerator.save_spec_to_file(merged, target_file)
                    discovered_count += 1
                    logger.info(
                        "Discovered and created NEW passport from Official Registry: %s", srv_name
                    )

            cursor = reg_data.get("metadata", {}).get("nextCursor")
            if not cursor or not srv_list:
                break

        # 5. Query community curated awesome-mcp-servers stream with multi-manifest extraction
        logger.info("Crawling awesome-mcp-servers GitHub repository manifests concurrently...")
        awesome_url = (
            "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md"
        )
        req_awesome = urllib.request.Request(
            awesome_url,
            headers={"User-Agent": "VerityRedTeam-Sync/1.0"},
        )
        try:
            with urllib.request.urlopen(
                req_awesome, context=_create_ssl_context(), timeout=8
            ) as resp:
                text = resp.read().decode("utf-8")

            # Parse all structured markdown entries (- [Name](URL) - Description)
            entries = []
            seen_repos = set()
            for line in text.splitlines():
                m = re.match(
                    r"^-\s+\[([^\]]+)\]\((https?://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)[^\)]*)\)(?:\s+-\s+(.*))?",
                    line,
                )
                if m:
                    display_name = m.group(1).strip()
                    owner = m.group(3).strip()
                    repo = m.group(4).strip()
                    desc_text = m.group(5).strip() if m.group(5) else ""
                    if owner in (
                        "punkpeye",
                        "modelcontextprotocol",
                        "glama-ai",
                        "sindresorhus",
                    ) or repo.startswith("awesome"):
                        continue
                    if (owner, repo) in seen_repos:
                        continue
                    seen_repos.add((owner, repo))
                    entries.append(
                        {
                            "display_name": display_name,
                            "owner": owner,
                            "repo": repo,
                            "desc": desc_text,
                            "url": f"https://github.com/{owner}/{repo}",
                        }
                    )

            logger.info("Parsed %d candidate repositories from awesome-mcp README", len(entries))

            import concurrent.futures
            import tomllib

            def process_awesome_entry(entry: dict[str, str]) -> ServerPackageSpec | None:
                owner = entry["owner"]
                repo = entry["repo"]
                desc_text = entry["desc"]
                repo_url = entry["url"]
                clean_name = f"{owner}_{repo}.json"
                if (self.output_dir / clean_name).is_file():
                    return None

                # Multi-manifest probe across branches
                manifest_files = [
                    "server.json",
                    "package.json",
                    "pyproject.toml",
                    "smithery.yaml",
                    "Cargo.toml",
                    "go.mod",
                ]
                for fn in manifest_files:
                    for branch in ["main", "master"]:
                        raw_u = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{fn}"
                        try:
                            req_probe = urllib.request.Request(
                                raw_u, headers={"User-Agent": "VerityRedTeam-Sync/1.0"}
                            )
                            with urllib.request.urlopen(
                                req_probe, context=_create_ssl_context(), timeout=3.0
                            ) as p_resp:
                                if p_resp.status == 200:
                                    content = p_resp.read()
                                    if fn == "server.json":
                                        sj = json.loads(content.decode("utf-8"))
                                        if isinstance(sj, dict):
                                            sj_data = {"server": sj}
                                            return self.merge_and_enrich_passport(
                                                package_name=f"{owner}/{repo}",
                                                ecosystem="generic",
                                                official_registry_data=sj_data,
                                                is_curated_source=True,
                                            )
                                    elif fn == "package.json":
                                        pj = json.loads(content.decode("utf-8"))
                                        if isinstance(pj, dict) and "name" in pj:
                                            return self.merge_and_enrich_passport(
                                                package_name=pj["name"],
                                                ecosystem="npm",
                                                npm_data=pj,
                                                is_curated_source=True,
                                            )
                                    elif fn == "pyproject.toml":
                                        toml_data = tomllib.loads(content.decode("utf-8"))
                                        proj = toml_data.get("project", {})
                                        py_name = proj.get("name") or repo
                                        py_desc = proj.get("description") or desc_text
                                        py_deps = proj.get("dependencies", [])
                                        pypi_sim = {
                                            "info": {
                                                "name": py_name,
                                                "summary": py_desc,
                                                "home_page": repo_url,
                                                "requires_dist": py_deps,
                                            },
                                            "releases": {"1.0.0": [{}]},
                                        }
                                        return self.merge_and_enrich_passport(
                                            package_name=py_name,
                                            ecosystem="pypi",
                                            pypi_data=pypi_sim,
                                            is_curated_source=True,
                                        )
                                    elif fn == "smithery.yaml":
                                        return self.merge_and_enrich_passport(
                                            package_name=f"{owner}/{repo}",
                                            ecosystem="generic",
                                            smithery_data={
                                                "qualifiedName": f"{owner}/{repo}",
                                                "description": desc_text,
                                                "deploymentUrl": repo_url,
                                            },
                                            is_curated_source=True,
                                        )
                                    elif fn in ("go.mod", "Cargo.toml"):
                                        eco = "golang" if fn == "go.mod" else "generic"
                                        return self.merge_and_enrich_passport(
                                            package_name=f"{owner}/{repo}",
                                            ecosystem=eco,
                                            is_curated_source=True,
                                        )
                        except Exception:
                            pass

                # If no deep manifest found, create Incomplete Passport capturing metadata
                return self.merge_and_enrich_passport(
                    package_name=f"{owner}/{repo}",
                    ecosystem="github",
                    is_curated_source=True,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                future_to_entry = {
                    executor.submit(process_awesome_entry, entry): entry for entry in entries
                }
                for future in concurrent.futures.as_completed(future_to_entry):
                    entry = future_to_entry[future]
                    owner = entry["owner"]
                    repo = entry["repo"]
                    clean_name = f"{owner}_{repo}.json"
                    try:
                        spec_res = future.result()
                        if spec_res:
                            # Attach repository_url and description if missing
                            if not spec_res.repository_url:
                                spec_dict = spec_res.to_dict()
                                spec_dict["repository_url"] = entry["url"]
                                if not spec_dict.get("description") and entry["desc"]:
                                    spec_dict["description"] = entry["desc"]
                                spec_res = ServerPackageSpec.from_dict(spec_dict)

                            target_file = self.output_dir / clean_name
                            FingerprintGenerator.save_spec_to_file(spec_res, target_file)
                            discovered_count += 1
                    except Exception as exc:
                        logger.debug(
                            "Error processing awesome-mcp entry %s/%s: %s", owner, repo, exc
                        )
        except Exception as exc:
            logger.debug("Failed crawling awesome-mcp-servers: %s", exc)

        self._save_state()
        return discovered_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Source MCP Passport Synchronizer & Update Engine"
    )
    parser.add_argument("--output", default="data/fingerprints", help="Passport storage directory")
    parser.add_argument(
        "--update-existing", action="store_true", help="Check and update existing MCP versions"
    )
    parser.add_argument(
        "--discover-new", action="store_true", help="Discover and pull new MCP servers"
    )
    parser.add_argument("--all", action="store_true", help="Run both update and discovery")
    args = parser.parse_args()

    syncer = PassportSynchronizer(output_dir=args.output)
    if args.all or args.update_existing:
        syncer.update_existing_passports()
    if args.all or args.discover_new:
        syncer.discover_new_mcps()


if __name__ == "__main__":
    main()
