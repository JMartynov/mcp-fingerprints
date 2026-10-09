import argparse
import json
import logging
from pathlib import Path

try:
    import numpy as np
    from fastembed import TextEmbedding

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

logger = logging.getLogger(__name__)


def extract_documents(passports: list[dict]) -> tuple[list[str], list[dict]]:
    """Extract documents and metadata for embedding. Matches SemanticSearcher logic."""
    documents = []
    metadata = []

    for passport in passports:
        if not isinstance(passport, dict) or "package_name" not in passport:
            continue

        package_name = passport.get("package_name", "")
        description = passport.get("description", "")
        ecosystem = passport.get("ecosystem", "unknown")

        versions = passport.get("versions", [])
        seen_tools = set()
        matched_tools = []

        # Combine package name, description and tool descriptions to form the document
        doc_parts = []
        if package_name:
            doc_parts.append(f"Package: {package_name}")
        if description:
            doc_parts.append(f"Description: {description}")

        tools_doc_parts = []
        if versions:
            for version in versions:
                tools = version.get("tool_signatures", [])
                for tool in tools:
                    tool_name = tool.get("name", "")
                    tool_desc = tool.get("description", "")

                    if not tool_name or tool_name in seen_tools:
                        continue

                    seen_tools.add(tool_name)
                    matched_tools.append(tool_name)
                    tools_doc_parts.append(f"Tool {tool_name}: {tool_desc}")

        if tools_doc_parts:
            doc_parts.append("Tools: " + " | ".join(tools_doc_parts))

        doc_text = "\n".join(doc_parts)
        documents.append(doc_text)
        metadata.append(
            {
                "package_name": package_name,
                "description": description,
                "ecosystem": ecosystem,
                "matched_tools": matched_tools,
                "score": 0.0,
            }
        )

    return documents, metadata


def load_passports_from_dir(dir_path: Path) -> list[dict]:
    """Helper to load passports from a directory for searching."""
    skip_files = {"sync_state.json", "index.json", ".passport_index.pickle"}
    passports = []

    if not dir_path.exists():
        return passports

    for file_path in dir_path.glob("**/*.json"):
        if file_path.name in skip_files:
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                passport = json.load(f)
                if isinstance(passport, dict) and "package_name" in passport:
                    passports.append(passport)
        except (json.JSONDecodeError, OSError):
            continue

    return passports


def build_index(passports_dir: str | Path, output_path: str | Path) -> None:
    if not HAS_DEPS:
        raise ImportError(
            "numpy and fastembed must be installed to build semantic index."
        )

    passports_dir = Path(passports_dir)
    output_path = Path(output_path)

    logger.info(f"Loading passports from {passports_dir}...")
    passports = load_passports_from_dir(passports_dir)

    logger.info(f"Extracting documents for {len(passports)} passports...")
    documents, metadata = extract_documents(passports)

    if not documents:
        logger.warning("No documents to index.")
        return

    logger.info("Initializing embedding model BAAI/bge-small-en-v1.5...")
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    logger.info("Encoding documents...")
    # Generate embeddings with batch_size=128
    embeddings = list(model.embed(documents, batch_size=128))

    # Convert to numpy array of float32
    vectors = np.array(embeddings, dtype=np.float32)

    # Normalize with L2 norm
    logger.info("Normalizing vectors...")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1
    normalized_vectors = vectors / norms

    package_names = np.array([m["package_name"] for m in metadata], dtype=str)

    # Convert metadata list of dicts to json string array or list of strings
    # We can store as list of json strings
    metadata_json = np.array([json.dumps(m) for m in metadata], dtype=str)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving compressed index to {output_path}...")

    np.savez_compressed(
        output_path,
        vectors=normalized_vectors,
        package_names=package_names,
        metadata=metadata_json,
    )

    logger.info("Semantic index built successfully.")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="Build semantic embeddings index")
    parser.add_argument(
        "--passports-dir",
        default="data/fingerprints",
        help="Path to passports directory",
    )
    parser.add_argument(
        "--output", default="data/embeddings.npz", help="Path to output NPZ file"
    )

    args = parser.parse_args()
    build_index(args.passports_dir, args.output)


if __name__ == "__main__":
    main()
