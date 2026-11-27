# AGENTS.md — MCP Fingerprints (`mcp-fingerprints`)

> **Scope**: Operational guide for [`mcp-fingerprints`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints) (MIT, Python `>=3.10`). Strictly a structural MCP server classification, AST extraction, canonical SHA-256 hashing, and passport knowledge base — **not** a security firewall, fuzzer, or runtime proxy.

---

## 1. Repository Layout & Specs

- **Package**: `mcp-fingerprints` (`src/mcp_fingerprints/cli.py`, `pyproject.toml`)
- **Dataset & Snapshot**: `data/fingerprints/`, `passports.json.gz`, `scripts/validate_passports.py`
- **Specs & Tasks**: [`docs/SPECIFICATION.md`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/docs/SPECIFICATION.md) | `docs/tasks/`

---

## 2. Hard Guardrails

- **Code & Tests Only for DeepSeek**: Restrict `aider_bridge.py` (`dispatch` / `turn`) to production code and test files (`*.py`, `*.sh`, `Dockerfile`, CI workflows). Handle routine Markdown, doc, and task/board status syncs (`README.md`, `CHANGELOG.md`, `docs/tasks/*.md`) directly in ephemeral Antigravity `flash` / `flash_lite` subagents.
- **No Read-Only `--plan-align` Audits**: Never invoke `aider_bridge.py --plan-align` for read-only repo audits (use Antigravity `research` `flash` subagents or `aider_bridge.py scope`). Use `--plan-align` only when true architectural ambiguity exists.
- **Preserve Deterministic Hashing & Zero-Mock Data**: Keep canonical SHA-256 hashing (`canonical_hash`, `toolset_canonical_hash`) deterministic; never fabricate passport data or commit `.env` secrets.

---

## 3. Shared `.env` & DeepSeek Worktree Workflow (`aider_bridge.py`)

`DEEPSEEK_API_KEY` lives in `/Users/ivan/Project/3t.tools.intellij/verityredteam/.env`. Source it before invoking `aider_bridge.py`:

```bash
set -a && source /Users/ivan/Project/3t.tools.intellij/verityredteam/.env && set +a
```

1. **Commit Test Contracts First**: Commit failing unit/invariant tests before `--worktree` so `--read-files` passes preflight (avoids exit `14`).
2. **Pass 1 — Dispatch in Isolated Worktree**:
   ```bash
   python3 ~/.gemini/config/skills/aider-deepseek/scripts/aider_bridge.py dispatch \
     --task-id "<task_id>" --worktree --no-auto-merge \
     --files <explicit_editable_files> \
     --read-files <locked_tests_or_specs> \
     --test-cmd "uv run pytest -m 'not integration' <test_file>" \
     --message "<Concrete spec. Zero unrelated edits.>"
   ```
   - **Prompts Containing Backticks**: `aider_bridge.py` accepts `--message` (no `--message-file` flag); load backticked prompts with a single-quoted heredoc (`MSG=$(cat <<'EOF' ... EOF)`) and pass `--message "$MSG"`.
   - **Cost Guards**: `aider_bridge.py` automatically shields `data/`, `*.json`, `uv.lock`, and unrequested files `>100` KB, and trips `--max-context-kb` (default `256`) before calling DeepSeek.
   - **Interactive Questions (Exit `10`)**: Run `aider_bridge.py inspect --task-id "<task_id>" --json`, then `aider_bridge.py reply --task-id "<task_id>" --answer "..."`.
3. **Pass 2 — Risk-Gated Self-Review (`--restore`)**: Run Pass 2 **only** for high-risk changes (AST/parsers, canonical hashing, concurrency/locks, breaking API changes, or `>150` LOC); skip on small fixes, scaffolds, and docs when `ruff` + `pytest` pass:
   ```bash
   python3 ~/.gemini/config/skills/aider-deepseek/scripts/aider_bridge.py turn \
     --task-id "<task_id>" --restore --worktree --no-auto-merge \
     --files <explicit_editable_files> \
     --read-files <locked_tests_or_specs> \
     --message "PASS 2 CODE REVIEW: Verify scope adherence, deterministic hashing/AST edge cases, type hints, and zero unrelated edits."
   ```
4. **Locked Merge THEN Cleanup**: Only after all verification gates pass, run:
   ```bash
   python3 ~/.gemini/config/skills/aider-deepseek/scripts/aider_bridge.py merge-worktree --task-id "<task_id>"
   python3 ~/.gemini/config/skills/aider-deepseek/scripts/aider_bridge.py cleanup --task-id "<task_id>"
   ```

---

## 4. Verification Gates

```bash
uv run pytest -v -m "not integration"   # Fast unit & invariant suite
uv run ruff check src tests             # Lint check
```
