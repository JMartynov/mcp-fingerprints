# Task 100: Advanced Filtering, Change-Type Badge Pills, Search, Sorting & URL State Sync on `web/updates.html` and `web/updates.js`

- **Target Repository:** [`JMartynov/mcp-fingerprints`](https://github.com/JMartynov/mcp-fingerprints)
- **Target Files:** `web/updates.html`, `web/updates.js`, `web/style.css`, `tests/test_web_catalog.py`, `tests/test_web_pwa_e2e.py`

## 1. Objective
Upgrade the Sync Updates page (`web/updates.html` & `web/updates.js`) with a real-time search bar, interactive change-type badge filter pills (`New Server`, `New Version`, `+Tools Added`, `Params Updated`) with live counts, an ecosystem filter, a `Verified Only` toggle, multi-criteria sorting, a `Reset Filters` action, and full URL query parameter synchronization (`?release=`, `?q=`, `?badge=`, `?eco=`, `?tools=`, `?verified=`, `?sort=`).

## 2. Requirements & Technical Specification

### A. Search Bar (`#updateSearchInput` + `?q=`)
- Add `<input type="search" id="updateSearchInput" placeholder="Search updated servers, tools, descriptions, or commands..." autocomplete="off" enterkeyhint="search" />` in `web/updates.html`.
- Real-time filtering across `server.name`, `server.description`, `server.command`, and `server.tools` (`t.name`, `t.desc`, `t.description`).
- Support scoped prefixes `tool:<term>` and `min-tools:<N>` consistently with `index.html`.

### B. Interactive Change-Type Badge Filter Pills (`.badge-filter-btn` + `?badge=`)
Add a row of filter pills in `web/updates.html` with live counts calculated from the currently loaded release (`updateData`):
- `all` ("All Updates")
- `new-server` ("New Server") — matches `server.badges.includes("NEW SERVER")`
- `new-version` ("New Version") — matches `server.badges.includes("NEW VERSION")`
- `tools-added` ("+Tools Added") — matches `server.badges.some(b => b.includes("TOOLS ADDED"))`
- `params-updated` ("Params Updated") — matches `server.badges.includes("PARAMETERS UPDATED")`

### C. Ecosystem Filter (`#updateEcoSelect` + `?eco=`) & Checkboxes
- Add `<select id="updateEcoSelect">` with options: `all` ("All Ecosystems"), `npm` ("NPM"), `pypi` ("PyPI"), `github` ("GitHub"), `golang` ("Go"), `generic` ("Generic").
- Preserve `#filterToolsOnly` ("Has Tools Only", `?tools=1`).
- Add `#filterVerifiedOnly` ("Verified Only", `?verified=1`) filtering `Boolean(server.is_verified)`.
- Add `#resetUpdateFiltersBtn` ("Reset Filters") to clear search, badge filter, ecosystem filter, checkboxes, and sort back to defaults.

### D. Sorting on `updates.html` (`#updateSortSelect` + `?sort=`)
Add `<select id="updateSortSelect">` with options:
- `default` ("Default (New Servers & Most Tools)"): Sorts servers with `"NEW SERVER"` badge first, then by `tools.length` descending, then `name` A→Z.
- `tools-added-desc` ("Most Tools Added (Δ ↓)"): Extracts numeric delta from `"+N TOOLS ADDED"` badge (or `tools.length` if `"NEW SERVER"`), sorting descending, tie-broken by `tools.length` desc.
- `tools-desc` ("Total Tools (↓)"): Sort by `(server.tools ? server.tools.length : 0)` descending, then `name` A→Z.
- `tools-asc` ("Fewest Tools (↑)"): Sort by `(server.tools ? server.tools.length : 0)` ascending, then `name` A→Z.
- `name-asc` ("Name (A → Z)"): Alphabetical `a.name.localeCompare(b.name)`.
- `name-desc` ("Name (Z → A)"): Reverse alphabetical `b.name.localeCompare(a.name)`.

### E. Bidirectional URL State & E2E Tests
- Sync `?release=`, `?q=`, `?badge=`, `?eco=`, `?tools=1`, `?verified=1`, and `?sort=` with `URLSearchParams` via `history.replaceState`.
- Update `#metricsDisplay` on `updates.html` to show filtered vs total count: e.g. `<strong>v${currentRelease}</strong> &mdash; Showing <strong>${displayServers.length}</strong> of <strong>${updateData.length}</strong> servers updated in this release.`
- Add Playwright E2E test coverage in `tests/test_web_pwa_e2e.py` verifying both `index.html` sorting/filtering/URL state and `updates.html` badge filtering/search/sorting.
