with open("web/app.js", "r") as f:
    content = f.read()

# Make the empty state match the required empty state badge
old_empty = """    toolsPreviewHtml = `
      <div class="tools-section">
        <div class="tools-label">Tools</div>
        <div style="font-size:0.8rem; color:var(--text-dim); margin-top:0.25rem;">No static tools declared for v${escapeHtml(activeVer)}</div>
      </div>
    `;"""

new_empty = """    toolsPreviewHtml = `
      <div class="tools-section">
        <div class="tools-label">Tools (0)</div>
        <div class="no-tools-badge">No static tools declared (Remote Endpoint / Gateway)</div>
      </div>
    `;"""

if old_empty in content:
    content = content.replace(old_empty, new_empty)
else:
    print("WARNING: Could not find empty tools block")

# Add filter event listener
old_events = """    });
  });

  document.getElementById("searchInput").addEventListener("input", (e) => {
    activeQuery = e.target.value;
    updateFilters();
  });
}"""

new_events = """    });
  });

  document.getElementById("searchInput").addEventListener("input", (e) => {
    activeQuery = e.target.value;
    updateFilters();
  });

  document.getElementById("filterToolsOnly")?.addEventListener("change", (e) => {
    updateFilters();
  });
}"""

if old_events in content:
    content = content.replace(old_events, new_events)
else:
    print("WARNING: Could not find events block")

# Update updateFilters
old_filter = """function updateFilters() {
  const query = activeQuery.toLowerCase().trim();

  filteredCatalog = catalog.filter((item) => {"""

new_filter = """function updateFilters() {
  const query = activeQuery.toLowerCase().trim();
  const filterToolsOnly = document.getElementById("filterToolsOnly")?.checked;

  filteredCatalog = catalog.filter((item) => {
    if (filterToolsOnly) {
      const activeVer = getActiveVersionForServer(item);
      const vData = getVersionData(item, activeVer);
      const tools = vData.tools || [];
      if (tools.length === 0) return false;
    }"""

if old_filter in content:
    content = content.replace(old_filter, new_filter)
else:
    print("WARNING: Could not find filter logic")

with open("web/app.js", "w") as f:
    f.write(content)
