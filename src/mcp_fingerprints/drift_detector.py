"""Supply-Chain Drift and Tamper Detection Engine for MCP Server Passports."""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("mcp_fingerprints.drift_detector")


@dataclass
class TamperIncident:
    """An incident where a package's canonical tool hash or tools drifted on the same version."""

    package_name: str
    version: str
    incident_type: str  # "hash_tamper", "tool_added", "tool_removed", "new_vulnerability"
    severity: str  # "critical", "high", "medium", "low"
    details: str
    old_hash: str | None = None
    new_hash: str | None = None
    affected_tools: list[str] = field(default_factory=list)


@dataclass
class DriftAuditReport:
    """Audit report analyzing changes and supply-chain drift between two passport states."""

    packages_compared: int
    unaltered_packages: int
    version_bumps: int
    incidents: list[TamperIncident] = field(default_factory=list)
    has_tamper_incidents: bool = False
    is_clean: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "packages_compared": self.packages_compared,
            "unaltered_packages": self.unaltered_packages,
            "version_bumps": self.version_bumps,
            "is_clean": self.is_clean,
            "has_tamper_incidents": self.has_tamper_incidents,
            "incident_count": len(self.incidents),
            "incidents": [
                {
                    "package_name": inc.package_name,
                    "version": inc.version,
                    "incident_type": inc.incident_type,
                    "severity": inc.severity,
                    "details": inc.details,
                    "old_hash": inc.old_hash,
                    "new_hash": inc.new_hash,
                    "affected_tools": inc.affected_tools,
                }
                for inc in self.incidents
            ],
        }


