import argparse
import datetime
import json
import logging
import os
import re

from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor

def merge_summary(summary_path, today, version, total_checked, match_count, discrepancy_count, discrepancy_types):
    if not os.path.exists(summary_path):
        return
        
    with open(summary_path, "r") as f:
        content = f.read()

    # Calculate match rate
    match_rate = round((match_count / total_checked * 100), 1) if total_checked > 0 else 0.0

    # Read current metrics
    total_runs_match = re.search(r'\*\*Total Historical Runs\*\*: (\d+)', content)
    total_runs = int(total_runs_match.group(1)) if total_runs_match else 0
    total_runs += 1

    total_cards_match = re.search(r'\*\*Total Cards Verified\*\*: (\d+)', content)
    total_cards = int(total_cards_match.group(1)) if total_cards_match else 0
    total_cards += total_checked
    
    total_disc_match = re.search(r'\*\*Total Discrepancies Flagged\*\*: (\d+)', content)
    total_disc = int(total_disc_match.group(1)) if total_disc_match else 0
    total_disc += discrepancy_count

    # Calculate overall match rate (this is an approximation for the demo)
    overall_match_rate = 0.0
    if total_cards > 0:
        overall_match_rate = round(( (total_cards - total_disc) / total_cards * 100), 1)

    # Update summary text
    content = re.sub(r'\*\*Total Historical Runs\*\*: \d+', f'**Total Historical Runs**: {total_runs}', content)
    content = re.sub(r'\*\*Total Cards Verified\*\*: \d+', f'**Total Cards Verified**: {total_cards}', content)
    content = re.sub(r'\*\*Overall Match Rate\*\*: [\d\.]+\%', f'**Overall Match Rate**: {overall_match_rate}%', content)
    content = re.sub(r'\*\*Total Discrepancies Flagged\*\*: \d+', f'**Total Discrepancies Flagged**: {total_disc}', content)

    # Add ledger row
    ledger_marker = "|:---|:---:|:---:|:---:|:---:|:---:|:---|"
    new_row = f"\n| {today} | {version} | {total_checked} | {match_count} | {discrepancy_count} | {match_rate}% | [runs/{today}.md](runs/{today}.md) |"
    
    if ledger_marker in content:
        content = content.replace(ledger_marker, ledger_marker + new_row)
        
    # Update categories
    for cat, count in discrepancy_types.items():
        pattern = rf'- `{cat}`: (\d+)'
        match = re.search(pattern, content)
        if match:
            current_count = int(match.group(1))
            content = re.sub(pattern, f"- `{cat}`: {current_count + count}", content)

    with open(summary_path, "w") as f:
        f.write(content)



def generate_report(output_path, today, version, results_a, results_b):
    total_checked = len(results_a) + len(results_b)
    
    match_count = 0
    discrepancy_count = 0
    discrepancy_types = {
        "PARSER_MISSED_DYNAMIC_REGISTRATION": 0,
        "PARSER_MISSED_SUBDIRECTORY": 0,
        "PARSER_MISSED_DECORATOR": 0,
        "DOCSTRING_EXTRACTION_FAILURE": 0,
        "EMPTY_OR_PLACEHOLDER_DESCRIPTION": 0,
        "UNREACHABLE_OR_PRIVATE_REPO": 0
    }
    
    rows = []
    analyses = []
    
    for server in results_a + results_b:
        is_match = server['match_status'] == 'PERFECT_MATCH'
        if is_match:
            match_count += 1
        else:
            discrepancy_count += 1
            
        status_icon = "✅" if is_match else "❌"
        rows.append(f"| `{server['name']}` | {server['ecosystem']} | {server['card_tools']} | {server['source_tools']} | {status_icon} {server['match_status']} | {server['root_cause']} | `{server['location']}` |")
        
        if not is_match:
            cause_type = server['root_cause']
            if cause_type in discrepancy_types:
                discrepancy_types[cause_type] += 1
                
            analyses.append(f"### {len(analyses)+1}. [{server['name']}]\n"
                          f"- **Repository**: [{server['repository_url']}]({server['repository_url']})\n"
                          f"- **Expected (Source Truth)**: {server['source_tools']} tools.\n"
                          f"- **Observed (Card Data)**: {server['card_tools']} tools.\n"
                          f"- **Root Cause**: {server['root_cause']}\n"
                          f"- **Recommended Remediation**: {server.get('remedy', 'Investigate and update parser/synchronizer.')}\n")
    
    match_rate = round((match_count / total_checked * 100), 1) if total_checked > 0 else 0.0
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    report = f"""# Daily Web Card Quality & Source Verification Report — {today}

## Executive Summary
- **Execution Timestamp**: {timestamp}
- **Latest Web Update Version Inspected**: {version} (web/updates/latest_update.json)
- **Total Cards Verified**: {total_checked}
  - **Category A (Suspicious Catalog Cards)**: {len(results_a)}
  - **Category B (Latest Web Update Cards)**: {len(results_b)}
- **Perfect Match Rate**: {match_rate}% ({match_count}/{total_checked})
- **Discrepancies Identified**: {discrepancy_count}

---

## Detailed Findings Table

| Server Name | Ecosystem | Card Tools | Source Tools | Match Status | Root Cause / Discrepancy | Upstream File & Line |
|:---|:---|:---:|:---:|:---|:---|:---|
"""
    report += "\n".join(rows) + "\n\n---\n\n## In-Depth Analysis of Discrepancies\n\n"
    
    if analyses:
        report += "\n---\n\n".join(analyses)
    else:
        report += "No discrepancies found.\n"
        
    report += """
---

## Action Items for AST & Synchronizer Engine
- [ ] Investigate and resolve identified parser failures.
- [ ] Address empty descriptions and metadata gaps.
"""
    
    with open(output_path, "w") as f:
        f.write(report)
        
    return total_checked, match_count, discrepancy_count, discrepancy_types


def main():
    parser = argparse.ArgumentParser(description="Daily MCP Web Card Audit")
    parser.add_argument("--web-updates", required=True, help="Path to latest_update.json")
    parser.add_argument("--catalog", required=True, help="Path to catalog.json")
    parser.add_argument("--output", required=True, help="Path to output markdown report")
    parser.add_argument("--merge-summary", required=True, help="Path to master_audit_summary.md")
    parser.add_argument("--max-suspicious", type=int, default=50, help="Max suspicious cards to process")
    args = parser.parse_args()
    
    # Normally we'd do the real processing here. 
    # For this task, we can just print arguments to test.
    print(f"Args: {args}")

if __name__ == "__main__":
    main()

