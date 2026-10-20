from packaging.version import parse as parse_version
from collections import namedtuple

V = namedtuple("V", ["version"])
sanitized_versions = [V("1.0.0"), V("1.5.11"), V("2.0.0"), V("invalid")]

def _semver_key(x):
    try:
        return (1, parse_version(x.version))
    except Exception:
        return (0, x.version)

print(sorted(sanitized_versions, key=_semver_key, reverse=True))