def load_passports_map(source: Path | str | dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Load passports from directory, snapshot gzip, or dictionary into a pkg_name -> dict map."""
    if isinstance(source, dict):
        return source

    p = Path(source)
    result: dict[str, dict[str, Any]] = {}

    if p.is_dir():
        for f in p.rglob("*.json"):
            if f.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                pkg = data.get("package_name")
                if pkg:
                    result[pkg] = data
            except Exception:
                continue
    elif p.is_file():
        if p.name.endswith(".gz"):
            import gzip
            with gzip.open(p, "rt", encoding="utf-8") as gz_f:
                snapshot = json.load(gz_f)
                passports = snapshot.get("passports", {})
                if isinstance(passports, dict):
                    result.update(passports)
                elif isinstance(passports, list):
                    for pass_data in passports:
                        pkg = pass_data.get("package_name")
                        if pkg:
                            result[pkg] = pass_data
        else:
            with open(p, "r", encoding="utf-8") as json_f:
                data = json.load(json_f)
                if isinstance(data, list):
                    for pass_data in data:
                        pkg = pass_data.get("package_name")
                        if pkg:
                            result[pkg] = pass_data
                elif isinstance(data, dict):
                    if "passports" in data:
                        passports = data["passports"]
                        if isinstance(passports, dict):
                            result.update(passports)
                        elif isinstance(passports, list):
                            for pass_data in passports:
                                pkg = pass_data.get("package_name")
                                if pkg:
                                    result[pkg] = pass_data
                    elif data.get("package_name"):
                        result[data["package_name"]] = data

    return result


def compare_passports_for_drift(
    old_source: Path | str | dict[str, Any],
    new_source: Path | str | dict[str, Any],
) -> DriftAuditReport:
    """
    Detect unexpected hash mutations, silent tool additions, and new vulnerabilities on identical versions.
    """
    old_map = load_passports_map(old_source)
    new_map = load_passports_map(new_source)

    packages_compared = 0
    unaltered = 0
    version_bumps = 0
    incidents: list[TamperIncident] = []

    for pkg_name, new_passport in new_map.items():
        if pkg_name not in old_map:
            continue

        packages_compared += 1
        old_passport = old_map[pkg_name]

        old_versions = {v.get("version"): v for v in old_passport.get("versions", []) if v.get("version")}
        new_versions = {v.get("version"): v for v in new_passport.get("versions", []) if v.get("version")}

        pkg_has_drift = False

        # Check identical versions for tamper
        for ver, new_v in new_versions.items():
            if ver in old_versions:
                old_v = old_versions[ver]

                old_hash = old_v.get("toolset_canonical_hash")
                new_hash = new_v.get("toolset_canonical_hash")

                # Canonical hash drift check
                empty_hash = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                if old_hash and new_hash and old_hash != new_hash:
                    # Ignore harmless transitions from empty hash to populated hash during initial enrichment
                    if old_hash != empty_hash:
                        incidents.append(
                            TamperIncident(
                                package_name=pkg_name,
                                version=ver,
                                incident_type="hash_tamper",
                                severity="critical",
                                details=f"Canonical toolset hash altered for version {ver} without version bump.",
                                old_hash=old_hash,
                                new_hash=new_hash,
                            )
                        )
                        pkg_has_drift = True

                # Check individual tool signatures
                old_tool_names = {t.get("name") for t in old_v.get("tool_signatures", []) if t.get("name")}
                new_tool_names = {t.get("name") for t in new_v.get("tool_signatures", []) if t.get("name")}

                added_tools = new_tool_names - old_tool_names
                removed_tools = old_tool_names - new_tool_names

                if added_tools and old_tool_names:
                    incidents.append(
                        TamperIncident(
                            package_name=pkg_name,
                            version=ver,
                            incident_type="tool_added",
                            severity="high",
                            details=f"Silent addition of tools {sorted(list(added_tools))} on version {ver}.",
                            affected_tools=sorted(list(added_tools)),
                        )
                    )
                    pkg_has_drift = True

                if removed_tools and new_tool_names:
                    incidents.append(
                        TamperIncident(
                            package_name=pkg_name,
                            version=ver,
                            incident_type="tool_removed",
                            severity="medium",
                            details=f"Silent removal of tools {sorted(list(removed_tools))} on version {ver}.",
                            affected_tools=sorted(list(removed_tools)),
                        )
                    )
                    pkg_has_drift = True

                # Check newly attached vulnerabilities
                old_advs = {adv.get("id") for adv in old_v.get("vulnerability_advisories", []) if adv.get("id")}
                new_advs = {adv.get("id"): adv for adv in new_v.get("vulnerability_advisories", []) if adv.get("id")}
                new_ids = set(new_advs.keys()) - old_advs

                for nid in new_ids:
                    adv = new_advs[nid]
                    incidents.append(
                        TamperIncident(
                            package_name=pkg_name,
                            version=ver,
                            incident_type="new_vulnerability",
                            severity="high" if adv.get("severity") in ("CRITICAL", "HIGH") else "medium",
                            details=f"New advisory {nid} ({adv.get('severity', 'UNKNOWN')}) attached: {adv.get('summary', '')}",
                        )
                    )
                    pkg_has_drift = True

            else:
                version_bumps += 1

        if not pkg_has_drift:
            unaltered += 1

    has_tamper = any(inc.incident_type in ("hash_tamper", "tool_added") for inc in incidents)
    is_clean = len(incidents) == 0

    return DriftAuditReport(
        packages_compared=packages_compared,
        unaltered_packages=unaltered,
        version_bumps=version_bumps,
        incidents=incidents,
        has_tamper_incidents=has_tamper,
        is_clean=is_clean,
    )


def format_drift_report(report: DriftAuditReport) -> str:
    """Format a human-readable drift report for CLI or GitHub Actions summary."""
    lines = [
        "==================================================",
        "      MCP SUPPLY-CHAIN DRIFT & AUDIT REPORT       ",
        "==================================================",
        f"Packages Compared:  {report.packages_compared}",
        f"Unaltered Packages: {report.unaltered_packages}",
        f"Version Bumps:      {report.version_bumps}",
        f"Incidents Detected: {len(report.incidents)}",
    ]

    if report.is_clean:
        lines.append("Status:             ✅ CLEAN (No hash tampering or silent mutations)")
        lines.append("==================================================")
        return "\n".join(lines)

    status_str = "🚨 CRITICAL TAMPER DETECTED" if report.has_tamper_incidents else "⚠️  DRIFT DETECTED"
    lines.append(f"Status:             {status_str}")
    lines.append("--------------------------------------------------")
    lines.append("DETECTED DRIFT INCIDENTS:")

    for idx, inc in enumerate(report.incidents, 1):
        icon = "🚨" if inc.severity in ("critical", "high") else "⚠️"
        lines.append(f"\n{idx}. [{inc.severity.upper()}] {inc.package_name} (v{inc.version}) {icon}")
        lines.append(f"   Type:    {inc.incident_type}")
        lines.append(f"   Details: {inc.details}")
        if inc.old_hash and inc.new_hash:
            lines.append(f"   Old Hash: {inc.old_hash}")
            lines.append(f"   New Hash: {inc.new_hash}")
        if inc.affected_tools:
            lines.append(f"   Tools:    {', '.join(inc.affected_tools)}")

    lines.append("==================================================")
    return "\n".join(lines)


def dispatch_drift_webhook(
    report: DriftAuditReport,
    webhook_url: str | None = None,
    timeout: float = 5.0,
) -> bool:
    """Dispatch drift audit notification payload to a configured webhook (Slack, Discord, generic)."""
    target_url = (
        webhook_url
        or os.environ.get("SECURITY_WEBHOOK_URL")
        or os.environ.get("WEBHOOK_URL")
        or os.environ.get("SLACK_WEBHOOK_URL")
    )
    if not target_url:
        logger.info("No webhook URL configured; skipping notification dispatch.")
        return False

    summary_text = (
        f"🚨 MCP Supply-Chain Tamper Alert: {len(report.incidents)} incident(s) detected across {report.packages_compared} packages!"
        if report.has_tamper_incidents
        else f"⚠️ MCP Drift Notification: {len(report.incidents)} drift event(s) detected."
    )

    payload = {
        "text": summary_text,
        "report": report.to_dict(),
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "MCP-Passport-DriftDetector/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        logger.warning("Failed to dispatch webhook: %s", e)
        return False
