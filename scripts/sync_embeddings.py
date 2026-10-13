import argparse
import hashlib
import logging
import sys
from pathlib import Path

# Add src and scripts to sys.path so we can import from them
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.build_semantic_index import HAS_DEPS, build_index

logger = logging.getLogger(__name__)

def compute_fingerprints_hash(passports_dir: Path) -> str:
    """Compute a hash of all passport JSON files to detect changes."""
    hasher = hashlib.sha256()
    skip_files = {"sync_state.json", "index.json", ".passport_index.pickle"}
    
    # Sort paths to ensure consistent hashing
    for file_path in sorted(passports_dir.rglob("*.json")):
        if file_path.name in skip_files:
            continue
        try:
            with open(file_path, "rb") as f:
                hasher.update(f.read())
        except OSError:
            pass
            
    return hasher.hexdigest()

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="Synchronize semantic embeddings cache.")
    parser.add_argument("--passports-dir", default="data/fingerprints", help="Path to passports directory")
    parser.add_argument("--output", default="data/embeddings.npz", help="Path to output NPZ file")
    parser.add_argument("--hash-file", default="data/.embeddings_hash", help="Path to file storing the last hash")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if no changes detected")
    
    args = parser.parse_args()
    
    if not HAS_DEPS:
        logger.warning("Optional dependencies (fastembed, numpy) not installed. Skipping embeddings sync.")
        sys.exit(0)
        
    passports_dir = Path(args.passports_dir)
    output_path = Path(args.output)
    hash_file = Path(args.hash_file)
    
    if not passports_dir.exists():
        logger.warning(f"Passports directory {passports_dir} does not exist. Exiting.")
        sys.exit(0)
        
    current_hash = compute_fingerprints_hash(passports_dir)
    
    if hash_file.exists() and not args.force:
        try:
            last_hash = hash_file.read_text().strip()
            if last_hash == current_hash and output_path.exists():
                logger.info("No changes in fingerprints detected. Embeddings cache is up to date.")
                sys.exit(0)
        except OSError:
            pass
            
    logger.info("Changes detected or index missing. Rebuilding semantic embeddings index...")
    try:
        build_index(passports_dir, output_path)
        # Save new hash
        hash_file.parent.mkdir(parents=True, exist_ok=True)
        hash_file.write_text(current_hash)
        logger.info(f"Updated embeddings hash saved to {hash_file}")
    except Exception as e:
        logger.error(f"Failed to build semantic index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
