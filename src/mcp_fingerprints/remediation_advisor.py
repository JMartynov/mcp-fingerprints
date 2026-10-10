from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from packaging.version import InvalidVersion
from packaging.version import parse as parse_version

from mcp_fingerprints.index import FingerprintFastIndex


@dataclass
class RemediationAction:
    package_name: str
    current_version: str
    cve_list: list[str]
    action_type: Literal["upgrade", "replace", "none"]
    target_package: str | None = None
    target_version: str | None = None
    similarity_score: float | None = None


@dataclass
class RemediationReport:
    is_clean: bool
    actions: list[RemediationAction] = field(default_factory=list)
    unremediated_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_clean": self.is_clean,
            "actions": [
                {
                    "package_name": a.package_name,
                    "current_version": a.current_version,
                    "cve_list": a.cve_list,
                    "action_type": a.action_type,
                    "target_package": a.target_package,
                    "target_version": a.target_version,
                    "similarity_score": a.similarity_score,
                }
                for a in self.actions
            ],
            "unremediated_count": self.unremediated_count,
        }


def _extract_version_from_cmd(command: str, args: list[str]) -> str | None:
    # Basic heuristic to extract version from npx or uvx command args
    # e.g., args: ["-y", "some-pkg@1.2.3"] or npx some-pkg@1.2.3
    # Look for @<version> in the last argument or the command
    for arg in reversed(args):
        if "@" in arg:
            parts = arg.split("@")
            if len(parts) > 1:
                return parts[-1]

    if "@" in command:
        parts = command.split("@")
        if len(parts) > 1:
            return parts[-1]

    return None


def _jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return float(intersection) / union if union > 0 else 0.0


