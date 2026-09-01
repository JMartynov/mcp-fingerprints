"""Multi-Source Synchronizer, Updater, and Discovery Engine for MCP Passports."""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

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


class PassportSynchronizer:
    """Synchronizes, discovers, and updates full-fidelity MCP Server Passports."""

    def __init__(
        self,
        output_dir: str | Path = "data/fingerprints",
        state_file: str | Path | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = Path(state_file) if state_file else self.output_dir / "sync_state.json"
        self.state: dict[str, Any] = self._load_state()

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
    ) -> ServerPackageSpec | None:
        """Merge complementary metadata from Smithery, npm, and PyPI into one Passport."""
        sources: list[str] = []
        tools: list[dict[str, Any]] = []
        prompts: list[dict[str, Any]] = []
        resources: list[dict[str, Any]] = []
        connections: list[dict[str, Any]] = []
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
        if smithery_data:
            sources.append("smithery")
            tools = [t for t in (smithery_data.get("tools") or []) if isinstance(t, dict)]
            prompts = [p for p in (smithery_data.get("prompts") or []) if isinstance(p, dict)]
            resources = [r for r in (smithery_data.get("resources") or []) if isinstance(r, dict)]
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
                v_fp = build_version_fingerprint(
                    version=v_str,
                    tools=v_tools,
                    prompts=prompts if v_tools else None,
                    resources=resources if v_tools else None,
                    release_date=v_date,
                    capabilities={
                        "tools": bool(v_tools),
                        "prompts": bool(prompts),
                        "resources": bool(resources),
                    },
                )
                v_fp_dict = v_fp.to_dict()
                v_fp_dict["dependencies"] = v_deps
                v_fp_dict["connections"] = connections if v_tools else []
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
                v_date = r_list[0].get("upload_time_iso_8601") if r_list else None
                v_tools = tools if v_str == latest_v else []
                v_fp = build_version_fingerprint(
                    version=v_str,
                    tools=v_tools,
                    prompts=prompts if v_tools else None,
                    resources=resources if v_tools else None,
                    release_date=v_date,
                )
                all_versions.append(v_fp)

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
                    },
                )
                v_fp_dict = v_fp.to_dict()
                v_fp_dict["connections"] = connections
                all_versions.append(VersionFingerprint.from_dict(v_fp_dict))

        # If no multi-version releases, build single version snapshot
        if not all_versions:
            ver_fp = build_version_fingerprint(
                version="1.0.0",
                tools=tools,
                prompts=prompts,
                resources=resources,
            )
            v_fp_dict = ver_fp.to_dict()
            v_fp_dict["connections"] = connections
            all_versions.append(VersionFingerprint.from_dict(v_fp_dict))

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
            has_tools_declared=bool(tools) or any(bool(v.tool_signatures) for v in all_versions),
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

    def update_existing_passports(self) -> int:
        """Scan all passport files in data/fingerprints/ and check for upstream version updates."""
        updated_count = 0
        for j_file in sorted(self.output_dir.rglob("*.json")):
            if j_file.name in ("sync_state.json", "index.json"):
                continue
            try:
                spec = ServerPackageSpec.from_dict(json.loads(j_file.read_text(encoding="utf-8")))
                pkg_name = spec.package_name
                eco = spec.ecosystem.lower()

                # Check upstream for new versions
                if eco == "npm":
                    npm_meta, _ = fetch_json(
                        f"https://registry.npmjs.org/{pkg_name}",
                        headers={"Accept": "application/vnd.npm.install-v1+json"},
                    )
                    if npm_meta and "dist-tags" in npm_meta:
                        latest_dist = npm_meta["dist-tags"].get("latest")
                        known_versions = {v.version for v in spec.versions}
                        if latest_dist and latest_dist not in known_versions:
                            logger.info(
                                "Found NEW version for %s: %s (was %s)",
                                pkg_name,
                                latest_dist,
                                known_versions,
                            )
                            # Extract latest known tool definitions from existing spec
                            existing_tools = []
                            existing_prompts = []
                            existing_resources = []
                            for v in reversed(spec.versions):
                                if v.tool_signatures and not existing_tools:
                                    existing_tools = [t.to_dict() for t in v.tool_signatures]
                                if v.prompt_signatures and not existing_prompts:
                                    existing_prompts = [p.to_dict() for p in v.prompt_signatures]
                                if v.resource_signatures and not existing_resources:
                                    existing_resources = [
                                        r.to_dict() for r in v.resource_signatures
                                    ]

                            smithery_simulated = (
                                {
                                    "tools": existing_tools,
                                    "prompts": existing_prompts,
                                    "resources": existing_resources,
                                }
                                if existing_tools
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
            except Exception as exc:
                logger.debug("Error checking updates for %s: %s", j_file.name, exc)
        logger.info("Updated %d existing passports with new release versions", updated_count)
        self._save_state()
        return updated_count

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
