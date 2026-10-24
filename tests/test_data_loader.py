"""Tests for multi-tier data loader and snapshot resolution."""

import gzip
import json
from pathlib import Path
import pytest
from mcp_fingerprints.data_loader import get_passports_path, load_passports
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints import McpIdentifier


def test_get_passports_path_local():
    path = get_passports_path(download_if_missing=False)
    assert path.exists()
    assert path.name.endswith(".gz") or path.is_dir()


def test_load_passports_local():
    passports = load_passports(download_if_missing=False)
    assert len(passports) > 100
    sample_key = next(iter(passports))
    assert hasattr(passports[sample_key], "package_name")
    assert hasattr(passports[sample_key], "versions")


def test_fingerprint_matcher_load_default():
    matcher = FingerprintMatcher()
    count = matcher.load_default(download_if_missing=False)
    assert count > 100
    assert matcher.total_packages > 100


def test_mcp_identifier_default_init():
    identifier = McpIdentifier()
    assert identifier.matcher.total_packages > 100
