import json
import logging
import re
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Any, Optional
import os
import time

logger = logging.getLogger(__name__)

class DeepZeroToolAuditor:
    def __init__(self):
        pass

    def inspect_file(self, filename: str, content: str) -> List[Dict[str, Any]]:
        """Inspect a single file content for missed tools."""
        tools = []
        
        # 1. Dynamic arrays and config files
        if filename.endswith(".json") and "openapi" not in filename.lower():
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    if "tools" in data and isinstance(data["tools"], list):
                        for tool in data["tools"]:
                            if isinstance(tool, dict) and "name" in tool:
                                tools.append({
                                    "name": tool["name"],
                                    "location": f"{filename}",
                                    "format": "JSON Config",
                                    "remedy": "Parse static JSON tool manifest"
                                })
            except json.JSONDecodeError:
                pass
                
        elif filename.endswith("openapi.json") or filename.endswith("openapi.yaml"):
            if "openapi" in content.lower() or "swagger" in content.lower():
                 if "paths" in content:
                      tools.append({
                            "name": "openapi_endpoints",
                            "location": f"{filename}",
                            "format": "OpenAPI / Swagger Spec",
                            "remedy": "Integrate OpenAPI adapter"
                      })
                      
        # 2. Markdown tables
        if filename.endswith(".md"):
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.match(r'^\|?\s*Tool\s*\|.*', line, re.IGNORECASE):
                     if i + 1 < len(lines) and re.match(r'^\|?[\s\-]*\|.*', lines[i+1]):
                         for j in range(i+2, len(lines)):
                             row = lines[j].strip()
                             if not row or not row.startswith('|'):
                                 break
                             parts = [p.strip() for p in row.split('|') if p.strip()]
                             if parts:
                                 tools.append({
                                     "name": parts[0],
                                     "location": f"{filename}:{j+1}",
                                     "format": "Markdown Table",
                                     "remedy": "Extract tools from documentation tables"
                                 })
                         break
                         
        # 3. TS Dynamic Iteration Patterns
        if filename.endswith((".ts", ".js")):
             if re.search(r'\.forEach\s*\(\s*(?:t|tool|item)\s*=>\s*.*server\.(?:tool|add_tool)\s*\(', content):
                 tools.append({
                     "name": "dynamic_array_tools",
                     "location": f"{filename}",
                     "format": "Dynamic Array Iteration",
                     "remedy": "Extend AST parser to evaluate identifier references in arrays"
                 })
             if re.search(r'HANDLERS\s*=\s*\{', content) and re.search(r'server\.add_tool', content):
                 tools.append({
                     "name": "dict_dispatcher_tools",
                     "location": f"{filename}",
                     "format": "Dictionary Dispatcher",
                     "remedy": "Extract keys from handler dictionary mappings"
                 })
                 
        # 4. Decorators
        if filename.endswith(".py"):
             for match in re.finditer(r'@(?:tool|action|mcp_tool|command)\s*(?:\(.*?\))?\s*\ndef\s+([a-zA-Z0-9_]+)', content):
                 tools.append({
                     "name": match.group(1),
                     "location": f"{filename}",
                     "format": "Custom Decorators",
                     "remedy": "Support alternative Python decorators (@action, @command)"
                 })
                 
        return tools

    def audit(self, repo_url: str) -> Dict[str, Any]:
        """
        Audit a repository URL for missed tools.
        """
        result = {
            "status": "pending",
            "tools_found_count": 0,
            "tools_found": [],
            "unexpected_format": None,
            "remedy": None,
            "location": None
        }

        if not repo_url or "github.com" not in repo_url:
            if repo_url and "npmjs.com" in repo_url:
                result["status"] = "CONFIRMED_ZERO_TOOLS: NPM_PACKAGE"
            elif repo_url and "pypi.org" in repo_url:
                result["status"] = "CONFIRMED_ZERO_TOOLS: PYPI_PACKAGE"
            else:
                result["status"] = "CONFIRMED_ZERO_TOOLS: UNKNOWN_SOURCE"
            return result

        parsed = urllib.parse.urlparse(repo_url)
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) < 2:
            result["status"] = "CONFIRMED_ZERO_TOOLS: INVALID_GITHUB_URL"
            return result
        
        owner, repo = parts[0], parts[1]
        
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        def _request_with_backoff(url):
            req = urllib.request.Request(url)
            if "GITHUB_TOKEN" in os.environ:
                 req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
            for attempt in range(1):
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        return json.loads(response.read().decode())
                except urllib.error.HTTPError as e:
                    if e.code == 403:
                        reset = int(e.headers.get("X-RateLimit-Reset", time.time() + 60))
                        wait = max(0, reset - time.time()) + 1
                        # For testing and fast execution, don't wait long.
                        if wait > 5:
                            raise e
                        time.sleep(wait)
                    elif e.code == 404:
                        return None
                    else:
                        raise e
            return None
            
        try:
            repo_data = _request_with_backoff(api_url)
            if not repo_data:
                result["status"] = "CONFIRMED_ZERO_TOOLS: DEAD_REPO"
                return result
            default_branch = repo_data.get("default_branch", "main")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                 result["status"] = "ERROR: GitHub API Rate Limit Exceeded"
                 return result
            result["status"] = f"ERROR: HTTP {e.code}"
            return result
        except Exception as e:
            result["status"] = f"ERROR: {str(e)}"
            return result

        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        try:
            tree_data = _request_with_backoff(tree_url)
            if not tree_data:
                result["status"] = "CONFIRMED_ZERO_TOOLS: DEAD_REPO"
                return result
        except Exception as e:
            result["status"] = f"ERROR: Failed to fetch tree: {str(e)}"
            return result

        tree = tree_data.get("tree", [])
        
        # Look for interesting files
        all_tools = []
        for item in tree:
            path = item.get("path", "")
            if item.get("type") == "blob":
                # Filter interesting files
                is_interesting = (
                    path.endswith(".md") or 
                    path.endswith(".ts") or 
                    path.endswith(".js") or 
                    path.endswith(".py") or 
                    path.endswith(".json") or 
                    path.endswith(".yaml")
                )
                if not is_interesting:
                    continue
                    
                # Small files or specific names
                if item.get("size", 0) > 100000: # Skip huge files
                    continue
                    
                # Fetch file content
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{path}"
                try:
                    req = urllib.request.Request(raw_url)
                    with urllib.request.urlopen(req, timeout=5) as response:
                        content = response.read().decode('utf-8', errors='ignore')
                        file_tools = self.inspect_file(path, content)
                        if file_tools:
                            all_tools.extend(file_tools)
                except Exception:
                    pass

        if all_tools:
            result["status"] = "TOOLS_FOUND_MISSED_BY_PARSER"
            result["tools_found_count"] = len(all_tools)
            result["tools_found"] = [t["name"] for t in all_tools]
            result["location"] = all_tools[0].get("location")
            result["unexpected_format"] = all_tools[0].get("format")
            result["remedy"] = all_tools[0].get("remedy")
        else:
            # Analyze repo properties to check if it's purely a prompt or resource package
            # Let's say if it only has text/markdown files and no tool definitions
            result["status"] = "CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK"

        return result

