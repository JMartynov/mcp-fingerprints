# Task 47: Graceful Time-Budgeted Stage-by-Stage Checkpoint & Resume Engine

## 1. Context & Objectives
Long-running synchronizations and remote crawlers in `PassportSynchronizer` (`src/mcp_fingerprints/synchronizer.py`) run against remote rate limits and CI/CD timeout ceilings (e.g. GitHub Actions 6h or Jules 80-minute DevBox budget).

Implement a robust, stage-by-stage time-budgeted execution engine that gracefully checkpoints progress, stops cleanly on success, and resumes on subsequent runs:

1. **Configurable Time-Budget & Signal Monitor**:
   - Add `--time-budget <seconds>` (default: 2400s / 40 min; 0 = unlimited) to `PassportSynchronizer` and CLI `sync`.
   - Measure elapsed runtime using `time.monotonic()`. Before initiating any remote API call, page fetch, or package download, verify if remaining time is below a safety threshold (default: 30s).
   - Register graceful handlers for `SIGTERM` and `SIGINT` to catch external runner aborts and persist checkpoints before process termination.

2. **Dedicated Checkpoint File (`data/.sync_checkpoint.json`)**:
   - Persist ephemeral checkpoint state isolated from `sync_state.json`:
     ```json
     {
       "checkpoint_active": true,
       "current_stage": "stage_discover_new",
       "substage": "smithery",
       "page": 7,
       "cursor": "...",
       "completed_stages": ["stage_update_existing", "stage_enrich_ast"],
       "timestamp": "2026-10-19T19:30:00Z",
       "reason": "time_budget_reached"
     }
     ```
   - Use atomic write (`tempfile` + `os.replace`) to prevent corruption.

3. **Stage-by-Stage Mark Management & Lifecycle**:
   - Define discrete synchronization stages:
     - `stage_update_existing`: Checking upstream versions for existing passports
     - `stage_enrich_ast`: AST/doc parsing for passports missing tool definitions
     - `stage_discover_new`:
       - `substage_smithery` (page 1..N)
       - `substage_pypi` (candidate iteration)
       - `substage_npm` (search page/limit)
       - `substage_official_registry` (cursor iteration)
       - `substage_awesome_mcp` (repo iteration)
     - `stage_runtime_probing`: Live stdio/http probing
   - **Stage-by-Stage Cleansing**: When a substage or stage finishes, immediately remove its checkpoint marker, append it to `completed_stages`, and advance `current_stage`.
   - When all stages successfully finish, completely delete `data/.sync_checkpoint.json`.

4. **Graceful Exit on Success & Automatic Resumption**:
   - When the time budget is reached:
     - Flush all in-memory passports and state to disk.
     - Write the active checkpoint marker.
     - Log: `Time budget reached. Gracefully checkpointed at stage '<stage>' (offset/page <X>). Exiting with status 0.`
     - Exit with exit code 0 so CI/CD and runners register clean success.
   - On subsequent execution:
     - Detect `data/.sync_checkpoint.json`.
     - Skip stages listed in `completed_stages`.
     - Fast-forward to the saved stage, substage, page, and cursor.
   - CLI flags: `--time-budget <sec>`, `--ignore-checkpoint`, `--clear-checkpoint`.

5. **Testing & Invariants**:
   - Unit tests in `tests/test_checkpoint_engine.py`:
     - Test simulated time budget exhaustion triggering clean exit 0 and saving `data/.sync_checkpoint.json`.
     - Test resumption from saved stage and skipping completed stages.
     - Test stage mark deletion as each stage passes and full file deletion on complete run.
     - Test `--ignore-checkpoint` and `--clear-checkpoint`.
   - Zero unauthorized dependencies: use Python standard library (`time`, `signal`, `json`, `pathlib`).

## 2. Strict Guardrails:
- Non-interactive completion directive: Implement all code and tests, verify with `pytest -v`, and finalize with a concise summary without open-ended questions.
