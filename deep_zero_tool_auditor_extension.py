import argparse
import datetime
import json
import logging
import os
import re

from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor

def extract_suspicious_cards(catalog_path, max_suspicious):
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
        
    suspicious_cards = []
    
    for server in catalog:
        # Check suspicious criteria
        is_suspicious = False
        
        # 1. tool_count == 0 or len(tools) == 0
        if server.get("tool_count", 0) == 0 or len(server.get("tools", [])) == 0:
            is_suspicious = True
            
        # 2. description is null, "", or < 10 chars
        desc = server.get("description")
        if not desc or len(str(desc)) < 10:
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
            # Try to get stars or downloads (if they exist) for sorting. For simplicity, just append.
            suspicious_cards.append(server)
            
    # For prioritization, we'd normally sort by stars/downloads. Here we can just take the first max_suspicious
    # Or ideally, sort if properties exist.
    
    return suspicious_cards[:max_suspicious]

def extract_latest_updates(web_updates_path):
    with open(web_updates_path, 'r') as f:
        updates = json.load(f)
    return updates.get("servers", []), updates.get("version", "unknown")

print("Ready")
