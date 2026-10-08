import json
import math
import sys
from unittest import mock

import pytest

try:
    import numpy as np
except ImportError:

    class MockNumpyArray(list):
        pass

    class MockLinalg:
        @staticmethod
        def norm(vec):
            return math.sqrt(sum(x * x for x in vec))

    class MockNumpy:
        linalg = MockLinalg()

        @staticmethod
        def array(lst):
            return MockNumpyArray(lst)

        @staticmethod
        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))

    np = MockNumpy()
    sys.modules["numpy"] = np

from mcp_fingerprints.cli import main as cli_main
from mcp_fingerprints.semantic_search import semantic_search

# Dummy passports for testing
DUMMY_PASSPORTS = [
    {
        "package_name": "spreadsheet-tools",
        "description": "Tools for working with excel and csv",
        "ecosystem": "python",
        "versions": [
            {
                "tool_signatures": [
                    {"name": "read_sheet", "description": "Reads a sheet"},
                    {"name": "write_sheet", "description": "Writes to a sheet"},
                ]
            }
        ],
    },
    {
        "package_name": "audio-tools",
        "description": "Audio transcription and processing",
        "ecosystem": "npm",
        "versions": [
            {
                "tool_signatures": [
                    {
                        "name": "transcribe_audio",
                        "description": "Converts speech to text",
                    }
                ]
            }
        ],
    },
]


@pytest.fixture
def dummy_passports_dir(tmp_path):
    dir_path = tmp_path / "fingerprints"
    dir_path.mkdir()

    with open(dir_path / "sheet.json", "w") as f:
        json.dump(DUMMY_PASSPORTS[0], f)

    with open(dir_path / "audio.json", "w") as f:
        json.dump(DUMMY_PASSPORTS[1], f)

    return dir_path


class MockTextEmbedding:
    def __init__(self, model_name=None):
        self.model_name = model_name

    def embed(self, texts):
        for t in texts:
            # simple dummy embedding based on string contents
            if "spreadsheet" in t.lower() or "sheet" in t.lower():
                yield np.array([1.0, 0.0, 0.0])
            elif (
                "audio" in t.lower()
                or "speech" in t.lower()
                or "transcribe" in t.lower()
            ):
                yield np.array([0.0, 1.0, 0.0])
            else:
                yield np.array([0.0, 0.0, 1.0])


def test_semantic_search_mocked(dummy_passports_dir):
    with (
        mock.patch("mcp_fingerprints.semantic_search.HAS_FASTEMBED", True),
        mock.patch("mcp_fingerprints.semantic_search.TextEmbedding", MockTextEmbedding),
    ):
        results = semantic_search("read spreadsheet", str(dummy_passports_dir), top_k=2)

        assert len(results) == 2

        # Spreadsheet tools should be top because "spreadsheet" maps to [1,0,0] and the query maps to [1,0,0]
        assert results[0]["package_name"] == "spreadsheet-tools"
        assert results[0]["score"] > 0.9  # Should be 1.0 based on dummy embeddings


def test_semantic_search_fallback(dummy_passports_dir):
    with mock.patch("mcp_fingerprints.semantic_search.HAS_FASTEMBED", False):
        results = semantic_search("spreadsheet", str(dummy_passports_dir), top_k=2)

        # Should fallback to lexical search, which still finds it
        assert len(results) > 0
        assert results[0]["package_name"] == "spreadsheet-tools"


def test_semantic_search_exception_fallback(dummy_passports_dir):
    with (
        mock.patch("mcp_fingerprints.semantic_search.HAS_FASTEMBED", True),
        mock.patch(
            "mcp_fingerprints.semantic_search.SemanticSearcher.search",
            side_effect=Exception("Model failed"),
        ),
    ):
        results = semantic_search("spreadsheet", str(dummy_passports_dir), top_k=2)

        # Should fallback to lexical search
        assert len(results) > 0
        assert results[0]["package_name"] == "spreadsheet-tools"


def test_cli_semantic_search(dummy_passports_dir, monkeypatch, capsys):
    with (
        mock.patch("mcp_fingerprints.semantic_search.HAS_FASTEMBED", True),
        mock.patch("mcp_fingerprints.semantic_search.TextEmbedding", MockTextEmbedding),
    ):
        monkeypatch.setattr(
            "sys.argv",
            [
                "mcp-fingerprints",
                "search",
                "read spreadsheet",
                "--dir",
                str(dummy_passports_dir),
                "--semantic",
            ],
        )

        cli_main()

        captured = capsys.readouterr()

        # Output should format the search results
        assert "spreadsheet-tools" in captured.out
