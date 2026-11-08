# Task 99: Advanced Multi-Facet Filtering, Scoped Search Operators, Sorting & URL State Sync on `web/index.html` and `web/app.js`

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `web/index.html`, `web/app.js`, `web/style.css`, `tests/test_web_catalog.py`, `tests/test_web_pwa_e2e.py`

## 1. Objective
Upgrade the main MCP Server Passports Directory (`web/index.html` & `web/app.js`) with multi-criteria sorting, transport & capability facet filters, live ecosystem badge counts, scoped search operators (`tool:`, `param:`, `author:`, `license:`, `env:`, `min-tools:`), a one-click `Reset Filters` button, and full bidirectional URL query parameter synchronization.

## 2. Requirements & Technical Specification

### A. Multi-Criteria Sorting (`#sortSelect` + `?sort=`)
Add a `<label for="sortSelect">` and `<select id="sortSelect">` in `web/index.html` inside the `.controls` panel:
- `tools-desc` (Default — "Most Tools ↓"): Sort by active version `tool_count` descending (servers with `tool_count > 0` first, then `name` A→Z).
- `tools-asc` ("Fewest Tools ↑"): Sort by active version `tool_count` ascending (`tool_count > 0` first ascending, then `0` tools, tie-broken by `name` A→Z).
- `name-asc` ("Name (A → Z)"): Alphabetical `a.name.localeCompare(b.name)`.
- `name-desc` ("Name (Z → A)"): Reverse alphabetical `b.name.localeCompare(a.name)`.
- `newest` ("Recently Released ↓"): Sort by `release_date` descending (empty dates last, tie-broken by `tool_count` desc).
- `versions-desc` ("Most Versions ↓"): Sort by `(item.versions ? item.versions.length : (item.total_versions || 1))` descending, tie-broken by `tool_count` desc.
- `relevance` ("Search Relevance"): Ranks exact `name` match > `name` prefix > exact `tool.name` match > `name` substring > `tool.name` substring > description/parameter match.

### B. Facet Filters & Live Ecosystem Counts
1. **Ecosystem Pills (`.filter-btn[data-filter="eco"]`, `?eco=`)**:
   - Dynamically compute and display the count of matching servers per ecosystem (`All`, `NPM`, `PyPI`, `GitHub`, `Go`, `Generic`) based on current non-ecosystem filters (search, transport, checkboxes), e.g., `GitHub (1,420)` or via a `<span class="filter-count">` inside each button while keeping `data-val` intact.
2. **Transport Filter (`#transportSelect`, `?transport=`)**:
   - `<select id="transportSelect">` with options:
     - `all` ("All Transports")
     - `stdio` ("stdio (Local)") — matches when `vData.transports` includes `"stdio"` or `item.connection_type === "stdio"`
     - `sse` ("SSE / HTTP (Remote)") — matches when `vData.transports` includes `"sse"` or `"http"` or `"streamable-http"` or `item.connection_type === "sse"`
3. **Quick-Toggle Checkboxes**:
   - `#filterToolsOnly` ("Has Tools Only", `?tools=1`) — existing ID preserved!
   - `#filterVerifiedOnly` ("Verified Only", `?verified=1`) — filters `Boolean(item.is_verified)`.
   - `#filterZeroConf` ("No API Keys Needed", `?zeroconf=1`) — filters `(!vData.required_env_vars || vData.required_env_vars.length === 0)`.
   - `#filterHasExtras` ("Has Prompts/Resources", `?extras=1`) — filters `((item.prompts && item.prompts.length > 0) || (item.resources && item.resources.length > 0))`.
4. **Scoped Search Operators in `#searchInput` (`parseSearchQuery(rawQuery)`)**:
   - Parse tokens from `#searchInput`:
     - `tool:<term>` — server has a tool whose `name` contains `<term>`
     - `param:<term>` — server has a tool parameter whose `name` contains `<term>`
     - `author:<term>` — `item.author` contains `<term>`
     - `license:<term>` — `item.license` contains `<term>`
     - `env:<term>` — `vData.required_env_vars` has a var containing `<term>`
     - `min-tools:<N>` — `vData.tools.length >= Number(N)`
     - Remaining free-text tokens match across `name`, `description`, `author`, `tools[].name`, `tools[].description`, and `parameters[].name`.
5. **Reset Filters Button (`#resetFiltersBtn`)**:
   - Resets search, ecosystem (`all`), transport (`all`), all checkboxes, and sort (`tools-desc`), updates URL state, and re-renders.
   - Keyboard shortcut: pressing `/` when not focused inside an `<input>`, `<textarea>`, or `<select>` focuses `#searchInput`.

### C. Bidirectional URL State (`updateURLState()` & `initFromURL()`)
Sync `q`, `eco`, `transport`, `tools`, `verified`, `zeroconf`, `extras`, and `sort` with `URLSearchParams` via `history.replaceState`.
**CRITICAL**: Preserve all existing DOM IDs and classes (`#searchInput`, `.filter-btn[data-val='...']`, `#filterToolsOnly`, `#metricsDisplay`, `#serverGrid`, `#inspectorModal`) so all existing Playwright E2E and unit tests pass without regression.
In `#metricsDisplay`, continue rendering the exact substring `"MCP servers"` (e.g., `Showing <strong>X</strong> of <strong>Y</strong> verified MCP servers`).
