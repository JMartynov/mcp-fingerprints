# Task 46: Attribution Enrichment & Multi-Format Reporting

### 1. Architectural Context & Technical Objective
Currently, `ProbeReport` and `FingerprintMatchResult` only report raw package names, matched versions, and confidence scores. When a developer or auditor identifies an MCP server, their next questions are:
1. *Where can I download and install this?*
2. *Where is the source repository / documentation?*
3. *Who maintains it, and what license does it use?*
4. *Is the matched version the latest release, or is it outdated?*

The objective of Task 46 is to:
1. Enrich `ProbeReport` with actionable metadata from `ServerPackageSpec` (repository URLs, official download/install commands, maintainers, latest registry versions).
2. Implement flexible output formatting across CLI commands:
   - `--format short` (or `-s`): Concise 1-3 line summary (ideal for CI/CD logs and status bars).
   - `--format long` (or `-l`): Exhaustive audit report with tool parameter schemas, descriptions, and canonical hashes.
   - `--format table`: Formatted ASCII/Markdown table.
   - `--format json`: Structured JSON output.

---

### 2. Concrete Real-World Problem & Workflow (Practitioner Scenario)

* **The Practitioner**: Terminal power user, CI/CD pipeline author, or developer evaluating new tools.
* **The Problem**: 
  - A developer runs an unknown or shared MCP command from a tutorial. The existing tool says `Identified: @modelcontextprotocol/server-sqlite`. But the developer doesn't know where the official repository is, how to install it permanently in their own client, or whether it's up to date.
  - In CI/CD pipelines, long multiline outputs pollute the logs; authors need a concise one-line status string like: `✔ Verified: @modelcontextprotocol/server-postgres v0.6.2 (100% match)`.
* **What the Utility Finds**:
  - Connects the match back to the rich `ServerPackageSpec` in the passport knowledge base.
  - Automatically generates the canonical download/install instructions (e.g. `npx -y @modelcontextprotocol/server-sqlite` or `pip install mcp-server-sqlite`).
  - Identifies latest available version versus observed version.
* **How It Solves the Problem**:
  - Delivers immediate actionable context without requiring manual web searches.
  - Adapts its output format cleanly to the user's environment (interactive terminal, CI pipeline, or automated script).

---

### 3. Technical Implementation Specifications

1. **Enrich `ProbeReport` and `FingerprintMatchResult` (`src/mcp_fingerprints/models.py` & `src/mcp_fingerprints/prober.py`)**:
   - Add fields to `ProbeReport`:
     - `repository_url: str | None`
     - `homepage_url: str | None`
     - `install_command: str | None` (computed from ecosystem and package name)
     - `author: str | None`
     - `latest_version: str | None`
     - `is_outdated: bool`
2. **Implement Formatting Engine (`src/mcp_fingerprints/reporter.py`)**:
   - `format_probe_report(report: ProbeReport, format_type: str = "long") -> str`:
     - `format_type="short"`:
       ```text
       ✔ Identified: @modelcontextprotocol/server-sqlite v0.6.2 (npm)
         Repository: https://github.com/modelcontextprotocol/servers
         Download:   npx -y @modelcontextprotocol/server-sqlite
         Tools (4):  read_query, write_query, create_table, list_tables
       ```
     - `format_type="long"`:
       Includes full capability breakdowns, canonical hashes, parameter schemas, and protocol annotations.
     - `format_type="table"`:
       Tabular overview of observed tools, parameters, and protocol hints.
     - `format_type="json"`:
       Full machine-readable JSON dictionary (`report.to_dict()`).
3. **Update CLI (`src/mcp_fingerprints/cli.py`)**:
   - Add `--format [short|long|table|json]` (with `-s` / `-l` shortcuts) to `probe` and other inspection commands.

---

### 4. Concrete Usage Examples

#### CLI Usage
```bash
# Short 3-line summary (ideal for quick checks and CI logs)
mcp-fingerprints probe --format short -- npx -y @modelcontextprotocol/server-memory

# Long comprehensive audit report
mcp-fingerprints probe --format long -- npx -y @modelcontextprotocol/server-memory

# Table view of tools and parameters
mcp-fingerprints probe --format table -- npx -y @modelcontextprotocol/server-memory
```

#### Sample Short Output
```text
✔ Identified: @modelcontextprotocol/server-memory v0.6.2 (npm, 100% confidence)
  Repository: https://github.com/modelcontextprotocol/servers
  Download:   npx -y @modelcontextprotocol/server-memory
  Tools (5):  create_entities, create_relations, read_graph, search_nodes, open_nodes
```

---

### 5. README Documentation Plan

Add the following section to `README.md`:

```markdown
## Reporting & Output Formats

Customize the output verbosity to fit your terminal or CI environment:

\`\`\`bash
# Concise 3-line summary for quick checks and CI logs
mcp-fingerprints probe --format short -- npx -y @modelcontextprotocol/server-sqlite --db app.db

# Exhaustive schema and parameter audit report
mcp-fingerprints probe --format long -- npx -y @modelcontextprotocol/server-sqlite --db app.db

# Structured JSON output for scripting and automation
mcp-fingerprints probe --json -- npx -y @modelcontextprotocol/server-sqlite --db app.db
\`\`\`
```

---

### 6. Clear Acceptance Criteria & Test Plan

- [ ] `ProbeReport` accurately populates `repository_url`, `install_command`, and `latest_version` from the passport spec.
- [ ] `--format short` outputs a clean, non-bloated 3-line terminal summary.
- [ ] `--format long` provides detailed tool schemas, protocol hints, and hash signatures.
- [ ] `--format table` formats clean ASCII tables of capabilities.
- [ ] Unit tests in `tests/test_reporter.py` verify all formatters without ANSI escape corruptions.
