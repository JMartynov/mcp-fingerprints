# Task 46: High-Performance Multi-Core Parallel Batching & Two-Tier SHA-256 Cache Engine

## 1. Context & Objectives
In `mcp-fingerprints`, over 5,000 passport JSON files are processed, validated, and compiled. Currently, `PassportSchemaValidator.validate_directory()` and `build_snapshot()` process files sequentially in a single-threaded loop, re-reading and re-validating every file from scratch on every run.

Implement maximum parallelism and a high-performance two-tier content-addressable SHA-256 caching engine:

1. **Multi-Core Parallel Batching**:
   - Utilize `concurrent.futures.ProcessPoolExecutor` utilizing all available CPU cores (`os.cpu_count()`) to bypass the Python Global Interpreter Lock (GIL).
   - Implement batch-chunking (e.g. 50–100 files per worker chunk) to minimize IPC/pickling overhead across worker processes.
   - Graceful fallback to single-process mode when running in constrained environments (e.g. `max_workers=1` or when spawning processes is restricted).

2. **Two-Tier Content-Addressable Cache Engine (`src/mcp_fingerprints/cache.py`)**:
   - Structure a persistent cache in `data/.passport_cache.json` (or customizable path).
   - **Tier 1 (Instant stat check)**: Compare file `st_size` and `st_mtime_ns`. If identical to cached record, trust the prior validation/snapshot status without reading file bytes.
   - **Tier 2 (SHA-256 Digest Verification)**: If `st_mtime_ns` or `st_size` differs, compute the file's SHA-256 content digest. If the hash matches the cached hash (e.g. touched timestamp but unchanged content), update the timestamp and bypass re-validation.
   - **Tier 3 (Cache Miss / Modification)**: If SHA-256 changed or entry is new, execute full validation/parsing in the parallel worker pool and update the cache.
   - Implement atomic cache writes (write to temporary file and `os.replace`) to prevent cache corruption during abrupt process termination.
   - Prune entries from the cache when corresponding files are removed from the filesystem.

3. **Accelerate Core Operations**:
   - `PassportSchemaValidator.validate_directory()`: Parallelized and cached validation.
   - `mcp-fingerprints validate`: Add `--no-cache` / `--force` flags and `--workers <N>` option.
   - `build_snapshot()`: Parallelized passport reading and fast incremental snapshot building using cached parsed objects or fast payload assembly.

4. **CLI & Telemetry**:
   - Output cache statistics in validate/snapshot summary (e.g., `Valid: 5,058 (5,050 cached, 8 validated in 0.42s)`).

5. **Testing & Invariants**:
   - Comprehensive unit tests in `tests/test_cache.py` and `tests/test_parallel_validator.py`.
   - Verify cache hit on unchanged files, cache miss on modified files, cache invalidation on deleted files, `--no-cache` behavior, and equivalence of parallel vs sequential results.
   - Zero external dependencies: rely solely on Python standard library (`hashlib`, `concurrent.futures`, `multiprocessing`, `os`, `json`, `pathlib`).

## 2. Strict Guardrails:
- Non-interactive completion directive: Implement all code and tests, ensure `pytest` passes, and finalize with a concise summary without open-ended questions.
