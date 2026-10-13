import json
import logging
import shutil
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

def partition_path_for_package(package_name: str, ecosystem: str) -> Path:
    """
    Computes the hierarchical partition path for a given package name and ecosystem.
    Examples:
        - npm/@mcp/server -> npm/@/mcp__server.json
        - pypi/mcp-server-git -> pypi/m/mcp-server-git.json
    """
    # Sanitize inputs
    safe_ecosystem = ecosystem.lower().replace("/", "_").replace("\\", "_")
    safe_package = package_name.lower()
    
    # Extract first char or handle namespaces
    if safe_package.startswith("@") and "/" in safe_package:
        # npm namespace
        parts = safe_package.split("/", 1)
        first_char = parts[0][0] # @
        # Flatten the rest for the filename to avoid deep directories and slashes in names
        safe_filename = safe_package.replace("/", "__") + ".json"
    else:
        first_char = safe_package[0] if safe_package else "_"
        safe_filename = safe_package.replace("/", "__") + ".json"
        
    # To avoid special chars in directory names creating issues, allow alpha numeric and @
    if not first_char.isalnum() and first_char != "@":
        first_char = "_"

    return Path(safe_ecosystem) / first_char / safe_filename

def migrate_to_partitioned_layout(data_dir: Path) -> None:
    """
    Migrates flat JSON files in `data_dir` to a hierarchical layout.
    """
    if not data_dir.exists():
        return

    # First, gather all flat JSON files (files directly in data_dir)
    flat_files = [f for f in data_dir.iterdir() if f.is_file() and f.suffix == ".json"]
    
    if not flat_files:
        logger.info("No flat files found to migrate.")
        return
        
    logger.info(f"Migrating {len(flat_files)} flat files to partitioned layout.")
    
    for file_path in flat_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            package_name = data.get("package_name")
            ecosystem = data.get("ecosystem")
            
            if not package_name or not ecosystem:
                logger.warning(f"Skipping {file_path}: missing package_name or ecosystem")
                continue
                
            rel_path = partition_path_for_package(package_name, ecosystem)
            target_path = data_dir / rel_path
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use shutil.move to safely move the file
            shutil.move(str(file_path), str(target_path))
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON in {file_path}")
        except Exception as e:
            logger.error(f"Error migrating {file_path}: {e}")
            
    logger.info("Migration complete.")

def scan_partitioned_fingerprints(data_dir: Path) -> Generator[Path, None, None]:
    """
    Scans for all JSON files within `data_dir`, supporting both flat and partitioned layouts
    gracefully using `rglob`.
    """
    if not data_dir.exists():
        return
    
    # rglob("*.json") recursively finds all JSON files
    yield from data_dir.rglob("*.json")
