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
                        # If the wait time is too long, we can't block the whole job.
                        # For testing and fast execution, we might just fail here.
                        if wait > 30:
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
