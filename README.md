# MCP Fingerprints & Passport Knowledge Base

[![Daily MCP Fingerprint & Passport Sync](https://github.com/JMartynov/mcp-fingerprints/actions/workflows/daily_sync.yml/badge.svg)](https://github.com/JMartynov/mcp-fingerprints/actions/workflows/daily_sync.yml)
[![Passports Count](https://img.shields.io/badge/passports-3%2C900%2B-blue.svg)](data/fingerprints)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An open-source, automated database and knowledge base of **Model Context Protocol (MCP)** server passports, version signatures, and tool contract fingerprints.

## Key Features
- **3,900+ Indexed Passports**: Cross-indexed across Smithery, npm, and PyPI registries.
- **Automated Daily Sync**: Continuously crawls, extracts tool signatures, canonicalizes hash fingerprints, and tracks historical schema drift.
- **Consolidated Snapshot**: Pre-compiled `passports.json.gz` for rapid HTTP consumption (< 50ms startup time).

## Fast Consumption

You can fetch the latest consolidated database in a single GET request:
```bash
curl -sL https://raw.githubusercontent.com/JMartynov/mcp-fingerprints/main/passports.json.gz | gzip -d > passports.json
```

### Python
```python
import gzip, json, urllib.request

url = "https://raw.githubusercontent.com/JMartynov/mcp-fingerprints/main/passports.json.gz"
with urllib.request.urlopen(url) as resp:
    with gzip.GzipFile(fileobj=resp) as gz:
        data = json.load(gz)

print(f"Loaded {data['total_passports']} MCP server passports.")
```

## CLI Usage
```bash
# Sync from registries
python -m mcp_fingerprints.cli sync --all

# Validate schema invariants
python -m mcp_fingerprints.cli validate --dir data/fingerprints

# Build compressed snapshot
python -m mcp_fingerprints.cli snapshot
```

## License
MIT
