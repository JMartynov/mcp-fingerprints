"""Multi-Source Synchronizer, Updater, and Discovery Engine for MCP Passports."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import io
import json
import logging
import os
import re
import ssl
import tarfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from packaging.version import parse as parse_version
from packaging.version import InvalidVersion

from mcp_fingerprints.ast_parser import (
    parse_mcp_source_code,
    parse_python_mcp_ast_bundle,
    parse_typescript_mcp_ast,
)
from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
)
from mcp_fingerprints.go_crawler import search_pkg_go_dev
from mcp_fingerprints.crawler import FingerprintGenerator
from mcp_fingerprints.crawler.maven_central import EnterpriseIndexer
from mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.monorepo_prober import match_monorepo_subpackage_dir
from mcp_fingerprints.openapi_parser import parse_openapi_spec
from mcp_fingerprints.runtime_sandbox import probe_mcp_server_stdio
from mcp_fingerprints.validator import McpServerValidator, sanitize_tool_definition


from mcp_fingerprints.sync import (
    ArchiveNotFoundError,
    CheckpointSyncMixin,
    ExtractorsSyncMixin,
    RegistrySyncMixin,
    _create_ssl_context,
    fetch_json,
    logger,
)


class PassportSynchronizer(CheckpointSyncMixin, ExtractorsSyncMixin, RegistrySyncMixin):
    """Synchronizes, discovers, and updates full-fidelity MCP Server Passports."""

    @staticmethod
    def _get_github_headers(raw: bool = False) -> dict[str, str]:
        """Build request headers for GitHub, attaching GITHUB_TOKEN or GH_TOKEN if available."""
        headers = {
            "User-Agent": "VerityRedTeam-MCPPassportSync/1.0",
        }
        if not raw:
            headers["Accept"] = "application/vnd.github.v3+json"
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _fetch_github_api_with_retry(self, url: str, timeout: float = 3.0, max_retries: int = 5) -> urllib.response.addinfourl:
        """Fetch from GitHub API with exponential backoff on HTTP 403 and 429, supporting GITHUB_TOKEN."""
        backoff = 2.0
        for attempt in range(max_retries):
            try:
                headers = self._get_github_headers()
                req = urllib.request.Request(
                    url,
                    headers=headers,
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
                    
                    if sleep_duration > 60.0:
                        logger.warning(
                            "GitHub API rate limit hit (%d) for %s, but reset time is %.1fs away (>60s). Aborting retries.",
                            he.code,
                            url,
                            sleep_duration,
                        )
                        raise
                    
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
        time_budget: int = 2400,
        ignore_checkpoint: bool = False,
        clear_checkpoint: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = Path(state_file) if state_file else self.output_dir / "sync_state.json"
        self.state: dict[str, Any] = self._load_state()
        self._last_detected_gateway: dict[str, tuple[list[dict[str, Any]], dict[str, bool]]] = {}
        
        self.time_budget = time_budget
        self.start_time = time.monotonic()
        self._stop_requested = False
        self.checkpoint_file = Path("data/.sync_checkpoint.json")
        
        if clear_checkpoint and self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            
        self.checkpoint_data = self._load_checkpoint(ignore_checkpoint)
        
        import signal
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except Exception as e:
            logger.debug(f"Could not register signal handlers: {e}")



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
