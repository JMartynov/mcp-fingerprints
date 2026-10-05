"""Vulnerability enrichment engine bridging OSV security advisories into MCP server passports."""

from __future__ import annotations

import gzip
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packaging.version import Version, parse as parse_version

from mcp_fingerprints.canonicalizer import canonicalize_json
from mcp_fingerprints.models import ServerPackageSpec

logger = logging.getLogger("mcp_fingerprints.enricher")


class VulnerabilityEnricher:
    """Enriches ServerPackageSpec passports with OSV vulnerability metadata."""

    def __init__(self, vulnerabilities_path: str | Path) -> None:
        self.vulns_path = Path(vulnerabilities_path)
        self.advisories_by_package: dict[str, list[dict[str, Any]]] = {}
        self._load_vulnerabilities()

    def _load_vulnerabilities(self) -> None:
        """Load and index OSV advisories from a gzip or plain JSON file."""
        if not self.vulns_path.exists():
            raise FileNotFoundError(f"Vulnerability file not found: {self.vulns_path}")

        if str(self.vulns_path).endswith(".gz"):
            with gzip.open(self.vulns_path, "rt", encoding="utf-8") as f:
                data = json.load(f)
        else:
            with open(self.vulns_path, "rt", encoding="utf-8") as f:
                data = json.load(f)

        records: list[dict[str, Any]] = []
        if isinstance(data, dict):
            raw_vulns = data.get("vulnerabilities", {})
            if isinstance(raw_vulns, dict):
                records = list(raw_vulns.values())
            elif isinstance(raw_vulns, list):
                records = raw_vulns
        elif isinstance(data, list):
            records = data

        for record in records:
            affected_list = record.get("affected") or []
            for aff in affected_list:
                pkg_obj = aff.get("package") or {}
                name = pkg_obj.get("name")
                eco = pkg_obj.get("ecosystem", "").lower()
                if name:
                    key = f"{eco}:{name.lower()}"
                    self.advisories_by_package.setdefault(key, []).append(record)
                    self.advisories_by_package.setdefault(name.lower(), []).append(record)

        logger.info(
            "Loaded and indexed %d vulnerability records across %d packages",
            len(records),
            len(self.advisories_by_package),
        )

    @staticmethod
    def is_version_vulnerable(
        version_str: str,
        ranges: list[dict[str, Any]],
        explicit_versions: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """Check whether a package version falls within any affected range or explicit list."""
        if explicit_versions and version_str in explicit_versions:
            return True, None
        try:
            ver = parse_version(version_str)
        except Exception:
            return False, None

        for r in ranges:
            if r.get("type") != "SEMVER":
                continue
            events = r.get("events", [])
            intros: list[Any] = []
            fixes: list[Any] = []
            last_affs: list[Any] = []
            for ev in events:
                if "introduced" in ev:
                    intro_str = str(ev["introduced"]).strip()
                    if intro_str and intro_str != "0":
                        try:
                            intros.append(parse_version(intro_str))
                        except Exception:
                            pass
                if "fixed" in ev:
                    fix_str = str(ev["fixed"]).strip()
                    if fix_str:
                        try:
                            fixes.append(parse_version(fix_str))
                        except Exception:
                            pass
                if "last_affected" in ev:
                    last_str = str(ev["last_affected"]).strip()
                    if last_str:
                        try:
                            last_affs.append(parse_version(last_str))
                        except Exception:
                            pass

            min_intro = min(intros) if intros else None
            min_fix = min(fixes) if fixes else None
            max_last = max(last_affs) if last_affs else None

            if min_intro and ver < min_intro:
                continue
            if min_fix and ver >= min_fix:
                continue
            if max_last and ver > max_last:
                continue

            fixed_str = str(min_fix) if min_fix else None
            return True, fixed_str

        return False, None

    @staticmethod
    def extract_severity_and_cvss(record: dict[str, Any]) -> tuple[str, float]:
        """Extract severity string and numeric CVSS score from an OSV record."""
        db_spec = record.get("database_specific") or {}
        cvss = float(db_spec.get("cvss_score") or 0.0)
        sev = str(db_spec.get("severity") or "")

        if not cvss or not sev:
            aff_list = record.get("affected") or []
            if aff_list and isinstance(aff_list[0], dict):
                aff_db = aff_list[0].get("database_specific") or {}
                if not cvss:
                    cvss = float(aff_db.get("cvss_score") or 0.0)
                if not sev:
                    sev = str(aff_db.get("severity") or "")

        if not sev:
            for s_entry in record.get("severity") or []:
                s_type = s_entry.get("type", "")
                if "CVSS" in s_type:
                    sev = "HIGH"
                    if cvss == 0.0:
                        cvss = 7.5

        if not sev:
            sev = "UNKNOWN"
        return sev.upper(), cvss

    def enrich_spec(self, spec: ServerPackageSpec) -> ServerPackageSpec:
        """Enrich a single ServerPackageSpec with known advisories and vulnerable versions."""
        eco = spec.ecosystem.lower()
        pkg_name = spec.package_name.lower()
        key = f"{eco}:{pkg_name}"
        records = self.advisories_by_package.get(key) or self.advisories_by_package.get(pkg_name) or []

        # Deduplicate records by advisory ID
        seen_ids = set()
        deduped_records = []
        for r in records:
            r_id = r.get("id")
            if r_id and r_id not in seen_ids:
                seen_ids.add(r_id)
                deduped_records.append(r)

        matched_advisories: list[dict[str, Any]] = []
        all_vulnerable_versions: set[str] = set()
        max_cvss = 0.0

        for rec in deduped_records:
            rec_id = rec.get("id")
            summary = rec.get("summary") or ""
            sev, cvss = self.extract_severity_and_cvss(rec)
            if cvss > max_cvss:
                max_cvss = cvss

            affected_for_this_spec: list[str] = []
            fixed_v = None
            for aff in rec.get("affected") or []:
                aff_pkg = aff.get("package", {}).get("name", "").lower()
                if aff_pkg not in (pkg_name, f"{eco}:{pkg_name}"):
                    continue
                ranges = aff.get("ranges") or []
                exp_vers = aff.get("versions") or []
                for v in spec.versions:
                    vuln, fix = self.is_version_vulnerable(v.version, ranges, exp_vers)
                    if vuln:
                        affected_for_this_spec.append(v.version)
                        all_vulnerable_versions.add(v.version)
                        if fix and not fixed_v:
                            fixed_v = fix

            if affected_for_this_spec:
                matched_advisories.append({
                    "id": rec_id,
                    "summary": summary,
                    "severity": sev,
                    "cvss_score": cvss,
                    "fixed_version": fixed_v,
                    "affected_versions": sorted(affected_for_this_spec),
                })

        profile = {
            "advisories_count": len(matched_advisories),
            "max_cvss_score": round(max_cvss, 1),
            "has_known_vulnerabilities": len(matched_advisories) > 0,
            "advisories": matched_advisories,
            "vulnerable_versions": sorted(list(all_vulnerable_versions)),
            "last_audited_utc": datetime.now(timezone.utc).isoformat(),
        }

        spec_dict = spec.to_dict()
        spec_dict["security_profile"] = profile
        return ServerPackageSpec.from_dict(spec_dict)

    def enrich_directory(self, directory: str | Path) -> tuple[int, int]:
        """Enrich all passports in directory. Returns (total_scanned, enriched_with_vulns)."""
        target_dir = Path(directory)
        total_scanned = 0
        enriched_with_vulns = 0

        for j_file in sorted(target_dir.rglob("*.json")):
            if j_file.name in ("sync_state.json", "index.json"):
                continue
            try:
                raw_spec = json.loads(j_file.read_text(encoding="utf-8"))
                spec = ServerPackageSpec.from_dict(raw_spec)
                enriched = self.enrich_spec(spec)
                total_scanned += 1
                if enriched.security_profile.get("has_known_vulnerabilities"):
                    enriched_with_vulns += 1
                j_file.write_text(canonicalize_json(enriched.to_dict()), encoding="utf-8")
            except Exception as exc:
                logger.debug("Error enriching %s: %s", j_file.name, exc)

        logger.info(
            "Enrichment completed: %d passports audited, %d identified with known vulnerabilities",
            total_scanned,
            enriched_with_vulns,
        )
        return total_scanned, enriched_with_vulns