def evaluate_client_config(
    config_path: str | Path,
    passport_dir: str | Path,
) -> RemediationReport:
    """Evaluate a client configuration for vulnerabilities and propose remediations."""
    p = Path(config_path)
    if not p.is_file():
        raise FileNotFoundError(f"Client configuration file not found: {p}")

    raw_conf = json.loads(p.read_text(encoding="utf-8"))

    servers_dict: dict[str, Any] = {}
    if "mcpServers" in raw_conf and isinstance(raw_conf["mcpServers"], dict):
        servers_dict = raw_conf["mcpServers"]
    elif "context_servers" in raw_conf and isinstance(
        raw_conf["context_servers"], dict
    ):
        servers_dict = raw_conf["context_servers"]

    index = FingerprintFastIndex()
    index.load_from_directory(passport_dir, use_cache=False)

    actions: list[RemediationAction] = []
    unremediated_count = 0

    for server_conf in servers_dict.values():
        command = server_conf.get("command", "")
        args = server_conf.get("args", [])

        # Try to find package in index
        # Heuristic: the package name might be in the command or the first non-flag arg
        pkg_hint = None
        current_version = None
        for arg in reversed(args):
            if "@" in arg:
                parts = arg.split("@")
                if len(parts) > 1:
                    pkg_hint = parts[0]
                    current_version = parts[1]
                    break

        if not pkg_hint:
            if command in ("npx", "uvx", "docker"):
                for arg in args:
                    if not arg.startswith("-"):
                        pkg_hint = arg
                        break
            else:
                pkg_hint = command

        if not pkg_hint:
            continue

        pkg_spec = index.find_package_by_hint_or_alias(pkg_hint)
        if not pkg_spec:
            continue

        if not current_version:
            # If no version specified, assume latest or unknown. We can't easily check vulnerability.
            continue

        # Check if version is vulnerable
        sec_profile = pkg_spec.security_profile
        vuln_versions = sec_profile.get("vulnerable_versions", [])

        if current_version not in vuln_versions:
            continue  # Clean version

        # It's vulnerable! Get CVE list
        cve_list = [
            adv.get("id")
            for adv in sec_profile.get("advisories", [])
            if current_version in adv.get("affected_versions", [])
        ]

        # Pathway 1: Version Upgrade
        try:
            curr_v = parse_version(current_version)
        except InvalidVersion:
            curr_v = None

        target_version = None

        if curr_v:
            safe_versions = []
            for v_fp in pkg_spec.versions:
                if v_fp.version not in vuln_versions:
                    try:
                        pv = parse_version(v_fp.version)
                        if pv > curr_v:
                            safe_versions.append(pv)
                    except InvalidVersion:
                        pass

            if safe_versions:
                safe_versions.sort()
                target_version = str(safe_versions[0])

        if target_version:
            actions.append(
                RemediationAction(
                    package_name=pkg_spec.package_name,
                    current_version=current_version,
                    cve_list=cve_list,
                    action_type="upgrade",
                    target_package=pkg_spec.package_name,
                    target_version=target_version,
                    similarity_score=1.0,
                )
            )
            continue

        # Pathway 2: Replace Server
        # Find tools in current version
        curr_tools = set()
        for v_fp in pkg_spec.versions:
            if v_fp.version == current_version:
                for t in v_fp.tool_signatures:
                    curr_tools.add(t.name)
                break

        if not curr_tools:
            actions.append(
                RemediationAction(
                    package_name=pkg_spec.package_name,
                    current_version=current_version,
                    cve_list=cve_list,
                    action_type="none",
                )
            )
            unremediated_count += 1
            continue

        # Search index for alternatives
        best_alt = None
        best_score = 0.0
        best_alt_version = None

        for alt_name, alt_spec in index.packages.items():
            if alt_name == pkg_spec.package_name:
                continue

            alt_sec_profile = alt_spec.security_profile
            alt_vuln_versions = alt_sec_profile.get("vulnerable_versions", [])

            # Find latest safe version of alternative
            safe_alt_versions = []
            for v_fp in alt_spec.versions:
                if v_fp.version not in alt_vuln_versions:
                    try:
                        safe_alt_versions.append((parse_version(v_fp.version), v_fp))
                    except InvalidVersion:
                        pass

            if not safe_alt_versions:
                continue

            safe_alt_versions.sort(key=lambda x: x[0], reverse=True)
            latest_safe_v_fp = safe_alt_versions[0][1]

            alt_tools = {t.name for t in latest_safe_v_fp.tool_signatures}
            score = _jaccard_similarity(curr_tools, alt_tools)

            if score > best_score:
                best_score = score
                best_alt = alt_name
                best_alt_version = latest_safe_v_fp.version

        if best_alt and best_score > 0.0:
            actions.append(
                RemediationAction(
                    package_name=pkg_spec.package_name,
                    current_version=current_version,
                    cve_list=cve_list,
                    action_type="replace",
                    target_package=best_alt,
                    target_version=best_alt_version,
                    similarity_score=best_score,
                )
            )
        else:
            actions.append(
                RemediationAction(
                    package_name=pkg_spec.package_name,
                    current_version=current_version,
                    cve_list=cve_list,
                    action_type="none",
                )
            )
            unremediated_count += 1

    is_clean = len(actions) == 0 and unremediated_count == 0
    return RemediationReport(
        is_clean=is_clean, actions=actions, unremediated_count=unremediated_count
    )

def apply_remediation_patch(config_text: str, report: RemediationReport, strategy: str = "all") -> str:
    """Safely apply a remediation report to raw configuration text preserving JSON comments."""
    import re
    
    new_text = config_text
    
    for action in report.actions:
        if action.action_type == "upgrade" and strategy in ("all", "upgrade"):
            # We want to replace pkg@old -> pkg@new in the raw string.
            # E.g. "my-pkg@1.0.0" -> "my-pkg@1.1.0"
            if action.current_version:
                target_str = f"{action.package_name}@{action.current_version}"
                replace_str = f"{action.package_name}@{action.target_version}"
                new_text = new_text.replace(target_str, replace_str)
        elif action.action_type == "replace" and strategy in ("all", "replace"):
            # Replace package name and version
            if action.current_version:
                target_str = f"{action.package_name}@{action.current_version}"
                replace_str = f"{action.target_package}@{action.target_version}"
                new_text = new_text.replace(target_str, replace_str)
            else:
                new_text = re.sub(r'\b' + re.escape(action.package_name) + r'\b', action.target_package, new_text)

    return new_text
