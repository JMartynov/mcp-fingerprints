import re

with open("src/mcp_fingerprints/synchronizer.py", "r") as f:
    content = f.read()

# Fix 2: Import packaging.version
if "from packaging.version import parse as parse_version" not in content:
    content = content.replace("from pathlib import Path\nfrom typing import Any", "from pathlib import Path\nfrom typing import Any\nfrom packaging.version import parse as parse_version")

# Fix 3: Version sorting
search2 = r'versions=tuple\(sorted\(sanitized_versions, key=lambda x: x\.version\)\),'
replace2 = """versions=tuple(
                sorted(
                    sanitized_versions,
                    key=lambda x: (
                        1 if (lambda v: hasattr(parse_version(v), "major"))(x.version) else 0,
                        parse_version(x.version) if (lambda v: hasattr(parse_version(v), "major"))(x.version) else x.version
                    )
                )
            ),"""

# Using the simplified sorting logic that works safely:
replace2 = """versions=tuple(
                sorted(
                    sanitized_versions,
                    key=lambda x: (
                        (lambda p: (1, p) if hasattr(p, "major") else (0, x.version))(parse_version(x.version))
                        if True else (0, x.version)
                    )
                )
            ),"""

# Or define a small helper function in the class? Let's just do a robust lambda:
replace2 = """versions=tuple(
                sorted(
                    sanitized_versions,
                    key=lambda x: (
                        (lambda v: (1, parse_version(v)) if hasattr(parse_version(v), "major") else (0, v))(x.version)
                        if isinstance(x.version, str) else (0, str(x.version))
                    )
                )
            ),"""

# Wait, `packaging.version.parse` will not have `major` attribute if it's a `LegacyVersion` or in newer packaging versions, non-standard versions raise `InvalidVersion`. We should use a safe approach.
# A standard approach is to use a try/except, but lambda doesn't support it directly.
