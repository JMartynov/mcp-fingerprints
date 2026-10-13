import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Attempt to import duckdb, with a graceful fallback if missing
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    duckdb = None  # type: ignore
    DUCKDB_AVAILABLE = False

class EphemeralDBEngine:
    """
    Provides an ephemeral on-demand DuckDB or SQLite/Dict query acceleration engine.
    Ensures zero git footprint by using `:memory:` or gitignored `.cache/` locations.
    """
    
    def __init__(self, data_dir: Path, use_cache: bool = False, cache_dir: Optional[Path] = None):
        self.data_dir = data_dir
        self.use_cache = use_cache
        self.cache_dir = cache_dir or Path(".cache/mcp_fingerprints")
        self.db_path = ":memory:"
        self._duck_conn = None
        self._sqlite_conn = None
        self._dict_index: Dict[str, Dict[str, Any]] = {}
        
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(self.cache_dir / "index.duckdb") if DUCKDB_AVAILABLE else str(self.cache_dir / "index.sqlite")

        self._initialize_db()
        
    def _initialize_db(self) -> None:
        if DUCKDB_AVAILABLE:
            try:
                self._duck_conn = duckdb.connect(self.db_path)
                self._build_duckdb_views()
            except Exception as e:
                logger.error(f"DuckDB initialization failed: {e}. Falling back.")
                self._fallback_init()
        else:
            logger.info("DuckDB not available. Falling back to SQLite/Dict index.")
            self._fallback_init()

    def _build_duckdb_views(self) -> None:
        if not self._duck_conn:
            return
            
        glob_pattern = str(self.data_dir / "**" / "*.json")
        # Create a view directly querying the JSON files via duckdb's read_json_auto
        # It recursively reads all json matching the pattern
        try:
            self._duck_conn.execute(f"""
                CREATE OR REPLACE VIEW fingerprints AS 
                SELECT * FROM read_json_auto('{glob_pattern}', ignore_errors=true)
            """)
        except duckdb.Error as e:
            # Table might fail if no JSON files exist yet
            logger.warning(f"Could not build DuckDB view, possibly no JSON files exist: {e}")

    def _fallback_init(self) -> None:
        # Simple fallback using dict/sqlite
        if self.db_path == ":memory:" or not self.use_cache:
            self._build_dict_index()
        else:
            self._sqlite_conn = sqlite3.connect(self.db_path)
            self._sqlite_conn.row_factory = sqlite3.Row
            self._build_sqlite_tables()
            
    def _build_dict_index(self) -> None:
        self._dict_index = {}
        if not self.data_dir.exists():
            return
            
        for f in self.data_dir.rglob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    pkg = data.get("package_name")
                    if pkg:
                        self._dict_index[pkg] = data
            except (json.JSONDecodeError, OSError):
                continue
                
    def _build_sqlite_tables(self) -> None:
        if not self._sqlite_conn:
            return
            
        cur = self._sqlite_conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fingerprints (
                package_name TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        
        if not self.data_dir.exists():
            return
            
        for f in self.data_dir.rglob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    raw = file.read()
                    data = json.loads(raw)
                    pkg = data.get("package_name")
                    if pkg:
                        cur.execute(
                            "INSERT OR REPLACE INTO fingerprints (package_name, data) VALUES (?, ?)", 
                            (pkg, raw)
                        )
            except (json.JSONDecodeError, OSError):
                continue
        self._sqlite_conn.commit()

    def search_packages(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self._duck_conn:
            try:
                # Basic LIKE search on package_name or description
                res = self._duck_conn.execute("""
                    SELECT * FROM fingerprints 
                    WHERE package_name ILIKE ? OR description ILIKE ?
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit)).fetchall()
                desc = self._duck_conn.description
                cols = [d[0] for d in desc]
                return [dict(zip(cols, row)) for row in res]
            except Exception as e:
                logger.error(f"DuckDB search failed: {e}")
                return []
                
        elif self._sqlite_conn:
            cur = self._sqlite_conn.cursor()
            cur.execute("""
                SELECT data FROM fingerprints 
                WHERE package_name LIKE ? OR json_extract(data, '$.description') LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            return [json.loads(row["data"]) for row in cur.fetchall()]
            
        else:
            results = []
            q = query.lower()
            for pkg, data in self._dict_index.items():
                if q in pkg.lower() or q in data.get("description", "").lower():
                    results.append(data)
                    if len(results) >= limit:
                        break
            return results

    def find_by_hash(self, toolset_hash: str) -> Optional[Dict[str, Any]]:
        # Using version_fingerprints[0].toolset_hash in DuckDB
        if self._duck_conn:
            try:
                # Use DuckDB list_filter/contains equivalent or UNNEST to check all elements
                res = self._duck_conn.execute("""
                    SELECT * FROM fingerprints 
                    WHERE list_filter(version_fingerprints, x -> x.toolset_canonical_hash = ?) != []
                    LIMIT 1
                """, (toolset_hash,)).fetchall()
                desc = self._duck_conn.description
                cols = [d[0] for d in desc]
                recs = [dict(zip(cols, row)) for row in res]
                return recs[0] if recs else None
            except Exception as e:
                logger.error(f"DuckDB find_by_hash failed: {e}")
                return None
                
        elif self._sqlite_conn:
            cur = self._sqlite_conn.cursor()
            cur.execute("SELECT data FROM fingerprints")
            for row in cur.fetchall():
                data = json.loads(row["data"])
                for vf in data.get("version_fingerprints", []):
                    if vf.get("toolset_canonical_hash") == toolset_hash:
                        return data
            return None
            
        else:
            for pkg, data in self._dict_index.items():
                for vf in data.get("version_fingerprints", []):
                    if vf.get("toolset_canonical_hash") == toolset_hash:
                        return data
            return None

    def get_package(self, package_name: str) -> Optional[Dict[str, Any]]:
        if self._duck_conn:
            try:
                res = self._duck_conn.execute("""
                    SELECT * FROM fingerprints 
                    WHERE package_name = ?
                    LIMIT 1
                """, (package_name,)).fetchall()
                desc = self._duck_conn.description
                cols = [d[0] for d in desc]
                recs = [dict(zip(cols, row)) for row in res]
                return recs[0] if recs else None
            except Exception as e:
                logger.error(f"DuckDB get_package failed: {e}")
                return None
                
        elif self._sqlite_conn:
            cur = self._sqlite_conn.cursor()
            cur.execute("SELECT data FROM fingerprints WHERE package_name = ?", (package_name,))
            row = cur.fetchone()
            return json.loads(row["data"]) if row else None
            
        else:
            return self._dict_index.get(package_name)

    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Direct SQL execution. Not available for dict index fallback."""
        if self._duck_conn:
            try:
                if params:
                    res = self._duck_conn.execute(sql, params).fetchall()
                else:
                    res = self._duck_conn.execute(sql).fetchall()
                desc = self._duck_conn.description
                cols = [d[0] for d in desc]
                return [dict(zip(cols, row)) for row in res]
            except Exception as e:
                logger.error(f"DuckDB execute_query failed: {e}")
                return []
        elif self._sqlite_conn:
            cur = self._sqlite_conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]
        else:
            raise NotImplementedError("Direct SQL queries are not supported without DuckDB or SQLite")

    def get_stats(self) -> Dict[str, Any]:
        engine_type = "duckdb" if self._duck_conn else ("sqlite" if self._sqlite_conn else "dict")
        count = 0
        if self._duck_conn:
            try:
                res = self._duck_conn.execute("SELECT count(*) as count FROM fingerprints").fetchone()
                count = res[0] if res else 0
            except:
                pass
        elif self._sqlite_conn:
            cur = self._sqlite_conn.cursor()
            cur.execute("SELECT count(*) FROM fingerprints")
            count = cur.fetchone()[0]
        else:
            count = len(self._dict_index)
            
        return {
            "engine": engine_type,
            "storage": self.db_path,
            "package_count": count
        }
        
    def close(self):
        if self._duck_conn:
            self._duck_conn.close()
        if self._sqlite_conn:
            self._sqlite_conn.close()


def benchmark_query_performance(data_dir: Path) -> Dict[str, float]:
    """
    Latencies benchmark comparing baseline JSON scanning with DuckDB.
    """
    logger.info("Starting performance benchmark...")
    
    # 1. Baseline: scan and find a package manually (Python Dict/File scan)
    start_time = time.time()
    found = False
    for f in data_dir.rglob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                if data.get("package_name") == "target_benchmark_package":
                    found = True
                    break
        except Exception:
            continue
    baseline_time = time.time() - start_time
    
    # 2. DuckDB Engine (cold start / view creation overhead)
    start_time = time.time()
    engine = EphemeralDBEngine(data_dir=data_dir, use_cache=False)
    db_init_time = time.time() - start_time
    
    # 3. DuckDB query execution
    start_time = time.time()
    engine.get_package("target_benchmark_package")
    query_time = time.time() - start_time
    
    engine.close()
    
    return {
        "baseline_scan_seconds": baseline_time,
        "db_init_seconds": db_init_time,
        "db_query_seconds": query_time,
    }
