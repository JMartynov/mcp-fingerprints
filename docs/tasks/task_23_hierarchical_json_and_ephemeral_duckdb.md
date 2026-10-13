# Task 23: Hierarchical JSON Partitioning & Ephemeral DuckDB Acceleration

### 1. Architectural Context & Technical Objective
`mcp_fingerprints` stores tool fingerprints and metadata as raw JSON files in `data/fingerprints/`. As the repository grows to thousands of fingerprints, a flat directory structure poses issues with inode scaling, git tree performance, and traversal overhead. Furthermore, doing live searches over thousands of JSON files strictly via Python dictionaries and standard loops can result in higher latency.
The objective is to implement a hierarchical directory structure (partitioning) for JSON files based on ecosystem and package name to prevent single-directory scaling issues. Alongside this, an `EphemeralDBEngine` leveraging DuckDB (when available) will be implemented to act as an on-demand, `:memory:` or `.cache/` backed query acceleration engine over these JSON files without introducing tracked binary files into git, keeping the JSON structure as the canonical source of truth.

### 2. Technical Implementation Specifications
1. **Partitioning Engine (`src/mcp_fingerprints/partitioner.py`)**:
   - `partition_path_for_package`: Determine layout based on ecosystem and the first character of the package/namespace.
   - `migrate_to_partitioned_layout`: Gracefully transition flat files to hierarchical structure.
   - `scan_partitioned_fingerprints`: Seamless replacement for `glob` returning a generator over all JSONs in the target directory using `rglob`.
2. **Ephemeral DB Engine (`src/mcp_fingerprints/db_engine.py`)**:
   - `EphemeralDBEngine`: A query engine providing an SQL-like and standardized query interface.
   - Must use `duckdb` (if installed) using `read_json_auto` to build views directly on top of the `.json` files.
   - If `duckdb` is missing, fallback cleanly to `sqlite3` and Python Dictionary caching.
   - Features APIs: `search_packages`, `find_by_hash`, `get_package`, `execute_query`, `get_stats`.
3. **Repository Updates**:
   - Add `duckdb>=1.0.0` as an optional dependency in `pyproject.toml`.
   - Protect git from binary files by updating `.gitignore` to block `*.duckdb`, `*.db`, `*.sqlite`, and `.cache/`.

### 3. Clear Acceptance Criteria
- [ ] `.gitignore` protects against committing binary database files.
- [ ] Partitioning logic correctly places npm namespace packages and PyPI packages into an ecosystem/first_char/name structure.
- [ ] DuckDB Engine accelerates querying across JSON files while relying solely on JSON as the canonical data source.
- [ ] Graceful fallback implementation functions without DuckDB installed.
- [ ] Backward compatibility is maintained with previous `.json` loader mechanisms.

### 4. Unit Test Plan
1. **Partitioning Layout Validation**: Test standard package name generation and complex npm scoped naming rules in `partition_path_for_package`.
2. **Non-destructive Migration**: Test moving flat files into their respective nested structures while skipping bad or malformed files.
3. **DuckDB Integration**: Test `search_packages` and `find_by_hash` natively parsing JSON glob queries using DuckDB.
4. **Fallback Resilience**: Mock DuckDB's availability as False and verify `sqlite3` or python Dictionary querying works transparently.
5. **Gitignore Protection Check**: Test `.gitignore` contents for proper filtering clauses.

### 5. Live Acceptance Test Plan
1. Using an isolated clean virtual environment (without `duckdb`), verify the system still boots, builds the index dictionary correctly and returns results for `mcp-fingerprints search <query>`.
2. In the full environment, run `mcp-fingerprints search <query>` and ensure the `DuckDB` index speeds up subsequent queries sub-15ms.
