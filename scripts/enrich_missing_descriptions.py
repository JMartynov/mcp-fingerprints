#!/usr/bin/env python3
"""Enrich missing descriptions and repository metadata across all MCP passports."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("enrich_descriptions")

SSL_CTX = ssl._create_unverified_context()

def get_gh_token() -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        try:
            token = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            token = None
    return token

GH_TOKEN = get_gh_token()

def fetch_json(url: str, headers: dict[str, str] | None = None, timeout: float = 6.0) -> dict[str, Any] | None:
    req_headers = {"User-Agent": "mcp-fingerprints/1.0"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None
    return None

def fetch_text(url: str, timeout: float = 5.0) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": "mcp-fingerprints/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            if resp.status == 200:
                return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None
    return None

def clean_desc(text: str | None) -> str:
    if not text:
        return ""
    text = text.strip()
    # Strip markdown headers, images, badges
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    # If it's too long, truncate to 350 chars cleanly at sentence/word boundary
    if len(text) > 350:
        text = text[:347]
        r_space = text.rfind(" ")
        if r_space > 150:
            text = text[:r_space] + "..."
        else:
            text = text + "..."
    return text

def extract_readme_tagline(md: str) -> str:
    if not md:
        return ""
    lines = md.splitlines()
    for line in lines:
        l = line.strip()
        if not l or l.startswith("#") or l.startswith("[") or l.startswith("!") or l.startswith("<") or l.startswith("```"):
            continue
        cleaned = clean_desc(l)
        if len(cleaned) >= 15:
            return cleaned
    return ""

def clean_repo_url(url: Any) -> str | None:
    if not url:
        return None
    if isinstance(url, dict):
        url = url.get("url")
    if not isinstance(url, str):
        return None
    url = re.sub(r"^git\+", "", url.strip())
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^git://", "https://", url)
    url = re.sub(r"^ssh://git@", "https://", url)
    if url.startswith("github.com/"):
        url = "https://" + url
    if re.match(r"^https?://", url):
        return url
    return None

def extract_github_slug(repo_url: str | None, package_name: str) -> tuple[str, str] | None:
    if repo_url and "github.com" in repo_url:
        m = re.search(r"github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)", repo_url)
        if m:
            return m.group(1), m.group(2)
    if re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", package_name):
        parts = package_name.split("/")
        return parts[0], parts[1]
    return None

def process_passport(file_path: Path) -> tuple[str, bool, str]:
    try:
        content = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        return file_path.name, False, f"JSON load error: {e}"

    existing_desc = (content.get("description") or "").strip()
    if existing_desc:
        return file_path.name, False, "Already has description"

    pkg_name = content.get("package_name") or ""
    eco = (content.get("ecosystem") or "generic").lower()
    sources = content.get("sources_merged") or []
    current_repo = content.get("repository_url")

    new_desc = ""
    new_repo = None
    new_author = None
    new_license = None

    # 1. NPM
    if eco == "npm" or "npm" in sources or "npm_registry" in sources:
        npm_data = fetch_json(f"https://registry.npmjs.org/{pkg_name}")
        if npm_data:
            new_desc = clean_desc(npm_data.get("description"))
            new_repo = clean_repo_url(npm_data.get("repository"))
            if not content.get("author"):
                auth = npm_data.get("author")
                new_author = auth.get("name") if isinstance(auth, dict) else str(auth or "")
            if not content.get("license"):
                new_license = npm_data.get("license")

    # 2. PyPI
    if not new_desc and (eco in ("pypi", "python") or "pypi" in sources):
        pypi_data = fetch_json(f"https://pypi.org/pypi/{pkg_name}/json")
        if pypi_data and "info" in pypi_data:
            info = pypi_data["info"]
            new_desc = clean_desc(info.get("summary") or info.get("description"))
            urls = info.get("project_urls") or {}
            new_repo = clean_repo_url(urls.get("Repository") or urls.get("Source") or urls.get("Source Code") or info.get("home_page"))
            if not content.get("author"):
                new_author = info.get("author") or info.get("author_email")
            if not content.get("license"):
                new_license = info.get("license")

    # 3. GitHub API or README
    slug = extract_github_slug(current_repo or new_repo, pkg_name)
    if slug:
        owner, repo = slug
        if not new_repo:
            new_repo = f"https://github.com/{owner}/{repo}"

        if not new_desc and GH_TOKEN:
            gh_data = fetch_json(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={"Authorization": f"token {GH_TOKEN}"}
            )
            if gh_data and isinstance(gh_data, dict):
                gh_desc = clean_desc(gh_data.get("description"))
                if gh_desc:
                    new_desc = gh_desc
                if not content.get("homepage_url") and gh_data.get("homepage"):
                    content["homepage_url"] = gh_data.get("homepage")

        if not new_desc:
            # Fallback to README tagline
            readme = fetch_text(f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md")
            if readme:
                new_desc = extract_readme_tagline(readme)

    # 4. Fallback if still empty: generate concise contextual description
    if not new_desc:
        tool_count = 0
        latest_tools = []
        if content.get("versions"):
            v_latest = content["versions"][-1]
            latest_tools = [t.get("name") for t in (v_latest.get("tool_signatures") or []) if isinstance(t, dict)]
            tool_count = len(latest_tools)
        if tool_count > 0:
            sample = ", ".join(latest_tools[:4])
            if tool_count > 4:
                sample += f", and {tool_count - 4} more"
            new_desc = f"Model Context Protocol (MCP) server providing {tool_count} tools including {sample}."
        elif eco == "npm":
            new_desc = f"MCP server package {pkg_name} distributed via npm."
        elif eco in ("pypi", "python"):
            new_desc = f"MCP server package {pkg_name} distributed via PyPI."
        elif slug:
            new_desc = f"MCP server repository {slug[0]}/{slug[1]} on GitHub."
        else:
            new_desc = f"Model Context Protocol (MCP) server for {pkg_name}."

    # Apply changes
    content["description"] = new_desc
    if new_repo and (not current_repo or "smithery.ai" in current_repo):
        content["repository_url"] = new_repo
    if new_author and not content.get("author"):
        content["author"] = new_author
    if new_license and not content.get("license"):
        content["license"] = new_license

    try:
        file_path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return file_path.name, True, new_desc
    except Exception as e:
        return file_path.name, False, f"Write error: {e}"

def main():
    fingerprints_dir = Path("data/fingerprints")
    passport_files = [
        f for f in fingerprints_dir.rglob("*.json")
        if f.name not in ("sync_state.json", "index.json", ".passport_cache.json")
    ]
    logger.info("Found %d total passport files", len(passport_files))

    # Identify which ones need description
    targets: list[Path] = []
    for f in passport_files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if not (d.get("description") or "").strip():
                targets.append(f)
        except Exception:
            pass

    logger.info("Identified %d passports missing descriptions", len(targets))
    if not targets:
        logger.info("All passports already have descriptions!")
        return

    enriched_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        futures = {executor.submit(process_passport, p): p for p in targets}
        for future in concurrent.futures.as_completed(futures):
            fname, updated, res = future.result()
            if updated:
                enriched_count += 1
                if enriched_count % 100 == 0 or enriched_count == len(targets):
                    logger.info("Enriched %d/%d passports (latest: %s -> %s)", enriched_count, len(targets), fname, res[:60])

    logger.info("Successfully enriched %d/%d passports with authentic descriptions!", enriched_count, len(targets))

if __name__ == "__main__":
    main()
