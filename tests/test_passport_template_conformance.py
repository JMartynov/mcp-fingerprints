"""Strict Template & Schema Conformance Verification for MCP Passports.

This test defines a canonical specification template and validates that every
passport file in data/fingerprints and the compiled passports.json.gz snapshot
strictly conforms to the expected structural invariants, types, and constraints.
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "fingerprints"
SNAPSHOT_FILE = ROOT / "passports.json.gz"

SHA256_REGEX = re.compile(r"^sha256:[a-f0-9]{64}$")
PURL_REGEX = re.compile(r"^pkg:[a-zA-Z0-9%_\-./@]+$")


# =========================================================================
# Canonical Passport Schema Template Definition
# =========================================================================
PASSPORT_TEMPLATE = {
    "required_fields": {
        "package_name": str,
        "purl": str,
        "ecosystem": str,
        "versions": list,
    },
    "optional_fields": {
        "display_name": (str, type(None)),
        "description": (str, type(None)),
        "repository_url": (str, type(None)),
        "homepage_url": (str, type(None)),
        "license": (str, type(None)),
        "verified": bool,
        "download_count": int,
        "stars": int,
        "dist_tags": dict,
        "categories": list,
        "keywords": list,
        "aliases": list,
    },
    "allowed_ecosystems": {"npm", "pypi", "golang", "generic", "github"},
}

VERSION_TEMPLATE = {
    "required_fields": {
        "version": str,
        "toolset_canonical_hash": str,
    },
    "optional_fields": {
        "release_date": (str, type(None)),
        "dependencies": dict,
        "connections": list,
        "capabilities": dict,
        "tool_signatures": list,
        "prompt_signatures": list,
        "resource_signatures": list,
    },
}

TOOL_SIGNATURE_TEMPLATE = {
    "required_fields": {
        "name": str,
        "canonical_hash": str,
    },
    "optional_fields": {
        "description": str,
        "description_hash": (str, type(None)),
        "is_mutating": bool,
        "property_keys": list,
        "required_keys": list,
        "parameter_types": dict,
        "inputSchema": dict,
        "outputSchema": (dict, type(None)),
    },
}


def validate_against_template(data: dict[str, Any], path_desc: str) -> list[str]:
    """Validate a single passport dictionary strictly against the canonical template."""
    errors: list[str] = []

    # 1. Top-Level Required Fields
    for field_name, expected_type in PASSPORT_TEMPLATE["required_fields"].items():
        if field_name not in data:
            errors.append(f"{path_desc}: Missing required top-level field '{field_name}'")
        elif not isinstance(data[field_name], expected_type):
            errors.append(
                f"{path_desc}: Field '{field_name}' must be {expected_type}, got {type(data[field_name])}"
            )

    # 2. Top-Level Optional Fields
    for field_name, expected_type in PASSPORT_TEMPLATE["optional_fields"].items():
        if field_name in data and data[field_name] is not None:
            if not isinstance(data[field_name], expected_type):
                errors.append(
                    f"{path_desc}: Optional field '{field_name}' must be {expected_type}, got {type(data[field_name])}"
                )

    # 3. PURL & Ecosystem Format
    purl = data.get("purl", "")
    if purl and not PURL_REGEX.match(purl):
        errors.append(f"{path_desc}: PURL '{purl}' does not match standard RFC PURL regex")

    eco = data.get("ecosystem", "").lower()
    if eco and eco not in PASSPORT_TEMPLATE["allowed_ecosystems"]:
        errors.append(f"{path_desc}: Ecosystem '{eco}' not in allowed list {PASSPORT_TEMPLATE['allowed_ecosystems']}")

    # 4. Versions Validation
    versions = data.get("versions", [])
    if not isinstance(versions, list) or len(versions) == 0:
        errors.append(f"{path_desc}: 'versions' must be a non-empty list")
    else:
        for idx, ver in enumerate(versions):
            v_desc = f"{path_desc} -> version[{idx}]"
            if not isinstance(ver, dict):
                errors.append(f"{v_desc}: Must be a dictionary")
                continue

            for vf_name, vf_type in VERSION_TEMPLATE["required_fields"].items():
                if vf_name not in ver:
                    errors.append(f"{v_desc}: Missing required field '{vf_name}'")
                elif not isinstance(ver[vf_name], vf_type):
                    errors.append(f"{v_desc}: Field '{vf_name}' must be {vf_type}")

            toolset_hash = ver.get("toolset_canonical_hash", "")
            if toolset_hash and not (SHA256_REGEX.match(toolset_hash) or len(toolset_hash) == 64):
                errors.append(f"{v_desc}: Invalid toolset_canonical_hash '{toolset_hash}'")

            # Validate Tool Signatures
            tools = ver.get("tool_signatures", [])
            if isinstance(tools, list):
                for t_idx, tool in enumerate(tools):
                    t_desc = f"{v_desc} -> tool[{t_idx}]"
                    if not isinstance(tool, dict):
                        errors.append(f"{t_desc}: Must be a dictionary")
                        continue

                    for tf_name, tf_type in TOOL_SIGNATURE_TEMPLATE["required_fields"].items():
                        if tf_name not in tool:
                            errors.append(f"{t_desc}: Missing required field '{tf_name}'")
                        elif not isinstance(tool[tf_name], tf_type):
                            errors.append(f"{t_desc}: Field '{tf_name}' must be {tf_type}")

                    t_hash = tool.get("canonical_hash", "")
                    if t_hash and not (SHA256_REGEX.match(t_hash) or len(t_hash) == 64):
                        errors.append(f"{t_desc}: Invalid tool canonical_hash '{t_hash}'")

    return errors


def test_template_conformance_individual_files():
    """Verify that all individual passport JSON files strictly match the canonical template."""
    if not DATA_DIR.is_dir():
        pytest.skip(f"Data directory {DATA_DIR} does not exist")

    passport_files = list(DATA_DIR.glob("*.json"))
    assert len(passport_files) >= 3000, f"Expected >= 3,000 passports, found {len(passport_files)}"

    all_errors: list[str] = []
    for pf in passport_files:
        if pf.name == "sync_state.json":
            continue
        try:
            content = json.loads(pf.read_text(encoding="utf-8"))
            errs = validate_against_template(content, pf.name)
            if errs:
                all_errors.extend(errs)
        except Exception as exc:
            all_errors.append(f"{pf.name}: JSON parse error {exc}")

    assert len(all_errors) == 0, f"Template violations in {len(all_errors)} items:\n" + "\n".join(all_errors[:10])


def test_template_conformance_snapshot_payload():
    """Verify that all passports inside passports.json.gz strictly match the canonical template."""
    if not SNAPSHOT_FILE.is_file():
        pytest.skip(f"Snapshot file {SNAPSHOT_FILE} does not exist")

    with gzip.open(SNAPSHOT_FILE, "rt", encoding="utf-8") as f:
        snapshot = json.load(f)

    assert snapshot.get("version") == "1.0.0"
    passports = snapshot.get("passports", {})
    assert len(passports) >= 3000

    all_errors: list[str] = []
    for pkg_name, pkg_data in passports.items():
        errs = validate_against_template(pkg_data, f"snapshot:{pkg_name}")
        if errs:
            all_errors.extend(errs)

    assert len(all_errors) == 0, f"Snapshot template violations in {len(all_errors)} items:\n" + "\n".join(all_errors[:10])
