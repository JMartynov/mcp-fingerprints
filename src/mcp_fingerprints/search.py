"""Search module for discovering MCP servers by keyword or capability."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

_SKIP_FILES = {"sync_state.json", "index.json", ".passport_index.pickle"}
_DIR_CACHE: dict[tuple[str, int, int], list[dict[str, Any]]] = {}


def _load_passports_cached(dir_path: Path) -> list[dict[str, Any]]:
    """Load passport dicts from a directory or .json.gz snapshot, caching by mtime."""
    if dir_path.is_file() and dir_path.name.endswith(".json.gz"):
        with gzip.open(dir_path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("passports", [])
        items = raw.values() if isinstance(raw, dict) else raw
        return [p for p in items if isinstance(p, dict) and "package_name" in p]

    json_files = [p for p in dir_path.glob("**/*.json") if p.name not in _SKIP_FILES]
    max_mtime = max((p.stat().st_mtime_ns for p in json_files), default=0)
    cache_key = (str(dir_path.resolve()), len(json_files), max_mtime)
    cached = _DIR_CACHE.get(cache_key)
    if cached is not None:
        return cached

    passports: list[dict[str, Any]] = []
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                passport = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(passport, dict) and "package_name" in passport:
            passports.append(passport)

    # Keep cache bounded to avoid unbounded memory growth across many temp dirs
    if len(_DIR_CACHE) > 8:
        _DIR_CACHE.clear()
    _DIR_CACHE[cache_key] = passports
    return passports


def _score_passport(passport: dict[str, Any], query_lower: str) -> dict[str, Any] | None:
    """Score a single passport against a lowercased query string."""
    score = 0
    matched_tools: list[str] = []

    package_name = passport.get("package_name", "")
    if query_lower in package_name.lower():
        score += 4

    description = passport.get("description", "")
    if description and query_lower in description.lower():
        score += 1

    for keyword in passport.get("keywords", []):
        if isinstance(keyword, str) and query_lower in keyword.lower():
            score += 3

    versions = passport.get("versions", [])
    if versions:
        seen_tools: set[str] = set()
        for version in versions:
            for tool in version.get("tool_signatures", []):
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

    if score <= 0:
        return None

    return {
        "package_name": package_name,
        "score": score,
        "matched_tools": matched_tools,
        "ecosystem": passport.get("ecosystem", "unknown"),
        "description": description,
    }


def search_passports(fingerprints_dir: Path | str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search passports for a query, scoring and ranking the results.

    Scores:
      - Exact tool name match: +10
      - Substring tool name match: +5
      - Package name match: +4
      - Keyword match: +3
      - Description match: +1
    """
    dir_path = Path(fingerprints_dir)
    query_lower = query.lower()

    scored_results: list[dict[str, Any]] = []
    for passport in _load_passports_cached(dir_path):
        scored = _score_passport(passport, query_lower)
        if scored is not None:
            scored_results.append(scored)

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:limit]


def format_search_results(results: list[dict[str, Any]]) -> str:
    """Format search results into a clean markdown table."""
    if not results:
        return "No results found."

    headers = ["Package Name", "Ecosystem", "Score", "Matched Tools", "Description"]

    col_widths = [len(h) for h in headers]
    for result in results:
        col_widths[0] = max(col_widths[0], len(str(result.get("package_name", ""))))
        col_widths[1] = max(col_widths[1], len(str(result.get("ecosystem", ""))))
        col_widths[2] = max(col_widths[2], len(str(result.get("score", ""))))
        tools_str = ", ".join(result.get("matched_tools", []))
        if len(tools_str) > 30:
            tools_str = tools_str[:27] + "..."
        col_widths[3] = max(col_widths[3], len(tools_str))

        desc = str(result.get("description", "") or "").replace("\n", " ")
        if len(desc) > 40:
            desc = desc[:37] + "..."
        col_widths[4] = max(col_widths[4], len(desc))

    def format_row(row_data: list[str]) -> str:
        return "| " + " | ".join(str(d).ljust(w) for d, w in zip(row_data, col_widths)) + " |"

    lines = [
        format_row(headers),
        "|-" + "-|-".join("-" * w for w in col_widths) + "-|",
    ]

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
            desc,
        ]
        lines.append(format_row(row))

    return "\n".join(lines)
