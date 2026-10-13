# Task 25: Automated Semantic Embeddings Cache CI Synchronization

### 1. Architectural Context & Technical Objective
The `mcp_fingerprints` repository includes a pre-computed semantic embeddings index (`data/embeddings.npz`) for MCP tool fingerprints using `fastembed` and `numpy`. Currently, this cache must be manually updated when new fingerprints are added.
The objective is to automate the synchronization of this embeddings cache within the CI/CD pipeline (e.g., in `.github/workflows/daily_sync.yml`). This ensures that the vector search remains perfectly in sync with the structural fingerprint database on every automated release.

### 2. Technical Implementation Specifications
1. Create a script `scripts/sync_embeddings.py` that utilizes `src/mcp_fingerprints/semantic_search.py` to regenerate `data/embeddings.npz`.
2. Update `.github/workflows/daily_sync.yml` to run `uv run python scripts/sync_embeddings.py` after new fingerprints are ingested.
3. Ensure the script only runs if new fingerprints are detected.
4. Add the updated `data/embeddings.npz` to the automated commit.
5. The `sync_embeddings.py` script must handle missing optional dependencies (`fastembed`, `numpy`) gracefully during isolated CI environments if not installed, though CI should install the `semantic` extra.

### 3. Clear Acceptance Criteria
- [ ] `scripts/sync_embeddings.py` is implemented and can regenerate `data/embeddings.npz`.
- [ ] `.github/workflows/daily_sync.yml` is updated to include the embedding sync step.
- [ ] Automated commits include the updated `data/embeddings.npz` file.
- [ ] CI uses `uv sync --all-extras` or equivalent to ensure `fastembed` is available.

### 4. Unit Test Plan
1. **Mock Generation:** Mock `fastembed` to return dummy vectors and assert that `sync_embeddings.py` writes an `.npz` file with the correct shape to a temporary directory.
2. **Missing Dependencies:** Run the sync function with `fastembed` mocked out as missing (e.g., `ImportError`) and verify it logs a warning and exits gracefully.
3. **No Changes Detected:** Ensure the script exits early if the existing embeddings cache already matches the latest fingerprints hash.

### 5. Live Acceptance Test Plan
Run `uv sync --all-extras` then manually add a dummy fingerprint to `data/fingerprints/`. Run `python scripts/sync_embeddings.py` and verify `data/embeddings.npz` is modified on disk using `git status`.
