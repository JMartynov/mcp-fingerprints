"""Search module for discovering MCP servers by keyword or capability."""

import json
from pathlib import Path
from typing import Any


def search_passports(fingerprints_dir: Path | str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Search passports for a query, scoring and ranking the results.
    
    Scores:
      - Exact tool name match: +10
      - Substring tool name match: +5
      - Package name match: +4
      - Keyword match: +3
      - Description match: +1
    """
    dir_path = Path(fingerprints_dir)
    query_lower = query.lower()
    
    skip_files = {"sync_state.json", "index.json", ".passport_index.pickle"}
    
    scored_results = []
    
    for file_path in dir_path.glob("**/*.json"):
        if file_path.name in skip_files:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                passport = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
            
        if not isinstance(passport, dict) or "package_name" not in passport:
            continue
            
        score = 0
        matched_tools = []
        
        # Package name match
        package_name = passport.get("package_name", "")
        if query_lower in package_name.lower():
            score += 4
            
        # Description match (top-level)
        description = passport.get("description", "")
        if description and query_lower in description.lower():
            score += 1
            
        # Keyword match
        keywords = passport.get("keywords", [])
        for keyword in keywords:
            if isinstance(keyword, str) and query_lower in keyword.lower():
                score += 3
                
        # Search through tools in the latest version
        versions = passport.get("versions", [])
        if versions:
            # Check the latest version (assuming the first or last, let's just check all tools in the latest version or all versions)
            # We'll check the most recent version, which is typically the first or we can scan all versions
            # Let's check all tools across all versions but keep a set of matched tools to avoid duplicates
            seen_tools = set()
            for version in versions:
                tools = version.get("tool_signatures", [])
                for tool in tools:
                    tool_name = tool.get("name", "")
                    tool_desc = tool.get("description", "")
                    
                    if not tool_name or tool_name in seen_tools:
                        continue
                        
                    tool_name_lower = tool_name.lower()
                    
                    is_match = False
                    if query_lower == tool_name_lower:
                        score += 10
                        is_match = True
                    elif query_lower in tool_name_lower:
                        score += 5
                        is_match = True
                        
                    if tool_desc and query_lower in tool_desc.lower():
                        score += 1
                        is_match = True
                        
                    if is_match:
                        matched_tools.append(tool_name)
                        seen_tools.add(tool_name)
                        
        if score > 0:
            scored_results.append({
                "package_name": package_name,
                "score": score,
                "matched_tools": matched_tools,
                "ecosystem": passport.get("ecosystem", "unknown"),
                "description": description
            })
            
    # Sort by score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_results[:limit]


def format_search_results(results: list[dict[str, Any]]) -> str:
    """Format search results into a clean markdown table."""
    if not results:
        return "No results found."
        
    headers = ["Package Name", "Ecosystem", "Score", "Matched Tools", "Description"]
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for result in results:
        col_widths[0] = max(col_widths[0], len(str(result.get("package_name", ""))))
        col_widths[1] = max(col_widths[1], len(str(result.get("ecosystem", ""))))
        col_widths[2] = max(col_widths[2], len(str(result.get("score", ""))))
        tools_str = ", ".join(result.get("matched_tools", []))
        if len(tools_str) > 30:
            tools_str = tools_str[:27] + "..."
        col_widths[3] = max(col_widths[3], len(tools_str))
        
        desc = str(result.get("description", "")).replace("\n", " ")
        if len(desc) > 40:
            desc = desc[:37] + "..."
        col_widths[4] = max(col_widths[4], len(desc))
        
    # Format rows
    def format_row(row_data: list[str]) -> str:
        return "| " + " | ".join(str(d).ljust(w) for d, w in zip(row_data, col_widths)) + " |"
        
    lines = []
    lines.append(format_row(headers))
    lines.append("|-" + "-|-".join("-" * w for w in col_widths) + "-|")
    
    for result in results:
        tools_str = ", ".join(result.get("matched_tools", []))
        if len(tools_str) > 30:
            tools_str = tools_str[:27] + "..."
            
        desc = str(result.get("description", "") or "").replace("\n", " ")
        if len(desc) > 40:
            desc = desc[:37] + "..."
            
        row = [
            str(result.get("package_name", "")),
            str(result.get("ecosystem", "")),
            str(result.get("score", "")),
            tools_str,
            desc
        ]
        lines.append(format_row(row))
        
    return "\n".join(lines)
