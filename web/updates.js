const serverGrid = document.getElementById('serverGrid');
const metricsDisplay = document.getElementById('metricsDisplay');
const releaseSelect = document.getElementById('releaseSelect');

let currentRelease = null;
let updateData = [];

// Initialize
async function init() {
  await loadHistory();
}

async function loadHistory() {
  try {
    const res = await fetch('updates/updates_history.json');
    if (!res.ok) throw new Error('History not found');
    const history = await res.json();
    
    releaseSelect.innerHTML = '';
    history.forEach((h, index) => {
      const opt = document.createElement('option');
      opt.value = h.version;
      opt.textContent = `v${h.version} (${h.count} updates)`;
      releaseSelect.appendChild(opt);
    });
    
    if (history.length > 0) {
      loadRelease(history[0].version);
    } else {
      metricsDisplay.textContent = 'No updates available.';
    }
  } catch (err) {
    console.error('Failed to load history', err);
    metricsDisplay.textContent = 'Failed to load update history.';
    releaseSelect.innerHTML = '<option value="">No releases found</option>';
  }
}

releaseSelect.addEventListener('change', (e) => {
  if (e.target.value) {
    loadRelease(e.target.value);
  }
});

async function loadRelease(version) {
  currentRelease = version;
  metricsDisplay.textContent = `Loading v${version}...`;
  serverGrid.innerHTML = '';
  
  try {
    const res = await fetch(`updates/v${version}.json`);
    if (!res.ok) throw new Error('Release data not found');
    updateData = await res.json();
    
    metricsDisplay.innerHTML = `<strong>v${version}</strong> &mdash; ${updateData.length} servers updated in this release.`;
    renderGrid(updateData);
  } catch (err) {
    console.error(err);
    metricsDisplay.textContent = `Failed to load v${version}.`;
  }
}

function renderGrid(servers) {
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
    }

    let repoHtml = '';
    if (server.repository_url) {
      repoHtml = `<a href="${server.repository_url}" target="_blank" style="color: var(--accent); text-decoration: none; font-size: 0.85rem;">View Repository ↗</a>`;
    }
    
    let badgesHtml = server.badges.map(b => {
      let cssClass = 'badge-new-server';
      if (b === 'NEW VERSION') cssClass = 'badge-new-version';
      else if (b.includes('TOOLS ADDED')) cssClass = 'badge-tools-added';
      else if (b === 'PARAMETERS UPDATED') cssClass = 'badge-params-updated';
      return `<span class="update-badge ${cssClass}">${b}</span>`;
    }).join('');


    card.innerHTML = `
      <div class="update-badges">${badgesHtml}</div>
      <div class="card-header">
        <div>
          <div class="card-title" style="cursor:pointer; text-decoration:underline; color:var(--accent);" onclick="event.stopPropagation(); openInspectorModal('${server.name.replace(/'/g, "\'")}')">${escapeHtml(server.name)}</div>
          <div class="card-meta">
            <span class="badge badge-eco">${escapeHtml(server.ecosystem)}</span>
            <span class="badge badge-version">v${escapeHtml(server.version)}</span>
            ${server.is_verified ? '<span class="badge badge-verified">✓ Verified</span>' : ''}
          </div>
        </div>
      </div>
      <div class="card-desc">${escapeHtml(server.description || 'No description provided.')}</div>
      ${toolsHtml}
      <div style="margin-top: auto; padding-top: 1rem; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
        ${repoHtml}
        <div style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted); background: #0f172a; padding: 0.2rem 0.4rem; border-radius: 4px; border: 1px solid var(--border);">
          ${escapeHtml(server.command || '')}
        </div>
      </div>
    `;

    serverGrid.appendChild(card);
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

init();

// Allow interaction for opening the config modal
document.body.addEventListener('click', (e) => {
  // If they click on a card... (except links and copy buttons)
  if (e.target.closest('.card') && !e.target.closest('a') && !e.target.closest('.btn-copy')) {
    const card = e.target.closest('.card');
    card.classList.toggle('selected');
    if (card.classList.contains('selected')) {
      card.style.borderColor = 'var(--accent)';
      card.style.boxShadow = '0 0 10px rgba(56, 189, 248, 0.3)';
    } else {
      card.style.borderColor = '';
      card.style.boxShadow = '';
    }
    updateBottomDrawer();
  }
});

