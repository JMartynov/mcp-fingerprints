"""Archive, GitHub tree, and README tool extraction helpers."""

from __future__ import annotations

import concurrent.futures
import datetime
import io
import json
import os
import re
import signal
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from packaging.version import InvalidVersion, parse as parse_version

from mcp_fingerprints.ast_parser import (
    parse_mcp_source_code,
    parse_python_mcp_ast_bundle,
    parse_typescript_mcp_ast,
)
from mcp_fingerprints.canonicalizer import build_version_fingerprint
from mcp_fingerprints.crawler import FingerprintGenerator
from mcp_fingerprints.crawler.maven_central import EnterpriseIndexer
from mcp_fingerprints.crawler.pkg_go_dev import search_pkg_go_dev
from mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from mcp_fingerprints.mcp_classifier import McpServerValidator, sanitize_tool_definition
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.monorepo_prober import match_monorepo_subpackage_dir
from mcp_fingerprints.openapi_parser import parse_openapi_spec
from mcp_fingerprints.runtime_sandbox import probe_mcp_server_stdio
from .http_client import ArchiveNotFoundError, _create_ssl_context, fetch_json, logger


def _sync_attr(name: str, fallback: Any) -> Any:
    mod = sys.modules.get("mcp_fingerprints.synchronizer")
    return getattr(mod, name, fallback) if mod is not None else fallback


class ExtractorsSyncMixin:
    """Mixin providing PyPI, npm, GitHub AST, and README tool extraction."""

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
                py_files: dict[str, str] = {}
                with zipfile.ZipFile(buf, "r") as zf:
                    for name in zf.namelist():
                        if name.endswith(".py") and not name.split("/")[-1].startswith("test"):
                            code = zf.read(name).decode("utf-8", errors="ignore")
                            py_files[name] = code
                bundle_res = parse_python_mcp_ast_bundle(py_files)
                for t in bundle_res.tools:
                    sanitized = sanitize_tool_definition(t)
                    if sanitized and sanitized.get("name") not in seen_tool_names:
                        seen_tool_names.add(sanitized.get("name"))
                        extracted_tools.append(sanitized)

            except zipfile.BadZipFile as e:
                logger.warning(f"Zip error extracting {package_name}: {e}")
        elif target_type == "sdist":
            import tarfile
            try:
                buf.seek(0)
                py_files = {}
                with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                    for member in tar.getmembers():
                        if not member.isfile():
                            continue
                        name = member.name
                        if name.endswith(".py") and not name.split("/")[-1].startswith("test"):
                            f_obj = tar.extractfile(member)
                            if f_obj:
                                code = f_obj.read().decode("utf-8", errors="ignore")
                                py_files[name] = code
                bundle_res = parse_python_mcp_ast_bundle(py_files)
                for t in bundle_res.tools:
                    sanitized = sanitize_tool_definition(t)
                    if sanitized and sanitized.get("name") not in seen_tool_names:
                        seen_tool_names.add(sanitized.get("name"))
                        extracted_tools.append(sanitized)

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
                                    sanitized = sanitize_tool_definition(t)
                                    if sanitized and sanitized.get("name") not in seen_tool_names:
                                        seen_tool_names.add(sanitized.get("name"))
                                        extracted_tools.append(sanitized)

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
                                if len(parts) > 7:
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
                                    headers=self._get_github_headers(raw=True),
                                )
                                with urllib.request.urlopen(req_raw, context=_create_ssl_context(), timeout=3.0) as raw_resp:
                                    if raw_resp.status == 200:
                                        code = raw_resp.read(500 * 1024).decode("utf-8", errors="ignore")
                                        if p.endswith((".json", ".yaml", ".yml")):
                                            extracted = parse_openapi_spec(code)
                                        else:
                                            lang = p.split('.')[-1]
                                            if lang == "mjs": lang = "js"
                                            extracted = _sync_attr("parse_mcp_source_code", parse_mcp_source_code)(code, language=lang)
                                        for tool in extracted:
                                            if tool.get("name") not in seen_tool_names:
                                                seen_tool_names.add(tool.get("name"))
                                                aggregated_tools.append(tool)
                            except Exception:
                                continue
            except urllib.error.HTTPError:
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
                    headers=self._get_github_headers(raw=True),
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
                        headers=self._get_github_headers(raw=True),
                    )
                    with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=2.5) as resp:
                        if resp.status == 200:
                            code = resp.read().decode("utf-8", errors="ignore")
                            extracted = _sync_attr("parse_mcp_source_code", parse_mcp_source_code)(code, language=lang)
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
                        headers=self._get_github_headers(raw=True),
                    )
                    with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=3.0) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="ignore")
                            tools = _sync_attr("parse_markdown_tool_docs", parse_markdown_tool_docs)(content)
                            if tools:
                                return tools
                except Exception:
                    continue
        return []

