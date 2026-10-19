# Task: Multi-Agent Configurable MCP Discovery, Generic MCP Detection, Auto-Passport Generation, and Workstation Drift Tracking

## 1. Context & Objectives
Extend `mcp-fingerprints` to comprehensively discover, detect, fingerprint, and track MCP servers across developer workstations and multiple AI coding agents, operating systems, and transports:
1. **Configurable Multi-Agent Registry across macOS, Linux, and Windows**:
   - Provide built-in support for all major AI coding agents: Claude Desktop, Claude Code (`~/.claude.json`, `.mcp.json`), Cursor, Windsurf, Zed, Cline, Roo Code, Goose, Continue.dev, JetBrains Junie, VS Code / GitHub Copilot (`mcp.json`), Antigravity (`~/.gemini/config/mcp_config.json`), OpenHands, Trae, LM Studio.
   - Support multiple OSs (`darwin`, `linux`, `win32`) dynamically resolving home directory, `$APPDATA`, `$USERPROFILE`, `$XDG_CONFIG_HOME`.
   - Support all schema dialects:
     - Standard dictionary: `{"mcpServers": {<name>: {command, args, env, url}}}`
     - Claude Code: top-level `mcpServers` AND per-project `projects[<path>].mcpServers`
     - Zed: `{"context_servers": {<name>: {"command": {"path": ..., "args": ..., "env": ...}}}}`
     - VS Code / Copilot: `{"servers": {<name>: {"type": ..., "command": ...}}}` or `{"mcpServers": ...}`
     - Goose: YAML with `extensions: {<name>: {cmd, args, envs, uri, type}}`
     - Continue.dev: YAML/JSON list of objects: `mcpServers: [{"name": ..., "command": ...}]`
   - Make client paths and definitions configurable via Python API (`ClientRegistry.register()`, `ClientRegistry.load_custom_config()`) and CLI options (`--client <name>`, `--config-file <path>`, `--custom-clients <path>`).

2. **Generic MCP Detection (`detect_mcp` / `src/mcp_fingerprints/detector.py`)**:
   - Generic function and CLI subcommand (`mcp-fingerprints detect`) to determine if any arbitrary process command or URL is an MCP server.
   - Detect transport (`stdio`, `http`, `sse`).
   - Active JSON-RPC 2.0 handshake (`initialize` method) with configurable timeout (default 3.0s).
   - Verify `serverInfo` and `capabilities` in response.
   - Return structured report: `is_mcp: bool`, `transport: str | None`, `server_info: dict`, `capabilities: dict`, `error: str | None`.

3. **Auto-Passport Generation & Local Database Storage**:
   - Option `--auto-passport` during `scan` or `probe`: if an MCP server (such as CodeScene) does not exist in `data/fingerprints/`, probe its tools (`tools/list`), build a valid `ServerPackageSpec` passport matching repository invariants, and save it to `data/fingerprints/<server_name>.json`.

4. **Workstation Environment Snapshot & Drift Tracking**:
   - `mcp-fingerprints scan --save-baseline <path>`: serializes the complete workstation inventory of discovered servers, clients, and live probe signatures into a baseline JSON file.
   - `mcp-fingerprints scan --diff <baseline_path>`: diffs the current live workstation scan against the saved baseline. Reports:
     - Added servers
     - Removed servers
     - Configuration drift (command line, arguments, environment variable changes)
     - Tool signature drift (tools added, tools removed, parameter schema changes)
   - Supports human-readable output and `--format json`.

5. **CLI & Documentation**:
   - Update `src/mcp_fingerprints/cli.py` to support `--client`, `--config-file`, `--custom-clients`, `--save-baseline`, `--diff`, `--auto-passport`, and add `detect` subcommand.
   - Update `README.md` to document the new features, supported agents, detection commands, and drift tracking workflows.

6. **Comprehensive Unit Tests**:
   - Add unit tests for all client dialects (Claude Code, Zed, Goose, Continue, VS Code), multi-OS path resolution, detector handshake mocks, auto-passport generation, and baseline diff/drift comparison.

## 2. Strict Guardrails:
- Zero Unauthorized Dependencies: Use Python standard library and existing repo dependencies (`pyyaml`, `packaging`, `tenacity`).
- Unit Test Mocking Mandate: Do not perform live network calls or run external Docker commands during tests; mock stdio subprocesses and HTTP responses.
- Maintain Invariants: All generated passports must validate against `McpServerValidator`.
- Preserve existing comments and docstrings.

## 3. Non-Interactive Completion Directive:
- Implement all requested modules, CLI options, tests, and documentation updates.
- Verify using pytest (`pytest -v`).
- Finalize your response with a concise summary of implemented changes without asking open-ended questions, so the task cleanly transitions to Completed.
