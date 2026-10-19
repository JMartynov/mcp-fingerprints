# Task 48: Interactive MCP Command Hub (`mcp-fingerprints interactive`) with Emoji-Decorated Ergonomic Menus, JSON Baseline Comparison & Extensible Action Registry

## 1. Context & Objectives
Developers and security engineers need an intuitive, ergonomic, and interactive terminal utility to discover, probe, search, and track MCP servers on their workstations without memorizing complex CLI flags.

Implement the Interactive MCP Command Hub (`src/mcp_fingerprints/hub.py` and CLI subcommand `interactive`):

1. **Context-Aware Status Header**:
   - On launch, displays a clean Rich/terminal status banner:
     - Current OS (macOS / Linux / Windows)
     - Detected AI coding clients (Claude Code, Claude Desktop, Cursor, Windsurf, Zed, etc.)
     - Total configured MCP servers found
     - Baseline status (Saved / Modified / Not initialized)

2. **Emoji-Decorated Categorized Menu Hierarchy**:
   Implement a clean interactive navigation loop with visual anchor emojis:
   - **🖥️ 1. Workstation Discovery & Inventory**:
     - `🔍 Scan All Local AI Agents` (runs multi-agent config scanner)
     - `🎯 Scan Specific Agent...` (prompts for agent selection)
     - `💾 Save Current State as Baseline JSON` (saves to `workstation_baseline.json`)
     - `⚖️ Diff Against Previous Baseline` (compares current scan vs saved baseline, highlighting added/removed servers and tool drift)
   - **🌐 2. Search Ready Database & Ingest Unknown Local MCPs**:
     - `🔤 Search Ready Database by Keyword` (prompts for keyword, instantly searches 5,000+ local passports)
     - `📥 Add Unknown MCP from Local Machine` (probes an unindexed local server like CodeScene or custom script, extracts tools, and saves passport to `data/fingerprints/`)
     - `📚 Browse Catalog Passports` (paginated interactive passport browser)
   - **🧪 3. Live Prober & Generic MCP Detector**:
     - `🔬 Detect if Command/URL is an MCP Server` (prompts for command or URL, performs JSON-RPC handshake)
     - `🩺 Deep Live Server Probe` (full schema & tool extraction)
     - `🏷️ Auto-Generate & Save Passport` (writes valid passport to `data/fingerprints/`)
   - **⚙️ 4. Performance, Cache & System**:
     - `⚡ View Cache & Benchmark Stats` (displays cache hit rate and timings)
     - `🧹 Clear Validation / Passport Cache`
     - `⏱️ Inspect Active Checkpoints & Time Budgets`
   - **🚪 5. Exit**

3. **1-Click JSON Export & Differential Comparison**:
   - After running scans or probes, offer immediate follow-up options:
     - Display formatted table
     - Save results to JSON file
     - Compare with previous run (prints added, removed, and drifted servers/tools)

4. **Extensible Action Registry Pattern**:
   - Implement an extensible dispatcher:
     ```python
     class ActionRegistry:
         def register(self, category: str, emoji: str, title: str, handler: callable, order: int = 0):
             ...
     ```
   - Allows existing and future capabilities to be plugged in seamlessly.

5. **CLI Integration & Graceful Fallbacks**:
   - Add `mcp-fingerprints interactive` subcommand (alias `mcp-fingerprints hub`).
   - If `mcp-fingerprints` is run with no arguments in an interactive terminal (`sys.stdin.isatty()`), launch the interactive hub by default instead of printing bare help.
   - Non-interactive / CI safety: if invoked without a TTY, output clear help and exit cleanly.
   - Graceful handling of `Ctrl+C` (`KeyboardInterrupt`) and `Ctrl+D` (`EOFError`).

6. **Testing & Invariants**:
   - Unit tests in `tests/test_hub.py`:
     - Test menu navigation and handler routing using simulated/mocked user inputs.
     - Test non-TTY graceful fallback.
     - Test baseline save and diff action workflow.
     - Test action registry extensibility.
   - Zero unauthorized dependencies: use standard library, existing dependencies (`pyyaml`), and `rich` / `questionary` if available or lightweight standard ANSI/prompt fallback.

## 2. Strict Guardrails:
- Non-interactive completion directive: Implement all code and tests, verify with `pytest -v`, and finalize with a concise summary without open-ended questions.
