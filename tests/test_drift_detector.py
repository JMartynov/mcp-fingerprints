"""Unit tests for the Supply-Chain Drift and Tamper Detector."""

import json
from unittest.mock import patch, MagicMock
from mcp_fingerprints.drift_detector import (
    compare_passports_for_drift,
    format_drift_report,
    dispatch_drift_webhook,
)


def test_compare_clean_passports():
    old = {
        "server-a": {
            "package_name": "server-a",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:hash_1",
                    "tool_signatures": [{"name": "tool1"}],
                }
            ],
        }
    }
    new = {
        "server-a": {
            "package_name": "server-a",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:hash_1",
                    "tool_signatures": [{"name": "tool1"}],
                }
            ],
        }
    }
    report = compare_passports_for_drift(old, new)
    assert report.is_clean is True
    assert report.has_tamper_incidents is False
    assert report.packages_compared == 1
    assert report.unaltered_packages == 1
    assert len(report.incidents) == 0

    text_rep = format_drift_report(report)
    assert "CLEAN" in text_rep


def test_hash_tamper_detection():
    old = {
        "server-tampered": {
            "package_name": "server-tampered",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:original_hash",
                    "tool_signatures": [{"name": "tool1"}],
                }
            ],
        }
    }
    new = {
        "server-tampered": {
            "package_name": "server-tampered",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:modified_hash_tampered",
                    "tool_signatures": [{"name": "tool1"}],
                }
            ],
        }
    }
    report = compare_passports_for_drift(old, new)
    assert report.is_clean is False
    assert report.has_tamper_incidents is True
    assert len(report.incidents) == 1

    inc = report.incidents[0]
    assert inc.incident_type == "hash_tamper"
    assert inc.severity == "critical"
    assert inc.old_hash == "sha256:original_hash"
    assert inc.new_hash == "sha256:modified_hash_tampered"

    text_rep = format_drift_report(report)
    assert "CRITICAL TAMPER DETECTED" in text_rep


def test_silent_tool_addition_and_removal():
    old = {
        "server-mutated": {
            "package_name": "server-mutated",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:h1",
                    "tool_signatures": [{"name": "safe_tool"}],
                }
            ],
        }
    }
    new = {
        "server-mutated": {
            "package_name": "server-mutated",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:h2",
                    "tool_signatures": [
                        {"name": "safe_tool"},
                        {"name": "injected_backdoor_tool"},
                    ],
                }
            ],
        }
    }
    report = compare_passports_for_drift(old, new)
    assert report.is_clean is False
    assert report.has_tamper_incidents is True

    add_inc = next(i for i in report.incidents if i.incident_type == "tool_added")
    assert add_inc.severity == "high"
    assert "injected_backdoor_tool" in add_inc.affected_tools


def test_new_vulnerability_advisory_attached():
    old = {
        "server-vuln": {
            "package_name": "server-vuln",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:h1",
                    "vulnerability_advisories": [],
                }
            ],
        }
    }
    new = {
        "server-vuln": {
            "package_name": "server-vuln",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:h1",
                    "vulnerability_advisories": [
                        {
                            "id": "GHSA-xxxx-yyyy-zzzz",
                            "severity": "CRITICAL",
                            "summary": "Remote Code Execution via MCP input",
                        }
                    ],
                }
            ],
        }
    }
    report = compare_passports_for_drift(old, new)
    assert report.is_clean is False
    assert len(report.incidents) == 1
    inc = report.incidents[0]
    assert inc.incident_type == "new_vulnerability"
    assert inc.severity == "high"
    assert "GHSA-xxxx-yyyy-zzzz" in inc.details


def test_benign_version_bump():
    old = {
        "server-bump": {
            "package_name": "server-bump",
            "versions": [
                {
                    "version": "1.0.0",
                    "toolset_canonical_hash": "sha256:v1_hash",
                }
            ],
        }
    }
    new = {
        "server-bump": {
            "package_name": "server-bump",
            "versions": [
                {
                    "version": "2.0.0",
                    "toolset_canonical_hash": "sha256:v2_hash",
                }
            ],
        }
    }
    report = compare_passports_for_drift(old, new)
    assert report.is_clean is True
    assert report.version_bumps == 1
    assert len(report.incidents) == 0


@patch("urllib.request.urlopen")
def test_dispatch_drift_webhook(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    old = {
        "server-t": {
            "package_name": "server-t",
            "versions": [{"version": "1.0.0", "toolset_canonical_hash": "sha256:old"}],
        }
    }
    new = {
        "server-t": {
            "package_name": "server-t",
            "versions": [{"version": "1.0.0", "toolset_canonical_hash": "sha256:new"}],
        }
    }
    report = compare_passports_for_drift(old, new)
    success = dispatch_drift_webhook(report, webhook_url="https://hooks.slack.com/services/test")
    assert success is True
    assert mock_urlopen.called

    # Test without webhook URL configured returns False
    assert dispatch_drift_webhook(report, webhook_url=None) is False
