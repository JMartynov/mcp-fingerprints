import json
import collections

with open("docs/research/master_mcp_ecosystem_audit_1000.json", "r") as f:
    data = json.load(f)

total_count = len(data)
present_count = sum(1 for x in data if x.get("in_repo"))
missing_count = total_count - present_count

group_stats = collections.defaultdict(lambda: {"total": 0, "present": 0, "missing": 0})
issue_stats = collections.defaultdict(int)

for item in data:
    group = item["group"]
    group_stats[group]["total"] += 1
    if item.get("in_repo"):
        group_stats[group]["present"] += 1
    else:
        group_stats[group]["missing"] += 1
        issue_type = item.get("issue_type")
        if issue_type:
            issue_stats[issue_type] += 1

report_lines = []
report_lines.append("# Master Empirical Research Audit & Remediation Roadmap")
report_lines.append("")
report_lines.append("## 1. Executive Summary")
report_lines.append("")
report_lines.append(f"- **Total candidates audited:** {total_count}")
report_lines.append(f"- **Global Coverage Ratio:** Present: {present_count} ({(present_count/total_count)*100:.1f}%), Missing: {missing_count} ({(missing_count/total_count)*100:.1f}%)")
report_lines.append("")
report_lines.append("### Group-by-group comparative matrix")
report_lines.append("| Group | Total | Present | Missing | Present % |")
report_lines.append("|-------|-------|---------|---------|-----------|")
for group, stats in group_stats.items():
    total = stats['total']
    present = stats['present']
    missing = stats['missing']
    pct = (present/total*100) if total else 0
    report_lines.append(f"| {group} | {total} | {present} | {missing} | {pct:.1f}% |")

report_lines.append("")
report_lines.append("## 2. Systemic Root-Cause Taxonomy & Failure Analysis")
report_lines.append("")
report_lines.append("### Issue Types Breakdown")
report_lines.append("| Issue Type | Count | Percentage | Severity |")
report_lines.append("|------------|-------|------------|----------|")
for issue, count in sorted(issue_stats.items(), key=lambda x: x[1], reverse=True):
    pct = (count/missing_count*100) if missing_count else 0
    severity = "High" if count > 50 else ("Medium" if count > 10 else "Low")
    report_lines.append(f"| {issue} | {count} | {pct:.1f}% | {severity} |")

report_lines.append("")
report_lines.append("### Deep Dive into Failure Modes")
report_lines.append("""
The failure modes observed highlight critical gaps in the current AST and crawling pipelines:
- **`rmcp` Rust macros & Custom SDKs**: The current crawler focuses strictly on standard AST parsing of functions but fails to recognize or evaluate declarative macros used by libraries like `rmcp` in Rust.
- **`mark3labs/mcp-go`**: Go code utilizing `mcp-go` SDK constructs tools using custom builder patterns that the current standard AST parsing does not explicitly track.
- **Spring AI `@Tool`**: In JVM/Java ecosystems, annotations drive runtime behavior. The static analysis is missing support for parsing and evaluating Spring AI annotations like `@Tool`.
- **PEP 723 `# /// script` headers**: Python scripts utilizing the emerging PEP 723 specification embed dependencies in comment blocks, which aren't typically evaluated by older AST parsing methods looking primarily at `requirements.txt` or `pyproject.toml`.
- **Registry Indexer Misses**: Many tools are published on custom indices or miss conventional tagging.
""")

report_lines.append("")
report_lines.append("## 3. Comprehensive Master Audit Catalog Table")
report_lines.append("")
report_lines.append("| MCP Name | Group | Location | Status | Issue Type | Specific Technical Remedy |")
report_lines.append("|---|---|---|---|---|---|")

for item in data:
    name = item.get("name", "")
    group = item.get("group", "")
    location = item.get("location", "")
    status = "Present" if item.get("in_repo") else "Missing"
    issue_type = item.get("issue_type", "") or ""
    remedy = item.get("remedy", "") or ""
    report_lines.append(f"| {name} | {group} | {location} | {status} | {issue_type} | {remedy} |")

report_lines.append("")
report_lines.append("## 4. Architectural Remediation Roadmap")
report_lines.append("")
report_lines.append("""
1. **Update `synchronizer.py`:**
   - Integrate custom logic to parse PEP 723 script blocks for inline dependencies.
   - Expand registry endpoints to include Go packages (`pkg.go.dev` custom scraping) and Crates.io with fallback to GitHub releases.

2. **Update `ast_parser.py`:**
   - Add a tree-sitter or regex-based macro evaluator for Rust code (e.g. `rmcp` macros).
   - Incorporate Java annotation scanning for JVM languages, extracting `@Tool` details from Spring AI.
   - Recognize Go custom builder patterns by tracking references to `mark3labs/mcp-go`.

3. **Crawler Modules:**
   - Extend GitHub search scopes to include `Dockerfile` labels referencing MCP and Monorepo custom path discovery.

4. **Curated Seed Lists:**
   - Seed crawler with standard "Awesome-MCP" repositories, international mirrors, and enterprise registries.
""")

with open("docs/research/master_mcp_ecosystem_audit_report.md", "w") as f:
    f.write("\n".join(report_lines))

