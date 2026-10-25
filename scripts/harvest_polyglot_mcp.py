#!/usr/bin/env python3
"""Harvest real Model Context Protocol (MCP) repositories across polyglot languages."""

import json
import subprocess
import sys
import time
from pathlib import Path


LANGUAGES = ["Ruby", "Swift", "PHP", "Kotlin"]
TARGET_COUNT = 200
OUTPUT_DIR = Path("data/samples")


def fetch_repos_for_query(query: str, max_pages: int = 5) -> list[dict]:
    repos = []
    seen = set()
    for page in range(1, max_pages + 1):
        cmd = [
            "gh", "api",
            f"search/repositories?q={query}&per_page=100&page={page}",
            "--jq", ".items[] | {name: .name, full_name: .full_name, html_url: .html_url, description: .description, stars: .stargazers_count, default_branch: .default_branch, topics: .topics}"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
            if not lines:
                break
            for line in lines:
                try:
                    item = json.loads(line)
                    fn = item.get("full_name")
                    if fn and fn not in seen:
                        seen.add(fn)
                        repos.append(item)
                except Exception:
                    continue
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching page {page} for '{query}': {e}", file=sys.stderr)
            break
    return repos


def harvest_language(lang: str) -> list[dict]:
    queries = [
        f"mcp-server+language:{lang}",
        f"modelcontextprotocol+language:{lang}",
        f"mcp+server+language:{lang}",
        f"topic:mcp-server+language:{lang}",
        f"mcp+tool+language:{lang}",
    ]
    all_repos = {}
    print(f"[*] Harvesting {lang} MCP repositories...")
    for q in queries:
        items = fetch_repos_for_query(q, max_pages=3)
        for item in items:
            fn = item["full_name"]
            if fn not in all_repos:
                all_repos[fn] = item
        if len(all_repos) >= TARGET_COUNT:
            break

    result = list(all_repos.values())[:TARGET_COUNT]
    print(f"[+] Found {len(result)} unique real repositories for {lang}")
    return result


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for lang in LANGUAGES:
        repos = harvest_language(lang)
        out_file = OUTPUT_DIR / f"{lang.lower()}_mcp_200.json"
        out_file.write_text(json.dumps(repos, indent=2), encoding="utf-8")
        summary[lang] = len(repos)
        print(f"[✓] Saved {len(repos)} repositories to {out_file}")

    print("\n=== Harvest Summary ===")
    for lang, count in summary.items():
        print(f" - {lang}: {count} repos")


if __name__ == "__main__":
    main()
