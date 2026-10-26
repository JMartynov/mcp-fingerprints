#!/usr/bin/env bash
set -euo pipefail

TODAY=$(date -u +%F)
echo "=== Starting Daily MCP Web Card Audit for ${TODAY} ==="
mkdir -p docs/reports/daily_web_audits/runs

PYTHONPATH=src python3 -m mcp_fingerprints.deep_zero_tool_auditor \
  --web-updates web/updates/latest_update.json \
  --catalog web/catalog.json \
  --output "docs/reports/daily_web_audits/runs/${TODAY}.md" \
  --merge-summary "docs/reports/daily_web_audits/master_audit_summary.md" \
  --max-suspicious 50

echo "=== Audit complete: docs/reports/daily_web_audits/runs/${TODAY}.md ==="