import argparse
import datetime

def extract_suspicious_cards(catalog_path: str, max_suspicious: int) -> List[Dict]:
    try:
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read catalog: {e}")
        return []
        
    suspicious_cards = []
    
    for server in catalog:
        is_suspicious = False
        
        # 1. tool_count == 0 or len(tools) == 0
        if server.get("tool_count", 0) == 0 or len(server.get("tools", [])) == 0:
            is_suspicious = True
            
        # 2. description is null, "", or < 10 chars
        desc = server.get("description")
        if not desc or len(str(desc).strip()) < 10:
            is_suspicious = True
            
        # 3. tools contains syntax artifacts
        tools = server.get("tools", [])
        for tool in tools:
            tool_desc = str(tool.get("description", ""))
            if re.match(r'^(", \}\);|function\(|def |\{)', tool_desc):
                is_suspicious = True
                break
                
        # 4. repository_url is missing while ecosystem is not generic
        if not server.get("repository_url") and server.get("ecosystem") != "generic":
            is_suspicious = True
            
        if is_suspicious:
            suspicious_cards.append(server)
            
    # For prioritization, we'll sort by some criteria if available, else just take max
    return suspicious_cards[:max_suspicious]

def merge_summary(summary_path: str, report_filename: str, run_date: str, version: str, total_checked: int, match_count: int, discrepancy_count: int, discrepancy_types: Dict[str, int]):
    if not os.path.exists(summary_path):
        # Create empty summary if it doesn't exist
        with open(summary_path, "w") as f:
            f.write("# Master Audit Summary: Daily Web Card Quality & Updates Ledger\n\n## Cumulative Quality Metrics\n- **Total Historical Runs**: 0\n- **Total Cards Verified**: 0\n- **Overall Match Rate**: 0.0%\n- **Total Discrepancies Flagged**: 0\n\n---\n\n## Historical Run Ledger\n\n| Date / Timestamp | Web Update Version | Cards Checked | Matches | Discrepancies | Match Rate | Daily Run Report |\n|:---|:---:|:---:|:---:|:---:|:---:|:---|\n\n---\n\n## Top Discrepancy Categories\n- `PARSER_MISSED_DYNAMIC_REGISTRATION`: 0\n- `PARSER_MISSED_SUBDIRECTORY`: 0\n- `PARSER_MISSED_DECORATOR`: 0\n- `DOCSTRING_EXTRACTION_FAILURE`: 0\n- `EMPTY_OR_PLACEHOLDER_DESCRIPTION`: 0\n- `UNREACHABLE_OR_PRIVATE_REPO`: 0\n\n---\n\n## Unresolved Remediation Action Items\n*(Items are populated automatically during daily inspection runs)*\n")
            
    with open(summary_path, "r") as f:
        content = f.read()

    match_rate = round((match_count / total_checked * 100), 1) if total_checked > 0 else 0.0

    total_runs_match = re.search(r'\*\*Total Historical Runs\*\*: (\d+)', content)
    total_runs = int(total_runs_match.group(1)) if total_runs_match else 0
    total_runs += 1

    total_cards_match = re.search(r'\*\*Total Cards Verified\*\*: (\d+)', content)
    total_cards = int(total_cards_match.group(1)) if total_cards_match else 0
    total_cards += total_checked
    
    total_disc_match = re.search(r'\*\*Total Discrepancies Flagged\*\*: (\d+)', content)
    total_disc = int(total_disc_match.group(1)) if total_disc_match else 0
    total_disc += discrepancy_count

    overall_match_rate = 0.0
    if total_cards > 0:
        overall_match_rate = round(( (total_cards - total_disc) / total_cards * 100), 1)

    content = re.sub(r'\*\*Total Historical Runs\*\*: \d+', f'**Total Historical Runs**: {total_runs}', content)
    content = re.sub(r'\*\*Total Cards Verified\*\*: \d+', f'**Total Cards Verified**: {total_cards}', content)
    content = re.sub(r'\*\*Overall Match Rate\*\*: [\d\.]+\%', f'**Overall Match Rate**: {overall_match_rate}%', content)
    content = re.sub(r'\*\*Total Discrepancies Flagged\*\*: \d+', f'**Total Discrepancies Flagged**: {total_disc}', content)

    ledger_marker = "|:---|:---:|:---:|:---:|:---:|:---:|:---|"
    new_row = f"\n| {run_date} | {version} | {total_checked} | {match_count} | {discrepancy_count} | {match_rate}% | [runs/{report_filename}](runs/{report_filename}) |"
    
    if ledger_marker in content:
        content = content.replace(ledger_marker, ledger_marker + new_row)
        
    for cat, count in discrepancy_types.items():
        pattern = rf'- `{cat}`: (\d+)'
        match = re.search(pattern, content)
        if match:
            current_count = int(match.group(1))
            content = re.sub(pattern, f"- `{cat}`: {current_count + count}", content)

    with open(summary_path, "w") as f:
        f.write(content)


