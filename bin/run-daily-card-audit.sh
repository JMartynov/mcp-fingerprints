#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%d_%H%M%S")
echo "=== Starting Daily MCP Web Card Audit for ${TIMESTAMP} ==="
mkdir -p docs/reports/daily_web_audits/runs

if [ ! -f web/catalog.json ]; then
  echo "web/catalog.json missing; generating web catalog..."
  PYTHONPATH=src uv run python3 scripts/generate_web_catalog.py
fi

PYTHONPATH=src uv run python3 -m mcp_fingerprints.deep_zero_tool_auditor \
  --web-updates web/updates/latest_update.json \
  --catalog web/catalog.json \
  --output "docs/reports/daily_web_audits/runs/${TIMESTAMP}.md" \
  --merge-summary "docs/reports/daily_web_audits/master_audit_summary.md" \
  --max-suspicious 50

echo "=== Audit complete: docs/reports/daily_web_audits/runs/${TIMESTAMP}.md ==="
