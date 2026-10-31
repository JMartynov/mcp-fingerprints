import re

with open("tests/test_reindex_sdk_passports.py", "r") as f:
    content = f.read()

python_test_start = content.find('def test_extract_tools_from_repo_python(mock_fetch_raw, mock_request):')
go_test_start = content.find('def test_extract_tools_from_repo_go(mock_fetch_raw, mock_request):')

# Find the end of python test
python_test_end = content.find('@patch', python_test_start)

# Replace just the python test body
new_python_test = '''def test_extract_tools_from_repo_python(mock_fetch_raw, mock_request):
    mock_request.side_effect = [
        {"default_branch": "main"},  # Repo fetch
        {"tree": [{"path": "main.py", "type": "blob"}]} # Tree fetch
    ]
    mock_fetch_raw.return_value = """
from mcp import Tool
def get_tools():
    return [
        Tool(name="python_tool", description="A python test tool", inputSchema={"type": "object"})
    ]
"""
    
    tools = extract_tools_from_repo("test-owner", "test-repo")
    assert len(tools) == 1
    assert tools[0]["name"] == "python_tool"
    assert "description" in tools[0]

'''

content = content[:python_test_start] + new_python_test + content[python_test_end:]

with open("tests/test_reindex_sdk_passports.py", "w") as f:
    f.write(content)
