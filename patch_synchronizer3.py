import re

with open("src/mcp_fingerprints/synchronizer.py", "r") as f:
    content = f.read()

# Fix 2: Import packaging.version
if "from packaging.version import parse as parse_version" not in content:
    content = content.replace("from typing import Any", "from typing import Any\nfrom packaging.version import parse as parse_version\nfrom packaging.version import InvalidVersion")

# Helper function can be defined locally or we can just replace the block with a try/except.
# Actually, the simplest is to define a helper function before `ServerPackageSpec(...)`

# We need to replace:
# sanitized_versions = []
# for v in all_versions:

search_block = """        # Ensure all versions have a valid version string
        sanitized_versions = []
        for v in all_versions:"""

replace_block = """        # Ensure all versions have a valid version string
        sanitized_versions = []
        for v in all_versions:"""

# And then for sorting:
search_sort = r"versions=tuple\(sorted\(sanitized_versions, key=lambda x: x\.version\)\),"

# Let's write a small script to inject a helper inside `merge_and_enrich_passport`
search_inject = """        clean_pkg_name = package_name.strip()
        is_valid, reason = McpServerValidator.is_valid_mcp_server("""

replace_inject = """        clean_pkg_name = package_name.strip()
        
        def _semver_key(v_obj):
            try:
                return (1, parse_version(v_obj.version))
            except InvalidVersion:
                return (0, v_obj.version)
                
        is_valid, reason = McpServerValidator.is_valid_mcp_server("""

content = content.replace(search_inject, replace_inject)

replace_sort = "versions=tuple(sorted(sanitized_versions, key=_semver_key)),"
content = re.sub(search_sort, replace_sort, content)

with open("src/mcp_fingerprints/synchronizer.py", "w") as f:
    f.write(content)