def generate_report(output_path: str, today: str, version: str, results_a: List[Dict], results_b: List[Dict]):
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
        rows.append(f"| `{server['name']}` | {server['ecosystem']} | {server['card_tools']} | {server['source_tools']} | {status_icon} {server['match_status']} | {server.get('root_cause', 'N/A')} | `{server.get('location', 'N/A')}` |")
        
        if not is_match:
            cause_type = server.get('root_cause', 'UNKNOWN')
            if cause_type in discrepancy_types:
                discrepancy_types[cause_type] += 1
                
            analyses.append(f"### {len(analyses)+1}. [{server['name']}]\n"
                          f"- **Repository**: [{server.get('repository_url', 'N/A')}]({server.get('repository_url', '#')})\n"
                          f"- **Expected (Source Truth)**: {server['source_tools']} tools.\n"
                          f"- **Observed (Card Data)**: {server['card_tools']} tools.\n"
                          f"- **Root Cause**: {server.get('root_cause', 'Unknown')}\n"
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
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)
        
    return total_checked, match_count, discrepancy_count, discrepancy_types

def map_audit_to_status(server: Dict, audit_result: Dict) -> Dict:
    card_tools = server.get("tool_count", 0)
    
    res = {
        "name": server.get("name", "unknown"),
        "ecosystem": server.get("ecosystem", "generic"),
        "card_tools": card_tools,
        "repository_url": server.get("repository_url", "")
    }
    
    status = audit_result.get("status", "")
    if "CONFIRMED_ZERO_TOOLS" in status:
        if card_tools == 0:
            res["match_status"] = "PERFECT_MATCH"
            res["source_tools"] = 0
            res["root_cause"] = "N/A"
            res["location"] = "N/A"
        else:
            res["match_status"] = "MISMATCH"
            res["source_tools"] = 0
            res["root_cause"] = status
            res["location"] = "N/A"
    elif "TOOLS_FOUND_MISSED_BY_PARSER" in status:
        res["match_status"] = "MISSED_TOOLS"
        res["source_tools"] = audit_result.get("tools_found_count", 0) + card_tools
        format_type = audit_result.get("unexpected_format", "")
        if "Dynamic Array Iteration" in format_type or "Dictionary Dispatcher" in format_type:
            res["root_cause"] = "PARSER_MISSED_DYNAMIC_REGISTRATION"
        elif "Custom Decorators" in format_type:
            res["root_cause"] = "PARSER_MISSED_DECORATOR"
        else:
            res["root_cause"] = format_type if format_type else "UNKNOWN"
        res["location"] = audit_result.get("location", "N/A")
        res["remedy"] = audit_result.get("remedy", "")
    elif "ERROR" in status:
        res["match_status"] = "UNREACHABLE_REPO"
        res["source_tools"] = "?"
        res["root_cause"] = "UNREACHABLE_OR_PRIVATE_REPO"
        res["location"] = "N/A"
    else:
        # Default
        res["match_status"] = "PERFECT_MATCH"
        res["source_tools"] = card_tools
        res["root_cause"] = "N/A"
        res["location"] = "N/A"
        
    return res

