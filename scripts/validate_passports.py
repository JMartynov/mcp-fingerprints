import json
import sys
from pathlib import Path

def validate_passports(data_dir: str) -> int:
    try:
        from mcp_fingerprints.models import ServerPackageSpec
    except ImportError:
        print("ERROR: Could not import ServerPackageSpec. Make sure PYTHONPATH includes the src directory.")
        return 1

    dir_path = Path(data_dir)
    if not dir_path.exists():
        print(f"ERROR: Data directory '{data_dir}' does not exist.")
        return 1
        
    has_errors = False
    for json_file in sorted(dir_path.rglob("*.json")):
        if json_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"{json_file}: ERROR: Invalid JSON: {e}")
            has_errors = True
            continue
            
        required_fields = ["passport_schema_version", "purl", "package_name", "ecosystem"]
        for field in required_fields:
            if not data.get(field):
                print(f"{json_file}: ERROR: Missing required field '{field}'.")
                has_errors = True

        try:
            spec = ServerPackageSpec.from_dict(data)
        except Exception as e:
            print(f"{json_file}: ERROR: Failed to parse ServerPackageSpec: {e}")
            has_errors = True
            continue
            
        versions = data.get("versions", [])
        for v in versions:
            tools = v.get("tool_signatures", [])
            for t in tools:
                if not isinstance(t.get("name"), str) or not t["name"]:
                    print(f"{json_file}: ERROR: Tool signature missing 'name' string.")
                    has_errors = True
                if not isinstance(t.get("description"), str):
                    print(f"{json_file}: ERROR: Tool signature '{t.get('name')}' missing 'description' string.")
                    has_errors = True
                if not isinstance(t.get("inputSchema"), dict):
                    print(f"{json_file}: ERROR: Tool signature '{t.get('name')}' missing 'inputSchema' dict.")
                    has_errors = True
                    
    if has_errors:
        return 1
    else:
        print("All passports valid.")
        return 0

if __name__ == "__main__":
    sys.exit(validate_passports("data/fingerprints"))
