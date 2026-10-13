# Task 26: Interactive Terminal Setup Wizard (`mcp-fingerprints init`)

### 1. Architectural Context & Technical Objective
While `mcp_fingerprints.cli` provides powerful commands, onboarding new users requires them to manually configure their environments or learn complex flags. 
The objective is to implement a robust, interactive setup wizard (`mcp-fingerprints init`) that guides users through configuring their local MCP client integrations (e.g., Claude Desktop, Cursor), setting up semantic search, and bootstrapping their initial configuration file. The wizard must check `sys.stdin.isatty()` to gracefully degrade or abort in headless CI environments.

### 2. Technical Implementation Specifications
1. Add a new `init` command to `src/mcp_fingerprints/cli.py`.
2. Implement the interactive wizard in a new module: `src/mcp_fingerprints/wizard.py`.
3. Use the standard library (e.g., `input()`, `sys.stdout`) to ask users questions (e.g., "Do you want to configure Claude Desktop?", "Do you want to enable semantic search?").
4. Validate `sys.stdin.isatty()` at the start of the command. If false, raise a descriptive error or fall back to defaults.
5. Generate a default configuration file (e.g., `~/.mcp_fingerprints.toml` or similar) based on user input.

### 3. Clear Acceptance Criteria
- [ ] `mcp-fingerprints init` command exists.
- [ ] Wizard checks for interactive terminal (`sys.stdin.isatty()`).
- [ ] Prompts user for configurations (clients, features).
- [ ] Writes a configuration file based on the interactive session.
- [ ] No heavy external UI dependencies added.

### 4. Unit Test Plan
1. **Headless Environment:** Mock `sys.stdin.isatty()` to return `False` and assert the wizard raises a `RuntimeError` or exits gracefully with a message.
2. **Interactive Flow Mocking:** Use `unittest.mock.patch('builtins.input')` with `side_effect` to simulate user responses (e.g., `['y', 'n', 'y']`). Assert the correct configuration dictionary is generated.
3. **Config Write Verification:** Assert that the final configuration is written to the correct destination (mocking `open` or using a temporary directory).

### 5. Live Acceptance Test Plan
Run `uv run mcp-fingerprints init` in a real terminal. Answer the prompts interactively. Verify that the resulting configuration file is created successfully and matches your inputs. Pipe input via `echo "y" | uv run mcp-fingerprints init` to ensure non-TTY behavior handles it appropriately.
