import sys

with open("web/updates.js", "r") as f:
    content = f.read()

# Add event listeners and toggle function
if "filterToolsOnly" not in content:
    content = content.replace("});\n\nasync function loadRelease(version) {", """});

document.getElementById('filterToolsOnly')?.addEventListener('change', () => {
  renderGrid(updateData);
});

window.toggleToolsExpand = function(safeName) {
  if (expandedServers.has(safeName)) expandedServers.delete(safeName);
  else expandedServers.add(safeName);
  renderGrid(updateData);
}

async function loadRelease(version) {""")

# Update renderGrid
old_renderGrid = """function renderGrid(servers) {
  serverGrid.innerHTML = '';
  if (servers.length === 0) {
    serverGrid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 2rem; color: var(--text-muted);">No updates found for this release.</div>';
    return;
  }
  
  servers.forEach(server => {
    const card = document.createElement('div');
    card.className = 'card';
    if (server.badges.includes("NEW SERVER")) {
      card.classList.add('highlight-card');
    }
    
    let toolsHtml = '';
    if (server.tools && server.tools.length > 0) {
      const displayTools = server.tools.slice(0, 5);
      const toolTags = displayTools.map(t => `<span class="tool-tag" title="${escapeHtml(t.desc)}">${escapeHtml(t.name)}</span>`).join('');
      const moreHtml = server.tools.length > 5 ? `<span class="tool-tag" style="background:transparent; border-style:dashed;">+${server.tools.length - 5} more</span>` : '';
      toolsHtml = `
        <div class="tools-section">
          <div class="tools-label">Tools (${server.tools.length})</div>
          <div class="tool-tags">${toolTags}${moreHtml}</div>
        </div>
      `;
    }"""

new_renderGrid = """function renderGrid(servers) {
  serverGrid.innerHTML = '';
  
  let displayServers = servers;
  const filterToolsOnly = document.getElementById('filterToolsOnly')?.checked;
  if (filterToolsOnly) {
    displayServers = displayServers.filter(s => s.tools && s.tools.length > 0);
  }
  
  if (displayServers.length === 0) {
    serverGrid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 2rem; color: var(--text-muted);">No updates found for this release.</div>';
    return;
  }
  
  displayServers.forEach(server => {
    const card = document.createElement('div');
    card.className = 'card';
    if (server.badges.includes("NEW SERVER")) {
      card.classList.add('highlight-card');
    }
    const safeName = server.name.replace(/'/g, "\\\\'");
    
    let toolsHtml = '';
    if (server.tools && server.tools.length > 0) {
      const isExpanded = expandedServers.has(server.name);
      const displayTools = isExpanded ? server.tools : server.tools.slice(0, 5);
      const toolTags = displayTools.map(t => `<span class="tool-tag" title="${escapeHtml(t.desc)}" onclick="event.stopPropagation(); openInspectorModal('${safeName}', '${escapeHtml(t.name)}')">${escapeHtml(t.name)}</span>`).join('');
      
      let moreHtml = '';
      if (server.tools.length > 5) {
        if (isExpanded) {
          moreHtml = `<span class="tool-tag-more" role="button" tabindex="0" onclick="event.stopPropagation(); toggleToolsExpand('${safeName}')" onkeydown="if(event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.stopPropagation(); toggleToolsExpand('${safeName}'); }">Show less ▴</span>`;
        } else {
          moreHtml = `<span class="tool-tag-more" role="button" tabindex="0" onclick="event.stopPropagation(); toggleToolsExpand('${safeName}')" onkeydown="if(event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.stopPropagation(); toggleToolsExpand('${safeName}'); }">+${server.tools.length - 5} more</span>`;
        }
      }
      toolsHtml = `
        <div class="tools-section">
          <div class="tools-label">Tools (${server.tools.length})</div>
          <div class="tool-tags">${toolTags}${moreHtml}</div>
        </div>
      `;
    } else {
      toolsHtml = `
        <div class="tools-section">
          <div class="tools-label">Tools (0)</div>
          <div class="no-tools-badge">No static tools declared (Remote Endpoint / Gateway)</div>
        </div>
      `;
    }"""

if old_renderGrid in content:
    content = content.replace(old_renderGrid, new_renderGrid)
else:
    print("Warning: old_renderGrid not found.")

content = content.replace(
    """<div class="card-title" style="cursor:pointer; text-decoration:underline; color:var(--accent);" onclick="event.stopPropagation(); openInspectorModal('${server.name.replace(/'/g, "\\'")}')">${escapeHtml(server.name)}</div>""",
    """<div class="card-title" style="cursor:pointer; text-decoration:underline; color:var(--accent);" onclick="event.stopPropagation(); openInspectorModal('${safeName}')">${escapeHtml(server.name)}</div>"""
)

# Update openInspectorModal to take targetToolName
content = content.replace("window.openInspectorModal = function(serverName) {", "window.openInspectorModal = function(serverName, targetToolName) {")
content = content.replace(
"""      html += `<div class="tool-detail-card">
            <div class="tool-detail-title">${escapeHtml(tool.name)}</div>
            <div class="tool-detail-desc">${escapeHtml(tool.description || tool.desc || "No description provided.")}</div>`;""",
"""      const isTarget = targetToolName && tool.name === targetToolName;
      html += `<div class="tool-detail-card" ${isTarget ? 'style="border-color: var(--accent); box-shadow: 0 0 12px var(--accent-glow);"' : ''} id="tool-update-${escapeHtml(tool.name)}">
            <div class="tool-detail-title">${escapeHtml(tool.name)}</div>
            <div class="tool-detail-desc">${escapeHtml(tool.description || tool.desc || "No description provided.")}</div>`;"""
)

# Also make inspector scroll to target tool
content = content.replace(
"""  body.innerHTML = html;
  document.getElementById("inspectorModal").classList.add("show");
}""",
"""  body.innerHTML = html;
  document.getElementById("inspectorModal").classList.add("show");
  
  if (targetToolName) {
    setTimeout(() => {
      const el = document.getElementById(`tool-update-${targetToolName}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  }
}"""
)


with open("web/updates.js", "w") as f:
    f.write(content)

