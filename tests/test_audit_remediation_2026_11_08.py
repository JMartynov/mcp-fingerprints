import pytest
from mcp_fingerprints.doc_parser import parse_markdown_tool_docs
from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor
import urllib.request
import json
import urllib.error

def test_markdown_deduplication():
    # Markdown containing both a table and a list for the same tools
    content = """
# Available Tools

| Name | Description | Parameters |
|---|---|---|
| search_tool | Searches the web | query (string) |
| list_files | Lists files | dir (string) |

Some detailed descriptions:
- search_tool: Searches the web (query: string)
- list_files: Lists files (dir: string)
- read_file: Reads a file (path: string)
"""
    tools = parse_markdown_tool_docs(content)
    
    # We should have exactly 3 unique tools
    assert len(tools) == 3
    tool_names = {t["name"] for t in tools}
    assert tool_names == {"search_tool", "list_files", "read_file"}

def test_auditor_deduplication(monkeypatch):
    auditor = DeepZeroToolAuditor()
    
    # Monkey patch inspect_file to return deterministic results
    def mock_inspect_file(path, content):
        if "README.md" in path:
            return [{"name": "search_tool", "location": "README.md"}]
        elif "tools.ts" in path:
            return [{"name": "search_tool", "location": "src/tools.ts"}, {"name": "read_file", "location": "src/tools.ts"}]
        return []
    
    auditor.inspect_file = mock_inspect_file
    
    class MockResponse:
        def __init__(self, data):
            self.data = data
        def read(self):
            return self.data
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    def mock_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else req
        if "/git/trees/" in url:
            return MockResponse(json.dumps({
                "tree": [
                    {"path": "README.md", "type": "blob", "size": 100},
                    {"path": "src/tools.ts", "type": "blob", "size": 100}
                ]
            }).encode('utf-8'))
        elif "api.github.com/repos/" in url:
            return MockResponse(json.dumps({
                "default_branch": "main",
                "description": "Mock repo",
                "topics": []
            }).encode('utf-8'))
        else:
            return MockResponse(b"mock file content")
            
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    result = auditor.audit("https://github.com/mock/repo")
    
    # We should only have 2 unique tools: search_tool and read_file
    assert result["tools_found_count"] == 2
    assert "search_tool" in result["tools_found"]
    assert "read_file" in result["tools_found"]
    # The first location should be preserved for search_tool
    assert result["location"] == "README.md"
