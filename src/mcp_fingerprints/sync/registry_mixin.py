"""Registry enrichment, discovery, and runtime probing orchestration."""

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


class RegistrySyncMixin:
    """Mixin providing passport merging, updates, enrichment, discovery, and probing."""

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
                try:
                    s_detail, _ = _sync_attr("fetch_json", fetch_json)(f"https://api.smithery.ai/servers/{s_name}", timeout=2)
                    if s_detail and isinstance(s_detail, dict) and "tools" in s_detail:
                        smithery_data = s_detail
                        break
                except Exception:
                    pass
        tools: list[dict[str, Any]] = list(pre_extracted_tools or [])
        prompts: list[dict[str, Any]] = []
        resources: list[dict[str, Any]] = []
        connections: list[dict[str, Any]] = list(pre_extracted_connections or [])
        extra_capabilities: dict[str, bool] = dict(pre_extracted_capabilities or {})
        desc = ""
        repo_url = None
        homepage_url = None
        license_str = None
        author = existing_spec.author if existing_spec else None
        keywords: list[str] = list(existing_spec.keywords) if existing_spec and existing_spec.keywords else []
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
            if not author:
                author = smithery_data.get("author") or smithery_data.get("publisher")
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
            if not author and author_obj:
                author = author_obj.get("name") if isinstance(author_obj, dict) else str(author_obj or "")
            repo_field = npm_data.get("repository")
            repo_raw = None
            if isinstance(repo_field, dict):
                repo_raw = repo_field.get("url")
            elif isinstance(repo_field, str):
                repo_raw = repo_field
            if not repo_raw:
                repo_raw = npm_data.get("homepage") or npm_data.get("bugs", {}).get("url")
            if repo_raw:
                clean_repo = re.sub(r"^git\+", "", repo_raw)
                clean_repo = re.sub(r"\.git$", "", clean_repo)
                clean_repo = re.sub(r"^git://", "https://", clean_repo)
                clean_repo = re.sub(r"^ssh://git@", "https://", clean_repo)
                repo_url = clean_repo
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
            if not author:
                author = info.get("author") or info.get("author_email")
            if not repo_url:
                proj_urls = info.get("project_urls") or {}
                for key in ("Repository", "Source", "Source Code", "GitHub", "Homepage", "Home"):
                    for p_key, p_val in proj_urls.items():
                        if p_key.lower() == key.lower() and p_val:
                            repo_url = p_val
                            break
                    if repo_url:
                        break
                if not repo_url:
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
            if not author:
                author = srv.get("author")
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

        # Prior-Version Toolset Inheritance
        if not tools and existing_spec:
            prior_tools, prior_prompts, prior_resources = self._extract_prior_tools(existing_spec)
            if prior_tools:
                tools = prior_tools
                prompts = prior_prompts
                resources = prior_resources
                is_simulated = True

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
        
        # Deduce transport from connections
        transport = "stdio"
        remote_endpoint = None
        for v in sanitized_versions:
            for conn in v.connections:
                ctype = conn.get("type", "")
                if ctype in ("sse", "websocket"):
                    # Validate HTTPS/WSS schemes
                    url = conn.get("url") or conn.get("deploymentUrl") or ""
                    if url:
                        is_localhost = "localhost" in url or "127.0.0.1" in url
                        if ctype == "sse" and not url.startswith("https://") and not is_localhost:
                            pass # Reject plain HTTP unless localhost, handled by not setting or by validator? We'll enforce in validator, but here we detect it.
                        elif ctype == "websocket" and not url.startswith("wss://") and not is_localhost:
                            pass
                        transport = ctype
                        remote_endpoint = url
                        break
            if transport != "stdio":
                break

        clean_pkg_name = package_name.strip()
        
        def _semver_key(v_obj):
            try:
                return (1, parse_version(v_obj.version))
            except InvalidVersion:
                return (0, v_obj.version)
                
        # If new metadata is missing or empty, preserve existing_spec metadata
        if existing_spec:
            if not desc or not desc.strip():
                desc = existing_spec.description
            if not repo_url or not str(repo_url).strip():
                repo_url = existing_spec.repository_url
            if not homepage_url or not str(homepage_url).strip():
                if hasattr(existing_spec, "homepage_url"):
                    homepage_url = existing_spec.homepage_url
            if not license_str or not str(license_str).strip():
                license_str = existing_spec.license

        is_valid, reason = McpServerValidator.is_valid_mcp_server(
            package_name=clean_pkg_name,
            ecosystem=ecosystem,
            dependencies=all_deps if all_deps else None,
            keywords=keywords,
            description=desc,
            has_tools_declared=bool(tools) or any(bool(v.tool_signatures) for v in all_versions) or bool(connections) or any(bool(v.connections) for v in all_versions) or bool(existing_spec),
            is_curated_source=is_curated_source,
            transport=transport,
            remote_endpoint=remote_endpoint,
        )
        if not is_valid:
            logger.info("Skipping invalid/non-MCP package %s (%s)", clean_pkg_name, reason)
            return None
        return ServerPackageSpec(
            package_name=clean_pkg_name,
            purl=purl,
            ecosystem=ecosystem,
            display_name=clean_pkg_name,
            description=desc,
            repository_url=repo_url,
            homepage_url=homepage_url,
            author=author,
            license=license_str,
            keywords=tuple(sorted(set(keywords))),
            aliases=tuple(sorted(set(aliases))),
            sources_merged=tuple(sorted(set(sources))),
            dist_tags=dist_tags,
            versions=tuple(sorted(sanitized_versions, key=_semver_key)),
            transport=transport,
            remote_endpoint=remote_endpoint,
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
        
        # Load from checkpoint if applicable
        start_cursor = self.checkpoint_data.get("cursor") if self.checkpoint_data.get("current_stage") == "stage_update_existing" else None
        skip = bool(start_cursor)

        for j_file in sorted(self.output_dir.rglob("*.json")):
            if j_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
                continue
                
            if skip:
                if j_file.name == start_cursor:
                    skip = False
                continue

            self._check_budget("stage_update_existing", cursor=j_file.name)
            
            try:
                spec = ServerPackageSpec.from_dict(json.loads(j_file.read_text(encoding="utf-8")))
                pkg_name = spec.package_name
                eco = spec.ecosystem.lower()

                # Check upstream for new versions
                if eco == "npm" or "npm_registry" in spec.sources_merged:
                    npm_meta, _ = _sync_attr("fetch_json", fetch_json)(
                        f"https://registry.npmjs.org/{pkg_name}",
                        headers={"Accept": "application/vnd.npm.install-v1+json"},
                    )
                    if npm_meta and "dist-tags" in npm_meta:
                        latest_dist = npm_meta["dist-tags"].get("latest")
                        known_versions = {v.version for v in spec.versions}
                        needs_desc = not (spec.description and spec.description.strip())
                        if (latest_dist and latest_dist not in known_versions) or needs_desc:
                            # Pull full packument to capture description, repository, author and license
                            full_npm_meta, _ = _sync_attr("fetch_json", fetch_json)(f"https://registry.npmjs.org/{pkg_name}")
                            if full_npm_meta:
                                npm_meta = full_npm_meta
                        if (latest_dist and latest_dist not in known_versions) or (needs_desc and npm_meta.get("description")):
                            logger.info(
                                "Updating metadata/version for npm %s: %s (was %s)",
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
                    pypi_meta, _ = _sync_attr("fetch_json", fetch_json)(f"https://pypi.org/pypi/{pkg_name}/json")
                    if pypi_meta and "info" in pypi_meta:
                        latest_dist = pypi_meta["info"].get("version")
                        known_versions = {v.version for v in spec.versions}
                        needs_desc = not (spec.description and spec.description.strip())
                        if (latest_dist and latest_dist not in known_versions) or (needs_desc and pypi_meta["info"].get("summary")):
                            logger.info(
                                "Updating metadata/version for PyPI %s: %s (was %s)",
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
                    s_detail, _ = _sync_attr("fetch_json", fetch_json)(f"https://api.smithery.ai/servers/{pkg_name}")
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
        
        start_cursor = self.checkpoint_data.get("cursor") if self.checkpoint_data.get("current_stage") == "stage_enrich_ast" else None
        skip = bool(start_cursor)

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
            if j_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
                continue
                
            if skip:
                if j_file.name == start_cursor:
                    skip = False
                continue

            try:
                spec = ServerPackageSpec.from_dict(json.loads(j_file.read_text(encoding="utf-8")))
                has_tools = any(bool(v.tool_signatures) for v in spec.versions)
                is_dead = any(v.capabilities.get("is_archived") or v.capabilities.get("is_unpublished") for v in spec.versions)
                if has_tools or is_dead:
                    continue
                
                check_repo = spec.repository_url
                
                # Generic GitHub Slug URL Auto-Resolution
                if not check_repo and re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", spec.package_name):
                    check_repo = f"https://github.com/{spec.package_name}"
                
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
                    
                    if not tools and check_repo:
                        fallback_tools = self._extract_ast_tools_from_github(spec.package_name, check_repo)
                        if fallback_tools:
                            tools = fallback_tools
                            gateway_caps["pypi_fallback_github_ast"] = True
                        else:
                            readme_tools = self._extract_tools_from_github_readme(spec.package_name, check_repo)
                            if readme_tools:
                                tools = readme_tools
                                gateway_caps["documentation_extracted_tools"] = True
                    
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
            for idx, candidate in enumerate(candidates_to_probe):
                self._check_budget("stage_enrich_ast", cursor=candidate[0].name)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(_process_candidate, c): c for c in candidates_to_probe}
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

    def discover_new_mcps(self, limit: int = 500, docker: bool = False, polyglot: bool = False) -> int:
        """Query search feeds, full Smithery directory, PyPI registry, and awesome-mcp-servers."""
        discovered_count = 0
        
        start_substage = self.checkpoint_data.get("substage") if self.checkpoint_data.get("current_stage") == "stage_discover_new" else None

        # 1. Query ALL Smithery Public Directory Pages
        if not start_substage or start_substage == "smithery":
            logger.info("Crawling Smithery Public Registry directory...")
            start_page = self.checkpoint_data.get("page", 1) if self.checkpoint_data.get("substage") == "smithery" else 1
            for page in range(start_page, 15):
                self._check_budget("stage_discover_new", substage="smithery", page=page)
                smithery_url = f"https://api.smithery.ai/servers?page={page}&pageSize=50"
                smithery_list, _ = _sync_attr("fetch_json", fetch_json)(smithery_url)
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
                s_detail, _ = _sync_attr("fetch_json", fetch_json)(f"https://api.smithery.ai/servers/{q_name}")
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
        pypi_candidates = []
        if not start_substage or start_substage in ("smithery", "pypi"):
            logger.info("Crawling PyPI Registry for Python MCP packages...")
            start_cursor = self.checkpoint_data.get("cursor") if self.checkpoint_data.get("substage") == "pypi" else None
            skip_pypi = bool(start_cursor)

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
            if skip_pypi:
                if pkg == start_cursor:
                    skip_pypi = False
                continue
            self._check_budget("stage_discover_new", substage="pypi", cursor=pkg)
            clean_name = f"{pkg}.json"
            if (self.output_dir / clean_name).is_file():
                continue
            pypi_data, _ = _sync_attr("fetch_json", fetch_json)(f"https://pypi.org/pypi/{pkg}/json")
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
        if not start_substage or start_substage in ("smithery", "pypi", "npm"):
            logger.info("Crawling npm registry for MCP keyword packages...")
            search_url = f"https://registry.npmjs.org/-/v1/search?text=keywords:modelcontextprotocol,mcp-server&size={limit}"
            self._check_budget("stage_discover_new", substage="npm")
            search_data, _ = _sync_attr("fetch_json", fetch_json)(search_url)
            start_cursor = self.checkpoint_data.get("cursor") if self.checkpoint_data.get("substage") == "npm" else None
            skip_npm = bool(start_cursor)

            if search_data and "objects" in search_data:
                for item in search_data["objects"]:
                    pkg_name = item["package"]["name"]
                    if skip_npm:
                        if pkg_name == start_cursor:
                            skip_npm = False
                        continue
                    self._check_budget("stage_discover_new", substage="npm", cursor=pkg_name)
                    clean_name = pkg_name.replace("/", "_") + ".json"
                    if (self.output_dir / clean_name).is_file() or (
                        self.output_dir / pkg_name
                    ).with_suffix(".json").is_file():
                        continue

                    # Fetch full metadata
                    npm_meta, _ = _sync_attr("fetch_json", fetch_json)(f"https://registry.npmjs.org/{pkg_name}")
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
        if not start_substage or start_substage in ("smithery", "pypi", "npm", "official_registry"):
            logger.info("Crawling Official MCP Registry (/v0.1/servers)...")
            cursor = self.checkpoint_data.get("cursor") if self.checkpoint_data.get("substage") == "official_registry" else None
            for _ in range(15):
                self._check_budget("stage_discover_new", substage="official_registry", cursor=cursor)
                reg_url = "https://registry.modelcontextprotocol.io/v0.1/servers"
                if cursor:
                    reg_url += f"?cursor={urllib.parse.quote(cursor)}"
                reg_data, _ = _sync_attr("fetch_json", fetch_json)(reg_url)
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

        # Docker Hub Discovery
        if docker and (not start_substage or start_substage in ("smithery", "pypi", "npm", "official_registry", "docker_hub")):
            logger.info("Crawling Docker Hub for MCP containers...")
            docker_search_url = "https://hub.docker.com/v2/search/repositories?query=mcp&page_size=20"
            self._check_budget("stage_discover_new", substage="docker_hub")
            docker_data, _ = _sync_attr("fetch_json", fetch_json)(docker_search_url)
            if docker_data and "results" in docker_data:
                for repo in docker_data["results"]:
                    repo_name_full = repo.get("repo_name", "")
                    if not repo_name_full:
                        continue
                    
                    parts = repo_name_full.split("/")
                    if len(parts) == 2:
                        namespace, repo_name = parts
                    else:
                        namespace = "library"
                        repo_name = repo_name_full
                        
                    pkg_name = f"docker_{namespace}_{repo_name}"
                    clean_name = f"{pkg_name}.json"
                    if (self.output_dir / clean_name).is_file():
                        continue
                        
                    description = repo.get("short_description", "")
                    
                    # Fetch full description
                    repo_url = f"https://hub.docker.com/v2/repositories/{repo_name_full}/"
                    repo_data, _ = _sync_attr("fetch_json", fetch_json)(repo_url)
                    full_description = ""
                    if repo_data:
                        full_description = repo_data.get("full_description", "")
                    
                    from mcp_fingerprints.crawler.docker_hub import extract_docker_stdio_args
                    tools = []
                    docker_args = []
                    docker_image = None
                    if full_description:
                        tools = _sync_attr("parse_markdown_tool_docs", parse_markdown_tool_docs)(full_description)
                        
                        # Try to find docker run command in the description
                        for line in full_description.splitlines():
                            if line.strip().startswith("docker run"):
                                img, args = extract_docker_stdio_args(line.strip())
                                if img and "mcp" in img.lower():
                                    docker_image = img
                                    docker_args = args
                                    break
                                elif "mcp" in line.lower():
                                    img, args = extract_docker_stdio_args(line.strip())
                                    if img:
                                        docker_image = img
                                        docker_args = args
                                        break
                                        
                    if not tools and description:
                        tools = [{"name": "unknown", "description": description, "inputSchema": {"type": "object", "properties": {}}}]
                        
                        
                    if tools:
                        spec = FingerprintGenerator.generate_server_spec(
                            package_name=pkg_name,
                            ecosystem="docker",
                            purl=f"pkg:docker/{repo_name_full}",
                            version="latest",
                            tools=tools,
                            description=description,
                            repository_url=f"https://hub.docker.com/r/{repo_name_full}"
                        )
                        
                        if docker_image:
                            # Update the connections in the version fingerprint
                            latest_v = spec.versions[0]
                            conn = {
                                "type": "stdio",
                                "command": "docker",
                                "args": ["run", "-i", "--rm", docker_image] + docker_args,
                            }
                            caps = dict(latest_v.capabilities)
                            
                            updated_v = build_version_fingerprint(
                                version=latest_v.version,
                                tools=tools,
                                capabilities=caps,
                            )
                            # Overwrite connections
                            updated_v = VersionFingerprint(
                                version=updated_v.version,
                                toolset_canonical_hash=updated_v.toolset_canonical_hash,
                                tool_signatures=updated_v.tool_signatures,
                                prompt_signatures=updated_v.prompt_signatures,
                                resource_signatures=updated_v.resource_signatures,
                                release_date=updated_v.release_date,
                                dependencies=updated_v.dependencies,
                                connections=[conn],
                                capabilities=updated_v.capabilities,
                            )
                            spec = ServerPackageSpec(
                                package_name=spec.package_name,
                                purl=spec.purl,
                                ecosystem=spec.ecosystem,
                                display_name=spec.display_name,
                                description=spec.description,
                                repository_url=spec.repository_url,
                                homepage_url=spec.homepage_url,
                                author=spec.author,
                                license=spec.license,
                                keywords=spec.keywords,
                                aliases=spec.aliases,
                                versions=(updated_v,),
                                sources_merged=spec.sources_merged,
                            )
                        
                        target_file = self.output_dir / clean_name
                        FingerprintGenerator.save_spec_to_file(spec, target_file)
                        discovered_count += 1
                        logger.info("Discovered NEW passport from Docker Hub: %s", pkg_name)

        # Enterprise JVM and .NET Packages (Maven Central & NuGet)
        if not start_substage or start_substage in (
            "smithery",
            "pypi",
            "npm",
            "official_registry",
            "docker_hub",
            "polyglot",
            "enterprise",
            "awesome_mcp",
        ):
            self._check_budget("stage_discover_new", substage="enterprise")
            logger.info("Discovering Enterprise JVM and .NET packages...")
            indexer = EnterpriseIndexer()

            # Maven
            for pkg in indexer.discover_maven():
                pkg_name = pkg["name"]
                clean_name = f"{pkg['ecosystem']}/{pkg_name[0].lower()}/{pkg_name}.json"
                if not (self.output_dir / clean_name).exists():
                    try:
                        spec = FingerprintGenerator.generate_server_spec(
                            package_name=pkg_name,
                            ecosystem=pkg["ecosystem"],
                            purl=pkg["purl"],
                            version=pkg["version"],
                            tools=[
                                {
                                    "name": "unknown",
                                    "description": pkg["description"],
                                    "inputSchema": {"type": "object", "properties": {}},
                                }
                            ],
                            description=pkg["description"],
                        )
                        target_file = self.output_dir / clean_name
                        FingerprintGenerator.save_spec_to_file(spec, target_file)
                        discovered_count += 1
                        logger.info(
                            "Discovered NEW enterprise passport from Maven: %s",
                            pkg_name,
                        )
                    except Exception as exc:
                        logger.debug(
                            "Error creating Maven passport for %s: %s", pkg_name, exc
                        )

            # NuGet
            for pkg in indexer.discover_nuget():
                pkg_name = pkg["name"]
                clean_name = f"{pkg['ecosystem']}/{pkg_name[0].lower()}/{pkg_name}.json"
                if not (self.output_dir / clean_name).exists():
                    try:
                        spec = FingerprintGenerator.generate_server_spec(
                            package_name=pkg_name,
                            ecosystem=pkg["ecosystem"],
                            purl=pkg["purl"],
                            version=pkg["version"],
                            tools=[
                                {
                                    "name": "unknown",
                                    "description": pkg["description"],
                                    "inputSchema": {"type": "object", "properties": {}},
                                }
                            ],
                            description=pkg["description"],
                            repository_url=pkg.get("repository_url"),
                        )
                        target_file = self.output_dir / clean_name
                        FingerprintGenerator.save_spec_to_file(spec, target_file)
                        discovered_count += 1
                        logger.info(
                            "Discovered NEW enterprise passport from NuGet: %s",
                            pkg_name,
                        )
                    except Exception as exc:
                        logger.debug(
                            "Error creating NuGet passport for %s: %s", pkg_name, exc
                        )

        # 5. Query community curated awesome-mcp-servers stream with multi-manifest extraction
        if not start_substage or start_substage in ("smithery", "pypi", "npm", "official_registry", "docker_hub", "polyglot", "awesome_mcp"):
            logger.info("Crawling awesome-mcp-servers GitHub repository manifests concurrently...")
            self._check_budget("stage_discover_new", substage="awesome_mcp")
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

        # Go modules discovery
        if polyglot and (not start_substage or start_substage in ("smithery", "pypi", "npm", "official_registry", "docker_hub", "polyglot", "go_modules")):
            logger.info("Crawling Go Modules for cloud-native MCP servers...")
            self._check_budget("stage_discover_new", substage="go_modules")
            go_repos = search_pkg_go_dev("mcp-go mcp-golang cloud-native")
            for repo_info in go_repos:
                full_name = repo_info["full_name"]
                owner, repo_name = full_name.split("/")
                pkg_name = f"go_{owner}_{repo_name}"
                clean_name = f"{pkg_name}.json"
                
                if (self.output_dir / clean_name).is_file():
                    continue
                    
                description = repo_info.get("description", "")
                
                tools = [{"name": "unknown", "description": description, "inputSchema": {"type": "object", "properties": {}}}]
                purl = f"pkg:golang/{full_name}"
                
                spec = FingerprintGenerator.generate_server_spec(
                    package_name=pkg_name,
                    ecosystem="go",
                    purl=purl,
                    version="0.1.0",
                    tools=tools,
                    description=description,
                    repository_url=f"https://github.com/{full_name}"
                )
                
                target_file = self.output_dir / clean_name
                FingerprintGenerator.save_spec_to_file(spec, target_file)
                discovered_count += 1
                logger.info("Discovered NEW passport from Go Modules: %s", pkg_name)

        # Polyglot and Regional/Multilingual GitHub Discovery
        if polyglot and (not start_substage or start_substage in ("smithery", "pypi", "npm", "official_registry", "docker_hub", "polyglot")):
            logger.info("Crawling GitHub for Polyglot and Regional MCP servers...")
            self._check_budget("stage_discover_new", substage="polyglot")
            
            queries = [
                "topic:mcp-server language:rust",
                "topic:mcp-server language:go",
                "Dify MCP",
                "WeCom MCP",
                "WeChat MCP",
                "Bilibili MCP",
                "模型上下文协议",
            ]
            
            for query in queries:
                # Add URL encoding for query
                encoded_query = urllib.parse.quote(query)
                github_search_url = f"https://api.github.com/search/repositories?q={encoded_query}&per_page=10"
                github_data, _ = _sync_attr("fetch_json", fetch_json)(github_search_url)
                if github_data and "items" in github_data:
                    for repo in github_data["items"]:
                        full_name = repo.get("full_name")
                        if not full_name:
                            continue
                            
                        owner, repo_name = full_name.split("/")
                        pkg_name = f"github_{owner}_{repo_name}"
                        clean_name = f"{pkg_name}.json"
                        
                        if (self.output_dir / clean_name).is_file():
                            continue
                            
                        description = repo.get("description", "")
                        default_branch = repo.get("default_branch", "main")
                        
                        # Try to parse tools from README
                        readme_url = f"https://raw.githubusercontent.com/{full_name}/{default_branch}/README.md"
                        try:
                            req = urllib.request.Request(readme_url, headers={"User-Agent": "VerityRedTeam-Sync/1.0"})
                            with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=5) as resp:
                                readme_text = resp.read().decode("utf-8")
                        except Exception:
                            readme_text = ""
                            
                        tools = []
                        if readme_text:
                            tools = _sync_attr("parse_markdown_tool_docs", parse_markdown_tool_docs)(readme_text)
                            
                        if not tools and description:
                            tools = [{"name": "unknown", "description": description, "inputSchema": {"type": "object", "properties": {}}}]
                            
                        if tools:
                            purl = f"pkg:github/{full_name}"
                            # Determine ecosystem based on language hint, or default to github
                            if "rust" in query.lower():
                                ecosystem = "cargo"
                            elif "go" in query.lower():
                                ecosystem = "go"
                            else:
                                ecosystem = "github"
                                
                            spec = FingerprintGenerator.generate_server_spec(
                                package_name=pkg_name,
                                ecosystem=ecosystem,
                                purl=purl,
                                version="latest",
                                tools=tools,
                                description=description,
                                repository_url=f"https://github.com/{full_name}"
                            )
                            
                            target_file = self.output_dir / clean_name
                            FingerprintGenerator.save_spec_to_file(spec, target_file)
                            discovered_count += 1
                            logger.info("Discovered NEW polyglot passport from GitHub: %s", pkg_name)


        # 4. Query Crates.io for Rust MCP packages
        if not start_substage or start_substage in ("smithery", "pypi", "npm", "crates"):
            logger.info("Crawling Crates.io Registry for Rust MCP packages...")
            try:
                from mcp_fingerprints.crawler.crates_io import get_mcp_crates
                rust_crates = get_mcp_crates()
                for crate in rust_crates:
                    pkg_name = crate.get("name")
                    if not pkg_name:
                        continue
                    self._check_budget("stage_discover_new", substage="crates", cursor=pkg_name)
                    clean_name = f"{pkg_name}.json"
                    if (self.output_dir / clean_name).is_file():
                        continue
                        
                    # Build dummy spec for now, or fetch github repo to extract tools
                    repo = crate.get("repository")
                    if repo and "github.com" in repo:
                        try:
                            tools = self._extract_ast_tools_from_github(pkg_name, repo_url=repo)
                        except Exception as err:
                            logger.warning("Failed to extract AST tools from %s for crate %s: %s", repo, pkg_name, err)
                            tools = []
                        if tools:
                            ver = crate.get("max_version") or "0.1.0"
                            spec = FingerprintGenerator.generate_server_spec(
                                package_name=pkg_name,
                                ecosystem="cargo",
                                purl=f"pkg:cargo/{pkg_name}",
                                version=ver,
                                tools=tools,
                                repository_url=repo,
                                description=crate.get("description")
                            )
                            target_file = self.output_dir / clean_name
                            FingerprintGenerator.save_spec_to_file(spec, target_file)
                            discovered_count += 1
                            logger.info("Discovered and created NEW passport from Crates.io: %s", pkg_name)
            except ImportError:
                logger.warning("Crates.io crawler not available.")

        return discovered_count

    def probe_runtime_passports(
        self,
        limit: int = 50,
        timeout: float = 5.0,
        safe_only: bool = True,
        **kwargs: Any,
    ) -> int:
        """
        Probe live MCP servers using stdio runtime handshake to verify tools and capabilities.
        """
        candidates: list[tuple[Path, ServerPackageSpec, list[str], dict[str, str]]] = []
        safe_commands = ("npx", "uvx", "node", "python", "python3")
        
        start_cursor = self.checkpoint_data.get("cursor") if self.checkpoint_data.get("current_stage") == "stage_runtime_probing" else None
        skip = bool(start_cursor)

        for j_file in sorted(self.output_dir.rglob("*.json")):
            if j_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
                continue
                
            if skip:
                if j_file.name == start_cursor:
                    skip = False
                continue
            try:
                spec = ServerPackageSpec.from_dict(json.loads(j_file.read_text(encoding="utf-8")))
                if not spec.versions:
                    continue
                latest_v = spec.versions[0]
                if latest_v.capabilities.get("runtime_verified"):
                    continue

                # Determine command and env
                cmd: list[str] = []
                env: dict[str, str] = {}

                for conn in latest_v.connections:
                    if conn.get("type") == "stdio" and conn.get("command"):
                        cmd = [conn["command"]] + conn.get("args", [])
                        env = conn.get("env", {})
                        break

                if not cmd:
                    if spec.ecosystem == "npm":
                        cmd = ["npx", "-y", spec.package_name]
                    elif spec.ecosystem in ("pypi", "python"):
                        cmd = ["uvx", spec.package_name]

                if not cmd:
                    continue

                if safe_only:
                    executable = Path(cmd[0]).name
                    if executable not in safe_commands:
                        continue

                candidates.append((j_file, spec, cmd, env))
                if len(candidates) >= limit:
                    break
            except Exception:
                continue

        verified_count = 0
        for j_file, spec, cmd, env in candidates:
            self._check_budget("stage_runtime_probing", cursor=j_file.name)
            try:
                tools = _sync_attr("probe_mcp_server_stdio", probe_mcp_server_stdio)(cmd, env=env, timeout_seconds=timeout)
                if not tools:
                    continue

                latest_v = spec.versions[0]
                caps = dict(latest_v.capabilities)
                caps["runtime_verified"] = True
                caps["tools"] = True
                caps["verified_tools"] = True

                clean_tools = [
                    {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "inputSchema": t.get("inputSchema", {}),
                    }
                    for t in tools
                ]

                prompt_dicts = [p.to_dict() for p in latest_v.prompt_signatures] if latest_v.prompt_signatures else []
                resource_dicts = [r.to_dict() for r in latest_v.resource_signatures] if latest_v.resource_signatures else []

                updated_v = build_version_fingerprint(
                    version=latest_v.version,
                    tools=clean_tools,
                    prompts=prompt_dicts,
                    resources=resource_dicts,
                    capabilities=caps,
                )

                # Preserve connections and release date from latest_v
                updated_v = VersionFingerprint(
                    version=latest_v.version,
                    toolset_canonical_hash=updated_v.toolset_canonical_hash,
                    tool_signatures=updated_v.tool_signatures,
                    prompt_signatures=latest_v.prompt_signatures,
                    resource_signatures=latest_v.resource_signatures,
                    release_date=latest_v.release_date,
                    dependencies=latest_v.dependencies,
                    connections=latest_v.connections,
                    capabilities=caps,
                )

                new_versions = (updated_v,) + tuple(v for v in spec.versions[1:])
                sources = list(spec.sources_merged)
                if "runtime_sandbox" not in sources:
                    sources.append("runtime_sandbox")

                updated_spec = ServerPackageSpec(
                    package_name=spec.package_name,
                    purl=spec.purl,
                    ecosystem=spec.ecosystem,
                    display_name=spec.display_name,
                    description=spec.description,
                    repository_url=spec.repository_url,
                    homepage_url=spec.homepage_url,
                    author=spec.author,
                    license=spec.license,
                    keywords=spec.keywords,
                    aliases=spec.aliases,
                    versions=new_versions,
                    sources_merged=tuple(sources),
                )

                j_file.write_text(json.dumps(updated_spec.to_dict(), indent=2), encoding="utf-8")
                verified_count += 1
                logger.info("Runtime verified %s with %d tools.", spec.package_name, len(tools))
            except Exception as e:
                logger.debug("Runtime probe failed for %s: %s", spec.package_name, e)
                continue

        return verified_count


