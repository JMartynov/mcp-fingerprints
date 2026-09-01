"""Schema validator for MCP Server Passports verifying structural invariants and completeness."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from mcp_fingerprints.models import ServerPackageSpec

logger = logging.getLogger("verity.passport.schema_validator")

# SHA-256 pattern (hex encoded with sha256: prefix)
SHA256_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")

# Package URL (PURL) pattern per RFC 3986
PURL_PATTERN = re.compile(r"^pkg:(npm|pypi|golang|generic|github)/[a-zA-Z0-9%_\-./@]+$")


class PassportSchemaValidator:
    """Validates structural integrity, type constraints, and schema conformance."""

    @classmethod
    def validate_passport_dict(
        cls,
        data: dict[str, Any],
        filename: str = "passport.json",
    ) -> tuple[bool, list[str]]:
        """Validate a single parsed passport dictionary against schema rules."""
        errors: list[str] = []

        # 1. Required top-level attributes
        required_top_level = ["package_name", "purl", "ecosystem", "versions"]
        for field in required_top_level:
            if field not in data or not data[field]:
                errors.append(f"Missing required top-level field '{field}' in {filename}")

        # 2. PURL format validation
        purl = data.get("purl", "")
        if purl and not PURL_PATTERN.match(purl):
            errors.append(f"Invalid PURL format '{purl}' in {filename}")

        # 3. Ecosystem validation
        eco = data.get("ecosystem", "").lower()
        if eco not in ("npm", "pypi", "golang", "generic", "github"):
            errors.append(f"Unknown ecosystem '{eco}' in {filename}")

        # 4. Versions array validation
        versions = data.get("versions", [])
        if not isinstance(versions, list) or not versions:
            errors.append(f"'versions' must be a non-empty list in {filename}")
        else:
            for idx, v in enumerate(versions):
                v_num = v.get("version", "")
                if not v_num:
                    errors.append(f"Version at idx {idx} missing 'version' in {filename}")

                # Canonical hash format
                hash_val = v.get("toolset_canonical_hash", "")
                if not hash_val or not SHA256_PATTERN.match(hash_val):
                    errors.append(f"Invalid toolset_canonical_hash in {filename} ({v_num})")

                # Tool signatures validation
                tools = v.get("tool_signatures", [])
                if not isinstance(tools, list):
                    errors.append(f"Tool signatures not a list in {filename} ({v_num})")
                else:
                    for t_idx, tool in enumerate(tools):
                        t_name = tool.get("name", "")
                        if not t_name:
                            errors.append(f"Tool at idx {t_idx} missing 'name' in {filename}")
                        t_hash = tool.get("canonical_hash", "")
                        if not t_hash or not SHA256_PATTERN.match(t_hash):
                            errors.append(f"Invalid hash for tool {t_name} in {filename}")

                        # Schema properties
                        props = tool.get("property_keys", [])
                        if not isinstance(props, list):
                            errors.append(f"Properties not a list for {t_name} in {filename}")
                        reqs = tool.get("required_keys", [])
                        if not isinstance(reqs, list):
                            errors.append(f"Required keys not a list for {t_name} in {filename}")

        # 5. Dataclass roundtrip validation
        try:
            ServerPackageSpec.from_dict(data)
        except Exception as exc:
            errors.append(f"Dataclass serialization failed: {exc} in {filename}")

        return len(errors) == 0, errors

    @classmethod
    def validate_file(cls, path: str | Path) -> tuple[bool, list[str]]:
        """Read and validate a single passport JSON file."""
        file_path = Path(path)
        if not file_path.is_file():
            return False, [f"File not found: {file_path}"]
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return False, [f"Root JSON element is not a dict: {file_path}"]
            return cls.validate_passport_dict(data, filename=file_path.name)
        except json.JSONDecodeError as exc:
            return False, [f"JSON decode error in {file_path}: {exc}"]
        except Exception as exc:
            return False, [f"Read error in {file_path}: {exc}"]

    @classmethod
    def validate_directory(cls, directory: str | Path) -> tuple[int, int, list[str]]:
        """Validate all passport files in a directory.

        Returns (valid_count, invalid_count, all_errors).
        """
        dir_path = Path(directory)
        all_errors: list[str] = []
        valid_count = 0
        invalid_count = 0

        for j_file in sorted(dir_path.rglob("*.json")):
            if j_file.name in ("sync_state.json", "index.json"):
                continue
            is_valid, errors = cls.validate_file(j_file)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                all_errors.extend(errors)

        return valid_count, invalid_count, all_errors
