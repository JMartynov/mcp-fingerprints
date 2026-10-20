import re

with open("src/mcp_fingerprints/synchronizer.py", "r") as f:
    content = f.read()

# Fix 1: npm repository extraction
search1 = r'repo_raw = npm_data\.get\("homepage"\) or npm_data\.get\("bugs", {}\)\.get\("url"\)\s+if repo_raw:\s+repo_url = repo_raw'
replace1 = """repo_field = npm_data.get("repository")
            repo_raw = None
            if isinstance(repo_field, dict):
                repo_raw = repo_field.get("url")
            elif isinstance(repo_field, str):
                repo_raw = repo_field
            if not repo_raw:
                repo_raw = npm_data.get("homepage") or npm_data.get("bugs", {}).get("url")
            if repo_raw:
                clean_repo = re.sub(r"^git\\+", "", repo_raw)
                clean_repo = re.sub(r"\\.git$", "", clean_repo)
                clean_repo = re.sub(r"^git://", "https://", clean_repo)
                clean_repo = re.sub(r"^ssh://git@", "https://", clean_repo)
                repo_url = clean_repo"""

if re.search(search1, content):
    content = re.sub(search1, replace1, content)
else:
    print("Could not find search1")

with open("src/mcp_fingerprints/synchronizer.py", "w") as f:
    f.write(content)