function updateBottomDrawer() {
  const selected = document.querySelectorAll('.card.selected');
  const drawer = document.getElementById('bottomDrawer');
  const countSpan = document.getElementById('selectedCount');
  
  if (selected.length > 0) {
    countSpan.textContent = selected.length;
    drawer.classList.add('show');
  } else {
    drawer.classList.remove('show');
  }
}

// Ensure openConfigModal is defined in this file (copying behavior from app.js)
window.openConfigModal = function() {
  const selectedCards = document.querySelectorAll('.card.selected');
  const collisionWarning = document.getElementById('collisionWarning');
  const collisionList = document.getElementById('collisionList');
  collisionList.innerHTML = '';
  
  const allTools = new Set();
  const collisions = new Set();
  const servers = [];
  
  selectedCards.forEach(card => {
    const name = card.querySelector('.card-title').textContent.trim();
    const command = card.querySelector('div[style*="font-family: monospace"]').textContent.trim();
    const toolTags = card.querySelectorAll('.tool-tag:not([style*="dashed"])'); // only actual tool tags
    
    servers.push({ name, command });
    
    toolTags.forEach(tag => {
      const toolName = tag.textContent;
      if (allTools.has(toolName)) {
        collisions.add(toolName);
      }
      allTools.add(toolName);
    });
  });
  
  if (collisions.size > 0) {
    collisionWarning.classList.add('show');
    collisions.forEach(c => {
      const li = document.createElement('li');
      li.textContent = c;
      collisionList.appendChild(li);
    });
  } else {
    collisionWarning.classList.remove('show');
  }
  
  // Expose selected servers to the global scope for the switchTab function
  window.selectedServers = servers;
  
  document.getElementById('configModal').classList.add('show');
  switchTab('claude'); // render the active tab
}

window.closeConfigModal = function() {
  document.getElementById('configModal').classList.remove('show');
}

window.switchTab = function(client) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelector(`.tab-btn[data-client="${client}"]`).classList.add('active');
  
  const servers = window.selectedServers || [];
  let code = '';
  
  if (client === 'claude') {
    const config = { mcpServers: {} };
    servers.forEach(s => {
      const parts = s.command.split(' ');
      const cmd = parts[0];
      const args = parts.slice(1);
      config.mcpServers[s.name] = { command: cmd, args: args };
    });
    code = JSON.stringify(config, null, 2);
  } else if (client === 'cursor') {
    code = "// Cursor MCP configuration\n// (This is a simplified representation as Cursor manages via UI mostly)\n" + JSON.stringify(servers, null, 2);
  } else if (client === 'cline') {
     const config = { mcpServers: {} };
    servers.forEach(s => {
      const parts = s.command.split(' ');
      const cmd = parts[0];
      const args = parts.slice(1);
      config.mcpServers[s.name] = { command: cmd, args: args };
    });
    code = JSON.stringify(config, null, 2);
  } else if (client === 'zed') {
     code = "{\n  \"mcp\": {\n    \"servers\": " + JSON.stringify(servers, null, 2) + "\n  }\n}";
  } else if (client === 'windsurf') {
      const config = { mcpServers: {} };
    servers.forEach(s => {
      const parts = s.command.split(' ');
      const cmd = parts[0];
      const args = parts.slice(1);
      config.mcpServers[s.name] = { command: cmd, args: args };
    });
    code = JSON.stringify(config, null, 2);
  } else if (client === 'docker') {
    code = "version: '3'\nservices:\n";
    servers.forEach(s => {
      code += `  ${s.name.replace(/[^a-zA-Z0-9]/g, '_')}:\n    image: node:18\n    command: ${s.command}\n`;
    });
  }
  
  document.getElementById('configOutput').textContent = code;
}

window.copyCombinedConfig = function() {
  const code = document.getElementById('configOutput').textContent;
  navigator.clipboard.writeText(code).then(() => {
    const toast = document.getElementById('toast');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  });
}