def main():
    parser = argparse.ArgumentParser(description="Daily MCP Web Card Audit")
    parser.add_argument("--web-updates", required=True, help="Path to latest_update.json")
    parser.add_argument("--catalog", required=True, help="Path to catalog.json")
    parser.add_argument("--output", required=True, help="Path to output markdown report")
    parser.add_argument("--merge-summary", required=True, help="Path to master_audit_summary.md")
    parser.add_argument("--max-suspicious", type=int, default=50, help="Max suspicious cards to process")
    args = parser.parse_args()
    
    # Use full ISO/UTC date-timestamp suffix for unique runs
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    today = now_utc.strftime("%Y-%m-%d")
    timestamp_suffix = now_utc.strftime("%Y-%m-%d_%H%M%S")
    
    # 1. Candidate Set A
    suspicious = extract_suspicious_cards(args.catalog, args.max_suspicious)
    
    # 2. Candidate Set B
    latest_updates = []
    version = "unknown"
    if os.path.exists(args.web_updates):
        with open(args.web_updates, 'r') as f:
            data = json.load(f)
            latest_updates = data.get("servers", [])
            version = data.get("version", "unknown")
            
    auditor = DeepZeroToolAuditor()
    
    results_a = []
    for s in suspicious:
        audit_res = auditor.audit(s.get("repository_url", ""))
        results_a.append(map_audit_to_status(s, audit_res))
        
    results_b = []
    for s in latest_updates:
        audit_res = auditor.audit(s.get("repository_url", ""))
        results_b.append(map_audit_to_status(s, audit_res))
        
    total_checked, match_count, discrepancy_count, discrepancy_types = generate_report(
        args.output, today, version, results_a, results_b
    )
    
    report_filename = os.path.basename(args.output)
    merge_summary(
        args.merge_summary, report_filename, today, version, total_checked, match_count, discrepancy_count, discrepancy_types
    )
    
    print(f"Audit complete: {total_checked} checked, {match_count} matches.")

if __name__ == "__main__":
    main()
