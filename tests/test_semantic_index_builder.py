import json
import math
import sys
from pathlib import Path
from unittest import mock

import pytest

try:
    import numpy as np
except ImportError:

    class MockNumpyArray(list):
        def __init__(self, lst, dtype=None):
            super().__init__(lst)
            self.dtype = dtype

        def __truediv__(self, other):
            if isinstance(other, MockNumpyArray):
                return MockNumpyArray(
                    [
                        [x_i / (y[0] if isinstance(y, list) else y) for x_i in x]
                        for x, y in zip(self, other)
                    ]
                )
            return MockNumpyArray([x / other for x in self])

        def __setitem__(self, key, value):
            pass

        def __eq__(self, other):
            return MockNumpyArray([False for _ in self])

        def copy(self):
            return MockNumpyArray(list(self), dtype=self.dtype)

    class MockLinalg:
        @staticmethod
        def norm(vec, axis=None, keepdims=False):
            if axis == 1 and keepdims:
                return MockNumpyArray([[math.sqrt(sum(x * x for x in v))] for v in vec])
            return math.sqrt(sum(x * x for x in vec))

    class MockNumpy:
        linalg = MockLinalg()
        float32 = "float32"

        @staticmethod
        def array(lst, dtype=None):
            return MockNumpyArray(lst, dtype=dtype)

        @staticmethod
        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))

        @staticmethod
        def argpartition(arr, kth):
            return MockNumpyArray(sorted(range(len(arr)), key=lambda i: arr[i]))

        @staticmethod
        def argsort(arr):
            return MockNumpyArray(sorted(range(len(arr)), key=lambda i: arr[i]))

        @staticmethod
        def savez_compressed(path, **kwargs):
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(json.dumps({k: "mock_data" for k in kwargs}))

        @staticmethod
        def load(path, allow_pickle=False):
            return {
                "vectors": MockNumpyArray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
                "package_names": MockNumpyArray(["spreadsheet-tools", "audio-tools"]),
                "metadata": MockNumpyArray(
                    [
                        '{"package_name": "spreadsheet-tools", "description": "", "ecosystem": "python", "matched_tools": [], "score": 0.0}',
                        '{"package_name": "audio-tools", "description": "", "ecosystem": "npm", "matched_tools": [], "score": 0.0}',
                    ]
                ),
            }

    np = MockNumpy()
    sys.modules["numpy"] = np

import scripts.build_semantic_index as build_mod

build_mod.np = np


class MockTextEmbedding:
    def __init__(self, model_name=None):
        self.model_name = model_name

    def embed(self, texts, batch_size=None):
        for t in texts:
            if "spreadsheet" in t.lower() or "sheet" in t.lower():
                yield np.array([1.0, 0.0, 0.0])
            elif "audio" in t.lower() or "speech" in t.lower():
                yield np.array([0.0, 1.0, 0.0])
            else:
                yield np.array([0.0, 0.0, 1.0])


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
def dummy_data_dir(tmp_path):
    passports_dir = tmp_path / "fingerprints"
    passports_dir.mkdir(parents=True)
    with open(passports_dir / "sheet.json", "w") as f:
        json.dump(DUMMY_PASSPORTS[0], f)
    with open(passports_dir / "audio.json", "w") as f:
        json.dump(DUMMY_PASSPORTS[1], f)
    output_npz = tmp_path / "embeddings.npz"
    return passports_dir, output_npz


def test_build_semantic_index(dummy_data_dir):
    passports_dir, output_npz = dummy_data_dir
    with (
        mock.patch(
            "scripts.build_semantic_index.TextEmbedding", MockTextEmbedding, create=True
        ),
        mock.patch("scripts.build_semantic_index.HAS_DEPS", True),
    ):
        build_mod.build_index(passports_dir, output_npz)
        assert output_npz.exists()


def test_semantic_search_with_precomputed_index(dummy_data_dir):
    passports_dir, output_npz = dummy_data_dir
    output_npz.parent.mkdir(parents=True, exist_ok=True)
    # The MockNumpy.load uses the path string so we just need the file to exist
    with open(output_npz, "w") as f:
        f.write('{"mock": "valid_json"}')

    from mcp_fingerprints.semantic_search import semantic_search

    with (
        mock.patch("mcp_fingerprints.semantic_search.HAS_FASTEMBED", True),
        mock.patch(
            "mcp_fingerprints.semantic_search.TextEmbedding",
            MockTextEmbedding,
            create=True,
        ),
        mock.patch("mcp_fingerprints.semantic_search.np", np, create=True),
    ):
        results = semantic_search(
            "spreadsheet", str(passports_dir), top_k=2, index_path=output_npz
        )
        assert len(results) > 0
        assert results[0]["package_name"] == "spreadsheet-tools"