window.downloadCombinedConfig = function() {
  const code = document.getElementById('configOutput').textContent;
  const blob = new Blob([code], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'config.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}


// --- Interactive Server & Tool Parameter Inspector ---
window.openInspectorModal = function(serverName) {
  const item = updateData.find((i) => i.name === serverName);
  if (!item) return;

  document.getElementById("inspectorTitle").innerText = item.name;
  const body = document.getElementById("inspectorBody");

  let html = `<div class="inspector-header-info">`;

  if (item.repository_url) {
    html += `<div class="inspector-meta-item"><strong>Repo:</strong> <a href="${item.repository_url}" target="_blank">${item.repository_url}</a></div>`;
  }
  if (item.homepage_url) {
    html += `<div class="inspector-meta-item"><strong>Home:</strong> <a href="${item.homepage_url}" target="_blank">${item.homepage_url}</a></div>`;
  }
  if (item.author) {
    html += `<div class="inspector-meta-item"><strong>Author:</strong> ${item.author}</div>`;
  }
  if (item.license) {
    html += `<div class="inspector-meta-item"><strong>License:</strong> ${item.license}</div>`;
  }
  if (item.version) {
    html += `<div class="inspector-meta-item"><strong>Version:</strong> ${item.version}</div>`;
  }
  if (item.required_env_vars && item.required_env_vars.length > 0) {
    html += `<div class="inspector-meta-item"><strong>Required Env:</strong> ${item.required_env_vars.join(", ")}</div>`;
  }

  html += `</div>`; // end header-info

  html += `<div style="margin-bottom: 1.5rem;">${escapeHtml(item.description || "No description available.")}</div>`;

  // Tools
  if (item.tools && item.tools.length > 0) {
    html += `<h3 style="margin-bottom: 1rem; color: var(--text);">Tools (${item.tools.length})</h3>`;
    item.tools.forEach((tool) => {
      html += `<div class="tool-detail-card">
            <div class="tool-detail-title">${escapeHtml(tool.name)}</div>
            <div class="tool-detail-desc">${escapeHtml(tool.description || tool.desc || "No description provided.")}</div>`;

      if (tool.parameters && tool.parameters.length > 0) {
        html += `<table class="schema-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Required</th>
                  <th>Default</th>
                  <th>Enum</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>`;
        tool.parameters.forEach((p) => {
          html += `<tr>
                <td class="param-name">${escapeHtml(p.name)}</td>
                <td>${escapeHtml(p.type || "")}${p.items_type ? ` of ${escapeHtml(p.items_type)}` : ""}</td>
                <td>${p.required ? "Yes" : "No"}</td>
                <td>${p.default !== undefined && p.default !== null ? escapeHtml(JSON.stringify(p.default)) : ""}</td>
                <td>${p.enum ? escapeHtml(p.enum.join(", ")) : ""}</td>
                <td>${escapeHtml(p.description || "")}</td>
              </tr>`;
        });
        html += `</tbody></table>`;
      } else {
        html += `<div style="font-size: 0.85rem; color: var(--text-muted);">No parameters defined.</div>`;
      }
      html += `</div>`;
    });
  }

  // Prompts
  if (item.prompts && item.prompts.length > 0) {
    html += `<h3 style="margin-bottom: 1rem; color: var(--text); margin-top: 2rem;">Prompts (${item.prompts.length})</h3>`;
    item.prompts.forEach((p) => {
      html += `<div class="tool-detail-card">
            <div class="tool-detail-title">${escapeHtml(p.name)}</div>
            <div class="tool-detail-desc">${escapeHtml(p.description || "No description provided.")}</div>
          </div>`;
    });
  }

  // Resources
  if (item.resources && item.resources.length > 0) {
    html += `<h3 style="margin-bottom: 1rem; color: var(--text); margin-top: 2rem;">Resources (${item.resources.length})</h3>`;
    item.resources.forEach((r) => {
      html += `<div class="tool-detail-card">
            <div class="tool-detail-title">${escapeHtml(r.name || r.uri_template || "Unnamed Resource")}</div>
            <div class="tool-detail-desc">${escapeHtml(r.description || "No description provided.")}</div>
            ${r.uri_template ? `<div style="font-size:0.85rem; color:var(--text-muted);">URI Template: <code>${escapeHtml(r.uri_template)}</code></div>` : ""}
          </div>`;
    });
  }

  body.innerHTML = html;
  document.getElementById("inspectorModal").classList.add("show");
}

window.closeInspectorModal = function() {
  document.getElementById("inspectorModal").classList.remove("show");
}

// Close modal if clicked outside of content
window.addEventListener("click", function(event) {
  const modal = document.getElementById("inspectorModal");
  if (event.target == modal) {
    closeInspectorModal();
  }
  const configModal = document.getElementById("configModal");
  if (event.target == configModal) {
    closeConfigModal();
  }
});
