# Task 28: Web Catalog Offline PWA & Search Virtualization

### 1. Architectural Context & Technical Objective
The static web catalog (`web/`) is currently a basic vanilla JS implementation. As the catalog grows to hundreds or thousands of fingerprints, DOM rendering can become slow. Furthermore, offline access is not supported.
The objective is to implement a Progressive Web App (PWA) Service Worker to cache the static catalog for offline use and implement DOM virtualization (windowing) for the search results list to maintain sub-16ms rendering performance even with 10,000+ entries, adhering strictly to vanilla JS without external frameworks.

### 2. Technical Implementation Specifications
1. Create `web/sw.js` (Service Worker) to cache `index.html`, `app.js`, CSS, and the JSON catalog snapshot.
2. Update `web/index.html` to register the Service Worker.
3. Modify `web/app.js` to implement list virtualization:
   - Calculate total height based on item count.
   - Render only the subset of list items visible in the viewport plus a small buffer.
   - Use absolute positioning within a scrollable container.
4. Ensure the `scripts/generate_web_catalog.py` includes a mechanism to inject the current cache version into `sw.js` to trigger updates.

### 3. Clear Acceptance Criteria
- [ ] Service worker (`sw.js`) successfully caches the web catalog.
- [ ] The web catalog is accessible offline.
- [ ] `app.js` utilizes DOM virtualization for search results.
- [ ] Vanilla JS is maintained; no React/Vue/Svelte dependencies.

### 4. Unit Test Plan
1. **Virtualization Logic:** Unit test the index calculation functions (e.g., `getVisibleRange(scrollTop, containerHeight, itemHeight)`) in a standard JS test runner (or via Playwright evaluating functions) to ensure accurate start and end indices are returned.
2. **Service Worker Versioning:** Test that `generate_web_catalog.py` correctly updates the cache version string in `sw.js` when generating the site.

### 5. Live Acceptance Test Plan
Use `uv run python scripts/generate_web_catalog.py`. Start a local HTTP server (`python -m http.server -d web`). Open the browser, verify virtualization by inspecting the DOM (only a few elements should exist). Disconnect the server (stop script), refresh the page, and verify it still loads offline via the Service Worker. Finally, use Playwright frontend verification instructions to capture a screenshot of the catalog rendering correctly.
