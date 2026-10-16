import json
import glob
from pathlib import Path

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    modified = False
    
    if "security_profile" in data:
        del data["security_profile"]
        modified = True
        
    for key in ["vulnerabilities", "cve", "cves", "advisories"]:
        if key in data:
            del data[key]
            modified = True
            
    for version in data.get("versions", []):
        for tool in version.get("tool_signatures", []):
            if "parameters" not in tool or not tool["parameters"] or True: # Force rebuild
                params = []
                input_schema = tool.get("inputSchema")
                if input_schema and isinstance(input_schema, dict):
                    properties = input_schema.get("properties", {})
                    required_keys = input_schema.get("required", [])
                    
                    for prop_name, prop_details in properties.items():
                        if not isinstance(prop_details, dict):
                            continue
                        
                        param = {
                            "name": prop_name,
                            "type": prop_details.get("type", "string"),
                        }
                        
                        if "description" in prop_details:
                            param["description"] = prop_details["description"]
                        
                        if prop_name in required_keys:
                            param["required"] = True
                            
                        if "default" in prop_details:
                            param["default"] = prop_details["default"]
                            
                        if "enum" in prop_details:
                            param["enum"] = prop_details["enum"]
                            
                        if "format" in prop_details:
                            param["format"] = prop_details["format"]
                            
                        if param["type"] == "array" and "items" in prop_details and isinstance(prop_details["items"], dict):
                            items = prop_details["items"]
                            if "type" in items:
                                param["items_type"] = items["type"]
                                
                        if param["type"] == "object" and "properties" in prop_details:
                            param["nested_properties"] = prop_details["properties"]
                            
                        params.append(param)
                        
                # Update parameters
                tool["parameters"] = params
                modified = True
                
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

def main():
    files = glob.glob("data/fingerprints/**/*.json", recursive=True)
    count = 0
    for file in files:
        if Path(file).name in ("sync_state.json", "index.json"):
            continue
        process_file(file)
        count += 1
    
    print(f"Processed {count} files.")
    
    # Process sync_state.json
    sync_state_path = "data/fingerprints/sync_state.json"
    if Path(sync_state_path).exists():
        with open(sync_state_path, 'r', encoding='utf-8') as f:
            sync_data = json.load(f)
            
        sync_data["ast_probed_repos"] = []
        sync_data["npm_probed_packages"] = []
        sync_data["pypi_probed_packages"] = []
        
        with open(sync_state_path, 'w', encoding='utf-8') as f:
            json.dump(sync_data, f, indent=2)
        print("Reset stalled zero-tool blacklist arrays in sync_state.json")

if __name__ == "__main__":
    main()
