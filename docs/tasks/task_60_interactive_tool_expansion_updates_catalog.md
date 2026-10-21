# Task Contract: Task 60 — Interactive Tool Expansion, Zero-Tool State, and Page Rework across Updates and Catalog Web Pages

## 1. Problem Statement & User Impact
On the web UI:
1. On `https://jmartynov.github.io/mcp-fingerprints/updates.html`, cards for servers with more than 5 tools show a static `+N more` badge (e.g. `+ 4 more` on `@ai-by-design/primitiv`). Clicking this badge does nothing — it is an unclickable `<span>` without any click handler.
2. Servers with 0 tools (such as remote endpoints, gateways, or client packages like `ai.arihaan/jobs`, `ai.askgina/perps`, `@juspay/neurolink`) render with an empty blank space in the card body where the tools section normally appears. This creates inconsistent card heights, visual voids, and leaves users unsure whether tools are missing or failed to load.
3. Individual tool tags on `updates.html` lack click handlers to open parameter inspection.
4. Users cannot filter out servers with 0 tools on `updates.html` or `index.html` when looking specifically for callable MCP tools.

## 2. Requirements & Deliverables

### A. Updates Page Rework (`web/updates.js`, `web/updates.html`, `web/style.css`)
1. **Interactive Tool Tag Expansion (`+N more` / `Show less ▴`)**:
   - Track expanded tool states per server (e.g., `Set` of server names or IDs `expandedServers`).
   - Render `+N more` using class `.tool-tag-more` with `role="button"`, `tabindex="0"`, and click/keyboard event handler `toggleToolsExpand('${safeName}')`.
   - When clicked, expand to display all tools for that server inline in `.tool-tags`, followed by a `Show less ▴` button chip (`.tool-tag-more`) that collapses back to 5 tools.
   - Individual tool tags (`.tool-tag`) must be clickable with `onclick="openInspectorModal('${safeName}', '${safeToolName}')"` or `title` tooltips, opening the inspector modal with that tool highlighted.
2. **Informative Empty Tools State**:
   - When `server.tools` is empty (`tool_count === 0` or missing):
     Do NOT render an empty blank space. Instead render:
     ```html
     <div class="tools-section">
       <div class="tools-label">Tools (0)</div>
       <div class="no-tools-badge">No static tools declared (Remote Endpoint / Gateway)</div>
     </div>
     ```
   - Style `.no-tools-badge` in `web/style.css` (subtle border, dimmed text, readable padding).
3. **Filter Controls**:
   - In `web/updates.html`, add a filter toggle / checkbox next to release selector:
     `<label class="filter-checkbox"><input type="checkbox" id="filterToolsOnly"> Has Tools Only</label>`
   - When checked, only servers with `tool_count > 0` (or `tools.length > 0`) are displayed in the grid.
4. **Rich Tool Drawer Parity (`.inline-tool-drawer`)**:
   - Provide an "Explore Tools ▾" / "Hide Tools ▴" toggle button in `tools-label` / `tools-section` matching `web/app.js`, enabling searching and filtering across tools for large servers.

### B. Catalog Page Parity (`web/app.js`, `web/index.html`)
1. **Tool Tag Expansion**:
   - Verify that clicking `+N more` in `web/app.js` opens the tool drawer or expands tags smoothly without console errors.
   - Ensure clean empty-state messaging when `tools.length === 0`.
   - Ensure the "Has Tools Only" filter operates correctly in conjunction with existing ecosystem and transport filters.

### C. Styling & Accessibility (`web/style.css`)
1. Ensure `.tool-tag-more` has hover states, smooth transitions, and keyboard accessibility (`Enter` and `Space` key support).
2. Ensure responsive wrapping on mobile displays.
3. Ensure no text overlap or layout shifts.

### D. Automated Verification & Acceptance Tests (`tests/test_web_catalog.py`)
1. Add tests in `tests/test_web_catalog.py`:
   - Test that `updates.js` contains `tool-tag-more` and `toggleToolsExpand` or `toggleToolDrawer`.
   - Test that `updates.js` handles zero-tool servers with `.no-tools-badge` or explicit empty state.
   - Test that tool tags have click handlers linking to inspection.
   - Test HTML validation for `updates.html` and `index.html`.
   - Validate JS syntax using a node syntax check or regex AST verification.

## 3. Non-Interactive Completion Directive
This task is dispatched to Google Jules (EULIS) for non-interactive execution.
Implement the full feature, ensure all unit tests pass (`python -m pytest tests/test_web_catalog.py -q`), update docs, and cleanly commit changes. Do not ask interactive questions; conclude with complete patch.
