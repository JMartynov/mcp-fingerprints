"""Checkpoint persistence, budget tracking, and pipeline stage orchestration."""

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


class CheckpointSyncMixin:
    """Mixin providing signal handling, checkpointing, and sync pipeline stages."""

    def _handle_signal(self, signum, frame):
        logger.warning(f"Received signal {signum}, requesting graceful shutdown...")
        self._stop_requested = True

    def _load_checkpoint(self, ignore_checkpoint: bool) -> dict[str, Any]:
        if ignore_checkpoint or not self.checkpoint_file.exists():
            return {
                "checkpoint_active": False,
                "current_stage": None,
                "substage": None,
                "page": None,
                "cursor": None,
                "completed_stages": [],
                "timestamp": None,
                "reason": None
            }
        try:
            return json.loads(self.checkpoint_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return {
                "checkpoint_active": False,
                "current_stage": None,
                "substage": None,
                "page": None,
                "cursor": None,
                "completed_stages": [],
                "timestamp": None,
                "reason": None
            }

    def _save_checkpoint(self, stage: str, substage: str | None = None, page: int | None = None, cursor: str | None = None, reason: str = "time_budget_reached"):
        self.checkpoint_data["checkpoint_active"] = True
        self.checkpoint_data["current_stage"] = stage
        self.checkpoint_data["substage"] = substage
        self.checkpoint_data["page"] = page
        self.checkpoint_data["cursor"] = cursor
        self.checkpoint_data["timestamp"] = datetime.datetime.now(datetime.UTC).isoformat()
        self.checkpoint_data["reason"] = reason
        
        import os
        import tempfile
        
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=self.checkpoint_file.parent, prefix=".sync_checkpoint_", suffix=".json")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint_data, f, indent=2)
            os.replace(temp_path, self.checkpoint_file)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _clear_checkpoint(self):
        self.checkpoint_data = {
            "checkpoint_active": False,
            "current_stage": None,
            "substage": None,
            "page": None,
            "cursor": None,
            "completed_stages": [],
            "timestamp": None,
            "reason": None
        }
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def _mark_stage_completed(self, stage: str):
        if stage not in self.checkpoint_data["completed_stages"]:
            self.checkpoint_data["completed_stages"].append(stage)
        self.checkpoint_data["checkpoint_active"] = False
        self.checkpoint_data["current_stage"] = None
        self.checkpoint_data["substage"] = None
        self.checkpoint_data["page"] = None
        self.checkpoint_data["cursor"] = None
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            
    def _is_stage_completed(self, stage: str) -> bool:
        return stage in self.checkpoint_data.get("completed_stages", [])

    def _check_budget(self, stage: str, substage: str | None = None, page: int | None = None, cursor: str | None = None, safety_threshold: float = 30.0) -> bool:
        """Returns True if budget is exhausted or stop is requested. False otherwise."""
        if self._stop_requested:
            self._save_checkpoint(stage, substage, page, cursor, reason="signal_interrupt")
            logger.info(f"Stop requested via signal. Gracefully checkpointed at stage '{stage}' (substage {substage}, page {page}, cursor {cursor}). Exiting with status 0.")
            self._save_state()
            import sys
            sys.exit(0)
            
        if self.time_budget > 0:
            elapsed = time.monotonic() - self.start_time
            if elapsed + safety_threshold >= self.time_budget:
                self._save_checkpoint(stage, substage, page, cursor, reason="time_budget_reached")
                logger.info(f"Time budget reached. Gracefully checkpointed at stage '{stage}' (substage {substage}, page {page}, cursor {cursor}). Exiting with status 0.")
                self._save_state()
                import sys
                sys.exit(0)
        return False

    def run_sync_pipeline(
        self,
        update_existing: bool = False,
        enrich_ast: bool = False,
        discover_new: bool = False,
        docker: bool = False,
        polyglot: bool = False,
        limit: int = 500,
        max_workers: int = 8,
        probe_runtime: bool = False,
        runtime_limit: int = 50,
        runtime_timeout: float = 5.0,
    ) -> None:
        """Run the synchronization pipeline stage by stage."""
        if update_existing and not self._is_stage_completed("stage_update_existing"):
            self.update_existing_passports()
            self._mark_stage_completed("stage_update_existing")

        if enrich_ast and not self._is_stage_completed("stage_enrich_ast"):
            self.enrich_zero_tool_passports(limit=limit, max_workers=max_workers)
            self._mark_stage_completed("stage_enrich_ast")

        if discover_new and not self._is_stage_completed("stage_discover_new"):
            self.discover_new_mcps(limit=limit, docker=docker, polyglot=polyglot)
            self._mark_stage_completed("stage_discover_new")

        if probe_runtime and not self._is_stage_completed("stage_runtime_probing"):
            logger.info("Probing runtime handshakes for up to %d safe servers...", runtime_limit)
            probed = self.probe_runtime_passports(limit=runtime_limit, timeout=runtime_timeout)
            logger.info("Successfully runtime-verified %d servers.", probed)
            self._mark_stage_completed("stage_runtime_probing")

        # Cleanup at the very end
        self._clear_checkpoint()

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



