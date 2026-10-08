"""Semantic search module for discovering MCP servers using embeddings."""

import json
import logging
from pathlib import Path
from typing import Any

from mcp_fingerprints.search import search_passports

logger = logging.getLogger(__name__)

try:
    from fastembed import TextEmbedding

    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False
    TextEmbedding = None


class SemanticSearcher:
    """Handles semantic search logic utilizing fastembed if available."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if not HAS_FASTEMBED:
            raise ImportError(
                "fastembed is not installed. Install with `pip install mcp-fingerprints[semantic]`"
            )
        if self._model is None:
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def _extract_documents(self, passports: list[dict]) -> tuple[list[str], list[dict]]:
        """Extract documents and metadata for embedding."""
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

    def search(
        self, query: str, passports: list[dict], top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Perform semantic search."""
        if not HAS_FASTEMBED:
            logger.warning(
                "fastembed is not installed. Falling back to lexical search."
            )
            raise ImportError("fastembed is not installed")

        if not passports:
            return []

        documents, metadata = self._extract_documents(passports)
        if not documents:
            return []

        # Embed query and documents
        try:
            import numpy as np

            # fastembed returns generators
            query_embeddings = list(self.model.embed([query]))
            if not query_embeddings:
                return []
            query_emb = query_embeddings[0]

            doc_embeddings = list(self.model.embed(documents))

            # Calculate cosine similarities
            scores = []
            for i, doc_emb in enumerate(doc_embeddings):
                # Cosine similarity: (A dot B) / (||A|| * ||B||)
                dot_product = np.dot(query_emb, doc_emb)
                norm_q = np.linalg.norm(query_emb)
                norm_d = np.linalg.norm(doc_emb)

                similarity = 0.0
                if norm_q > 0 and norm_d > 0:
                    similarity = dot_product / (norm_q * norm_d)

                scores.append((similarity, i))

            # Sort by descending similarity
            scores.sort(key=lambda x: x[0], reverse=True)

            results = []
            for score, idx in scores[:top_k]:
                item = metadata[idx].copy()
                item["score"] = float(score)  # Replace 0.0 with actual similarity
                # Normalize score to match lexical search scale loosely, or just return as is
                results.append(item)

            return results

        except Exception as e:
            logger.error(
                f"Semantic search failed: {e}. Falling back to lexical search."
            )
            raise


def load_passports_from_dir(dir_path: Path | str) -> list[dict]:
    """Helper to load passports from a directory for searching."""
    dir_path = Path(dir_path)
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


def semantic_search(
    query: str, passports_dir: Path | str, top_k: int = 10
) -> list[dict[str, Any]]:
    """
    Main entry point for semantic search.
    Gracefully falls back to lexical search if fastembed is missing or fails.
    """
    try:
        if not HAS_FASTEMBED:
            raise ImportError("fastembed is not installed.")

        passports = load_passports_from_dir(passports_dir)
        searcher = SemanticSearcher()
        return searcher.search(query, passports, top_k=top_k)

    except ImportError as e:
        logger.warning(
            f"Semantic search unavailable ({e}). Falling back to lexical search."
        )
        return search_passports(passports_dir, query, limit=top_k)
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Semantic search encountered an error: {e}. Falling back to lexical search."
        )
        return search_passports(passports_dir, query, limit=top_k)
