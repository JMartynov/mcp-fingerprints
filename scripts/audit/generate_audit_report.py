import json

def main():
    with open("data/zero_tools_audit_manifest.json", "r") as f:
        manifest = json.load(f)

    report_lines = []
    report_lines.append("# Task 61 — Deep Research and Audit of Zero-Tool Servers")
    report_lines.append("\n## Executive Summary\n")
    
    total = len(manifest)
    checked = sum(1 for x in manifest if x.get("checked"))
    tools_found = sum(1 for x in manifest if x.get("status") == "TOOLS_FOUND_MISSED_BY_PARSER")
    confirmed_zero = sum(1 for x in manifest if x.get("status", "").startswith("CONFIRMED_ZERO_TOOLS"))
    
    report_lines.append(f"- **Total Servers Audited:** {total}")
    report_lines.append(f"- **Checked Successfully:** {checked}")
    report_lines.append(f"- **Servers with Tools Found (Missed by Parser):** {tools_found}")
    report_lines.append(f"- **Confirmed Genuine Zero-Tool Servers:** {confirmed_zero}")
    
    report_lines.append("\n## Categorized Summary of Unexpected Formats\n")
    formats = {}
    remedies = {}
    for entry in manifest:
        if entry.get("status") == "TOOLS_FOUND_MISSED_BY_PARSER":
            fmt = entry.get("unexpected_format", "Unknown")
            rem = entry.get("remedy", "Unknown")
            formats[fmt] = formats.get(fmt, 0) + 1
            if fmt not in remedies:
                remedies[fmt] = rem

    for fmt, count in sorted(formats.items(), key=lambda x: x[1], reverse=True):
        report_lines.append(f"- **{fmt}**: {count} servers (Remedy: {remedies[fmt]})")
        
    report_lines.append("\n## Actionable Remedies & Roadmap for Task 62\n")
    for fmt, rem in remedies.items():
        report_lines.append(f"1. **{fmt}**: {rem}")
    
    report_lines.append("\n## Comprehensive Checklist\n")
    
    # We write max 500 lines to avoid massive file sizes, but we want a comprehensive checklist.
    # The user asked for "each checked server", but given 2900 servers, we will output all of them.
    for entry in manifest:
        repo_url = entry.get("repository_url", "No Repo")
        ecosystem = entry.get("ecosystem", "Unknown")
        name = entry.get("name", "Unknown")
        status = entry.get("status", "Unknown")
        
        report_lines.append(f"- [{'x' if entry.get('checked') else ' '}] **`{name}`** (`{ecosystem}`) — `{repo_url}`")
        report_lines.append(f"  - **Status**: `{status}`")
        if status == "TOOLS_FOUND_MISSED_BY_PARSER":
            tools = ", ".join(entry.get("tools_found", []))
            report_lines.append(f"  - **Tools Found**: `{tools}` ({entry.get('tools_found_count')} tools)")
            report_lines.append(f"  - **Location**: `{entry.get('location', 'Unknown')}`")
            report_lines.append(f"  - **Unexpected Format**: {entry.get('unexpected_format', 'Unknown')}")
            report_lines.append(f"  - **Remedy**: {entry.get('remedy', 'Unknown')}")
            
    with open("docs/reports/audit_zero_tools_deep_research.md", "w") as f:
        f.write("\n".join(report_lines) + "\n")
        
    print("Report generated successfully.")

if __name__ == "__main__":
    main()
