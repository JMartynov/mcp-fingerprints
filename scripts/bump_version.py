import argparse
import re
import sys
from pathlib import Path
from packaging.version import Version

def get_current_version(pyproject_path: str = "pyproject.toml") -> str:
    path = Path(pyproject_path)
    if not path.exists():
        raise FileNotFoundError(f"{pyproject_path} not found")
    
    content = path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find version in {pyproject_path}")
    return match.group(1)

def bump_patch_version(current_version: str) -> str:
    v = Version(current_version)
    # Simplify any pre/post/dev release back to base and bump patch/micro
    return f"{v.major}.{v.minor}.{v.micro + 1}"

def update_version_in_files(new_version: str, pyproject_path: str = "pyproject.toml", init_path: str = "src/mcp_fingerprints/__init__.py") -> None:
    # Update pyproject.toml
    pyproject = Path(pyproject_path)
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        new_content = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        pyproject.write_text(new_content, encoding="utf-8")

    # Update __init__.py
    init_file = Path(init_path)
    if init_file.exists():
        content = init_file.read_text(encoding="utf-8")
        new_content = re.sub(
            r'^__version__\s*=\s*"[^"]+"',
            f'__version__ = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        init_file.write_text(new_content, encoding="utf-8")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Bump patch version of the project.")
    parser.add_argument("--dry-run", action="store_true", help="Print the next version without modifying files")
    parser.add_argument("--apply", action="store_true", help="Apply the version bump to files")
    parser.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml")
    parser.add_argument("--init-file", default="src/mcp_fingerprints/__init__.py", help="Path to __init__.py")
    
    args = parser.parse_args(argv)
    
    try:
        current_version = get_current_version(args.pyproject)
        next_version = bump_patch_version(current_version)
        
        if args.dry_run:
            print(next_version)
            return 0
            
        if args.apply:
            update_version_in_files(next_version, args.pyproject, args.init_file)
            print(f"Bumped version from {current_version} to {next_version}")
            return 0
            
        # Default behavior if neither --dry-run nor --apply is provided
        print(f"Current version: {current_version}")
        print(f"Next version: {next_version}")
        print("Use --dry-run to print just the next version, or --apply to modify files.")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
