function renderGrid(servers) {
  const filterToolsOnly = document.getElementById("filterToolsOnly")?.checked;
  const filterVerifiedOnly = document.getElementById("filterVerifiedOnly")?.checked;
  const pq = parseUpdateSearchQuery(activeUpdateQuery);

  const filterServer = (server) => {
    if (filterToolsOnly && (!server.tools || server.tools.length === 0)) return false;
    if (filterVerifiedOnly && !server.is_verified) return false;
    if (activeUpdateEco !== "all" && (!server.ecosystem || server.ecosystem.toLowerCase() !== activeUpdateEco)) return false;

    if (activeBadgeFilter === "new-server" && !server.badges.includes("NEW SERVER")) return false;
    if (activeBadgeFilter === "new-version" && !server.badges.includes("NEW VERSION")) return false;
    if (activeBadgeFilter === "tools-added" && !server.badges.some(b => b.includes("TOOLS ADDED"))) return false;
    if (activeBadgeFilter === "params-updated" && !server.badges.includes("PARAMETERS UPDATED")) return false;

    if (pq.minTools !== null && (!server.tools || server.tools.length < pq.minTools)) return false;

    for (const term of pq.toolTerms) {
      if (!server.tools || !server.tools.some(t => (t.name || "").toLowerCase().includes(term))) return false;
    }

    for (const token of pq.freeTextTokens) {
      let match = false;
      if ((server.name || "").toLowerCase().includes(token) || 
          (server.description || "").toLowerCase().includes(token) ||
          (server.command || "").toLowerCase().includes(token)) {
        match = true;
      } else if (server.tools && server.tools.some(t => 
          (t.name || "").toLowerCase().includes(token) || 
          (t.desc || t.description || "").toLowerCase().includes(token))) {
        match = true;
      }
      if (!match) return false;
    }
    return true;
  };

  const getToolsAddedDelta = (s) => {
    if (s.badges.includes("NEW SERVER")) return s.tools?.length || 0;
    const addedBadge = s.badges.find(b => b.includes("TOOLS ADDED"));
    if (addedBadge) {
      const match = addedBadge.match(/\+(\d+)/);
      if (match) return parseInt(match[1], 10);
    }
    return 0;
  };

  // Calculate badge counts
  const badgeCounts = { "new-server": 0, "new-version": 0, "tools-added": 0, "params-updated": 0 };
  
  // Calculate based on search, eco, and checkbox filters (NOT badge filter)
  const serversForCounts = servers.filter(s => {
    const tempBadgeFilter = activeBadgeFilter;
    activeBadgeFilter = "all";
    const result = filterServer(s);
    activeBadgeFilter = tempBadgeFilter;
    return result;
  });

  serversForCounts.forEach(s => {
    if (s.badges.includes("NEW SERVER")) badgeCounts["new-server"]++;
    if (s.badges.includes("NEW VERSION")) badgeCounts["new-version"]++;
    if (s.badges.some(b => b.includes("TOOLS ADDED"))) badgeCounts["tools-added"]++;
    if (s.badges.includes("PARAMETERS UPDATED")) badgeCounts["params-updated"]++;
  });

  document.querySelectorAll(".badge-filter-btn").forEach(btn => {
    const b = btn.getAttribute("data-badge");
    if (b === "all") btn.innerHTML = `All Updates <span class="filter-count">(${serversForCounts.length})</span>`;
    else if (b === "new-server") btn.innerHTML = `New Server <span class="filter-count">(${badgeCounts["new-server"]})</span>`;
    else if (b === "new-version") btn.innerHTML = `New Version <span class="filter-count">(${badgeCounts["new-version"]})</span>`;
    else if (b === "tools-added") btn.innerHTML = `+Tools Added <span class="filter-count">(${badgeCounts["tools-added"]})</span>`;
    else if (b === "params-updated") btn.innerHTML = `Params Updated <span class="filter-count">(${badgeCounts["params-updated"]})</span>`;
  });

  let displayServers = servers.filter(filterServer);

  displayServers.sort((a, b) => {
    const aTools = a.tools?.length || 0;
    const bTools = b.tools?.length || 0;
    const aName = a.name || "";
    const bName = b.name || "";
    
    if (activeUpdateSort === "default") {
      const aNew = a.badges.includes("NEW SERVER") ? 1 : 0;
      const bNew = b.badges.includes("NEW SERVER") ? 1 : 0;
      if (aNew !== bNew) return bNew - aNew;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-added-desc") {
      const aDelta = getToolsAddedDelta(a);
      const bDelta = getToolsAddedDelta(b);
      if (aDelta !== bDelta) return bDelta - aDelta;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-desc") {
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-asc") {
      if (aTools !== bTools) return aTools - bTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-asc") {
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-desc") {
      return bName.localeCompare(aName);
    }
    return 0;
  });

  metricsDisplay.innerHTML = `<strong>v${currentRelease}</strong> &mdash; Showing <strong>${displayServers.length}</strong> of <strong>${updateData.length}</strong> servers updated in this release.`;

  if (displayServers.length === 0) {
    serverGrid.innerHTML = `<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--text-muted);">No updates match the current filters.</div>`;
    return;
  }

  let html = "";
  displayServers.forEach(server => {function renderGrid(servers) {
  const filterToolsOnly = document.getElementById("filterToolsOnly")?.checked;
  const filterVerifiedOnly = document.getElementById("filterVerifiedOnly")?.checked;
  const pq = parseUpdateSearchQuery(activeUpdateQuery);

  const filterServer = (server) => {
    if (filterToolsOnly && (!server.tools || server.tools.length === 0)) return false;
    if (filterVerifiedOnly && !server.is_verified) return false;
    if (activeUpdateEco !== "all" && (!server.ecosystem || server.ecosystem.toLowerCase() !== activeUpdateEco)) return false;

    if (activeBadgeFilter === "new-server" && !server.badges.includes("NEW SERVER")) return false;
    if (activeBadgeFilter === "new-version" && !server.badges.includes("NEW VERSION")) return false;
    if (activeBadgeFilter === "tools-added" && !server.badges.some(b => b.includes("TOOLS ADDED"))) return false;
    if (activeBadgeFilter === "params-updated" && !server.badges.includes("PARAMETERS UPDATED")) return false;

    if (pq.minTools !== null && (!server.tools || server.tools.length < pq.minTools)) return false;

    for (const term of pq.toolTerms) {
      if (!server.tools || !server.tools.some(t => (t.name || "").toLowerCase().includes(term))) return false;
    }

    for (const token of pq.freeTextTokens) {
      let match = false;
      if ((server.name || "").toLowerCase().includes(token) || 
          (server.description || "").toLowerCase().includes(token) ||
          (server.command || "").toLowerCase().includes(token)) {
        match = true;
      } else if (server.tools && server.tools.some(t => 
          (t.name || "").toLowerCase().includes(token) || 
          (t.desc || t.description || "").toLowerCase().includes(token))) {
        match = true;
      }
      if (!match) return false;
    }
    return true;
  };

  const getToolsAddedDelta = (s) => {
    if (s.badges.includes("NEW SERVER")) return s.tools?.length || 0;
    const addedBadge = s.badges.find(b => b.includes("TOOLS ADDED"));
    if (addedBadge) {
      const match = addedBadge.match(/\+(\d+)/);
      if (match) return parseInt(match[1], 10);
    }
    return 0;
  };

  // Calculate badge counts
  const badgeCounts = { "new-server": 0, "new-version": 0, "tools-added": 0, "params-updated": 0 };
  
  // Calculate based on search, eco, and checkbox filters (NOT badge filter)
  const serversForCounts = servers.filter(s => {
    const tempBadgeFilter = activeBadgeFilter;
    activeBadgeFilter = "all";
    const result = filterServer(s);
    activeBadgeFilter = tempBadgeFilter;
    return result;
  });

  serversForCounts.forEach(s => {
    if (s.badges.includes("NEW SERVER")) badgeCounts["new-server"]++;
    if (s.badges.includes("NEW VERSION")) badgeCounts["new-version"]++;
    if (s.badges.some(b => b.includes("TOOLS ADDED"))) badgeCounts["tools-added"]++;
    if (s.badges.includes("PARAMETERS UPDATED")) badgeCounts["params-updated"]++;
  });

  document.querySelectorAll(".badge-filter-btn").forEach(btn => {
    const b = btn.getAttribute("data-badge");
    if (b === "all") btn.innerHTML = `All Updates <span class="filter-count">(${serversForCounts.length})</span>`;
    else if (b === "new-server") btn.innerHTML = `New Server <span class="filter-count">(${badgeCounts["new-server"]})</span>`;
    else if (b === "new-version") btn.innerHTML = `New Version <span class="filter-count">(${badgeCounts["new-version"]})</span>`;
    else if (b === "tools-added") btn.innerHTML = `+Tools Added <span class="filter-count">(${badgeCounts["tools-added"]})</span>`;
    else if (b === "params-updated") btn.innerHTML = `Params Updated <span class="filter-count">(${badgeCounts["params-updated"]})</span>`;
  });

  let displayServers = servers.filter(filterServer);

  displayServers.sort((a, b) => {
    const aTools = a.tools?.length || 0;
    const bTools = b.tools?.length || 0;
    const aName = a.name || "";
    const bName = b.name || "";
    
    if (activeUpdateSort === "default") {
      const aNew = a.badges.includes("NEW SERVER") ? 1 : 0;
      const bNew = b.badges.includes("NEW SERVER") ? 1 : 0;
      if (aNew !== bNew) return bNew - aNew;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-added-desc") {
      const aDelta = getToolsAddedDelta(a);
      const bDelta = getToolsAddedDelta(b);
      if (aDelta !== bDelta) return bDelta - aDelta;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-desc") {
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-asc") {
      if (aTools !== bTools) return aTools - bTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-asc") {
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-desc") {
      return bName.localeCompare(aName);
    }
    return 0;
  });

  metricsDisplay.innerHTML = `<strong>v${currentRelease}</strong> &mdash; Showing <strong>${displayServers.length}</strong> of <strong>${updateData.length}</strong> servers updated in this release.`;

  if (displayServers.length === 0) {
    serverGrid.innerHTML = `<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--text-muted);">No updates match the current filters.</div>`;
    return;
  }

  let html = "";
  displayServers.forEach(server => {
  const filterToolsOnly = document.getElementById("filterToolsOnly")?.checked;
  const filterVerifiedOnly = document.getElementById("filterVerifiedOnly")?.checked;
  const pq = parseUpdateSearchQuery(activeUpdateQuery);

  const filterServer = (server) => {
    if (filterToolsOnly && (!server.tools || server.tools.length === 0)) return false;
    if (filterVerifiedOnly && !server.is_verified) return false;
    if (activeUpdateEco !== "all" && (!server.ecosystem || server.ecosystem.toLowerCase() !== activeUpdateEco)) return false;

    if (activeBadgeFilter === "new-server" && !server.badges.includes("NEW SERVER")) return false;
    if (activeBadgeFilter === "new-version" && !server.badges.includes("NEW VERSION")) return false;
    if (activeBadgeFilter === "tools-added" && !server.badges.some(b => b.includes("TOOLS ADDED"))) return false;
    if (activeBadgeFilter === "params-updated" && !server.badges.includes("PARAMETERS UPDATED")) return false;

    if (pq.minTools !== null && (!server.tools || server.tools.length < pq.minTools)) return false;

    for (const term of pq.toolTerms) {
      if (!server.tools || !server.tools.some(t => (t.name || "").toLowerCase().includes(term))) return false;
    }

    for (const token of pq.freeTextTokens) {
      let match = false;
      if ((server.name || "").toLowerCase().includes(token) || 
          (server.description || "").toLowerCase().includes(token) ||
          (server.command || "").toLowerCase().includes(token)) {
        match = true;
      } else if (server.tools && server.tools.some(t => 
          (t.name || "").toLowerCase().includes(token) || 
          (t.desc || t.description || "").toLowerCase().includes(token))) {
        match = true;
      }
      if (!match) return false;
    }
    return true;
  };

  const getToolsAddedDelta = (s) => {
    if (s.badges.includes("NEW SERVER")) return s.tools?.length || 0;
    const addedBadge = s.badges.find(b => b.includes("TOOLS ADDED"));
    if (addedBadge) {
      const match = addedBadge.match(/\+(\d+)/);
      if (match) return parseInt(match[1], 10);
    }
    return 0;
  };

  // Calculate badge counts
  const badgeCounts = { "new-server": 0, "new-version": 0, "tools-added": 0, "params-updated": 0 };
  
  // Calculate based on search, eco, and checkbox filters (NOT badge filter)
  const serversForCounts = servers.filter(s => {
    const tempBadgeFilter = activeBadgeFilter;
    activeBadgeFilter = "all";
    const result = filterServer(s);
    activeBadgeFilter = tempBadgeFilter;
    return result;
  });

  serversForCounts.forEach(s => {
    if (s.badges.includes("NEW SERVER")) badgeCounts["new-server"]++;
    if (s.badges.includes("NEW VERSION")) badgeCounts["new-version"]++;
    if (s.badges.some(b => b.includes("TOOLS ADDED"))) badgeCounts["tools-added"]++;
    if (s.badges.includes("PARAMETERS UPDATED")) badgeCounts["params-updated"]++;
  });

  document.querySelectorAll(".badge-filter-btn").forEach(btn => {
    const b = btn.getAttribute("data-badge");
    if (b === "all") btn.innerHTML = `All Updates <span class="filter-count">(${serversForCounts.length})</span>`;
    else if (b === "new-server") btn.innerHTML = `New Server <span class="filter-count">(${badgeCounts["new-server"]})</span>`;
    else if (b === "new-version") btn.innerHTML = `New Version <span class="filter-count">(${badgeCounts["new-version"]})</span>`;
    else if (b === "tools-added") btn.innerHTML = `+Tools Added <span class="filter-count">(${badgeCounts["tools-added"]})</span>`;
    else if (b === "params-updated") btn.innerHTML = `Params Updated <span class="filter-count">(${badgeCounts["params-updated"]})</span>`;
  });

  let displayServers = servers.filter(filterServer);

  displayServers.sort((a, b) => {
    const aTools = a.tools?.length || 0;
    const bTools = b.tools?.length || 0;
    const aName = a.name || "";
    const bName = b.name || "";
    
    if (activeUpdateSort === "default") {
      const aNew = a.badges.includes("NEW SERVER") ? 1 : 0;
      const bNew = b.badges.includes("NEW SERVER") ? 1 : 0;
      if (aNew !== bNew) return bNew - aNew;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-added-desc") {
      const aDelta = getToolsAddedDelta(a);
      const bDelta = getToolsAddedDelta(b);
      if (aDelta !== bDelta) return bDelta - aDelta;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-desc") {
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-asc") {
      if (aTools !== bTools) return aTools - bTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-asc") {
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-desc") {
      return bName.localeCompare(aName);
    }
    return 0;
  });

  metricsDisplay.innerHTML = `<strong>v${currentRelease}</strong> &mdash; Showing <strong>${displayServers.length}</strong> of <strong>${updateData.length}</strong> servers updated in this release.`;

  if (displayServers.length === 0) {
    serverGrid.innerHTML = `<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--text-muted);">No updates match the current filters.</div>`;
    return;
  }

  let html = "";
  displayServers.forEach(server => {function renderGrid(servers) {
  const filterToolsOnly = document.getElementById("filterToolsOnly")?.checked;
  const filterVerifiedOnly = document.getElementById("filterVerifiedOnly")?.checked;
  const pq = parseUpdateSearchQuery(activeUpdateQuery);

  const filterServer = (server) => {
    if (filterToolsOnly && (!server.tools || server.tools.length === 0)) return false;
    if (filterVerifiedOnly && !server.is_verified) return false;
    if (activeUpdateEco !== "all" && (!server.ecosystem || server.ecosystem.toLowerCase() !== activeUpdateEco)) return false;

    if (activeBadgeFilter === "new-server" && !server.badges.includes("NEW SERVER")) return false;
    if (activeBadgeFilter === "new-version" && !server.badges.includes("NEW VERSION")) return false;
    if (activeBadgeFilter === "tools-added" && !server.badges.some(b => b.includes("TOOLS ADDED"))) return false;
    if (activeBadgeFilter === "params-updated" && !server.badges.includes("PARAMETERS UPDATED")) return false;

    if (pq.minTools !== null && (!server.tools || server.tools.length < pq.minTools)) return false;

    for (const term of pq.toolTerms) {
      if (!server.tools || !server.tools.some(t => (t.name || "").toLowerCase().includes(term))) return false;
    }

    for (const token of pq.freeTextTokens) {
      let match = false;
      if ((server.name || "").toLowerCase().includes(token) || 
          (server.description || "").toLowerCase().includes(token) ||
          (server.command || "").toLowerCase().includes(token)) {
        match = true;
      } else if (server.tools && server.tools.some(t => 
          (t.name || "").toLowerCase().includes(token) || 
          (t.desc || t.description || "").toLowerCase().includes(token))) {
        match = true;
      }
      if (!match) return false;
    }
    return true;
  };

  const getToolsAddedDelta = (s) => {
    if (s.badges.includes("NEW SERVER")) return s.tools?.length || 0;
    const addedBadge = s.badges.find(b => b.includes("TOOLS ADDED"));
    if (addedBadge) {
      const match = addedBadge.match(/\+(\d+)/);
      if (match) return parseInt(match[1], 10);
    }
    return 0;
  };

  // Calculate badge counts
  const badgeCounts = { "new-server": 0, "new-version": 0, "tools-added": 0, "params-updated": 0 };
  
  // Calculate based on search, eco, and checkbox filters (NOT badge filter)
  const serversForCounts = servers.filter(s => {
    const tempBadgeFilter = activeBadgeFilter;
    activeBadgeFilter = "all";
    const result = filterServer(s);
    activeBadgeFilter = tempBadgeFilter;
    return result;
  });

  serversForCounts.forEach(s => {
    if (s.badges.includes("NEW SERVER")) badgeCounts["new-server"]++;
    if (s.badges.includes("NEW VERSION")) badgeCounts["new-version"]++;
    if (s.badges.some(b => b.includes("TOOLS ADDED"))) badgeCounts["tools-added"]++;
    if (s.badges.includes("PARAMETERS UPDATED")) badgeCounts["params-updated"]++;
  });

  document.querySelectorAll(".badge-filter-btn").forEach(btn => {
    const b = btn.getAttribute("data-badge");
    if (b === "all") btn.innerHTML = `All Updates <span class="filter-count">(${serversForCounts.length})</span>`;
    else if (b === "new-server") btn.innerHTML = `New Server <span class="filter-count">(${badgeCounts["new-server"]})</span>`;
    else if (b === "new-version") btn.innerHTML = `New Version <span class="filter-count">(${badgeCounts["new-version"]})</span>`;
    else if (b === "tools-added") btn.innerHTML = `+Tools Added <span class="filter-count">(${badgeCounts["tools-added"]})</span>`;
    else if (b === "params-updated") btn.innerHTML = `Params Updated <span class="filter-count">(${badgeCounts["params-updated"]})</span>`;
  });

  let displayServers = servers.filter(filterServer);

  displayServers.sort((a, b) => {
    const aTools = a.tools?.length || 0;
    const bTools = b.tools?.length || 0;
    const aName = a.name || "";
    const bName = b.name || "";
    
    if (activeUpdateSort === "default") {
      const aNew = a.badges.includes("NEW SERVER") ? 1 : 0;
      const bNew = b.badges.includes("NEW SERVER") ? 1 : 0;
      if (aNew !== bNew) return bNew - aNew;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-added-desc") {
      const aDelta = getToolsAddedDelta(a);
      const bDelta = getToolsAddedDelta(b);
      if (aDelta !== bDelta) return bDelta - aDelta;
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-desc") {
      if (aTools !== bTools) return bTools - aTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "tools-asc") {
      if (aTools !== bTools) return aTools - bTools;
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-asc") {
      return aName.localeCompare(bName);
    } else if (activeUpdateSort === "name-desc") {
      return bName.localeCompare(aName);
    }
    return 0;
  });

  metricsDisplay.innerHTML = `<strong>v${currentRelease}</strong> &mdash; Showing <strong>${displayServers.length}</strong> of <strong>${updateData.length}</strong> servers updated in this release.`;

  if (displayServers.length === 0) {
    serverGrid.innerHTML = `<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--text-muted);">No updates match the current filters.</div>`;
    return;
  }

  let html = "";
  displayServers.forEach(server => {function renderGrid(servers) {
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
    const safeName = server.name.replace(/'/g, "\\'");
    
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
          <div class="card-title" style="cursor:pointer; text-decoration:underline; color:var(--accent);" onclick="event.stopPropagation(); openInspectorModal('${safeName}')">${escapeHtml(server.name)}</div>
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
window.openInspectorModal = function(serverName, targetToolName) {
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
      const isTarget = targetToolName && tool.name === targetToolName;
      html += `<div class="tool-detail-card" ${isTarget ? 'style="border-color: var(--accent); box-shadow: 0 0 12px var(--accent-glow);"' : ''} id="tool-update-${escapeHtml(tool.name)}">
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
  
  if (targetToolName) {
    setTimeout(() => {
      const el = document.getElementById(`tool-update-${targetToolName}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  }
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

let activeUpdateQuery = "";
let activeBadgeFilter = "all";
let activeUpdateEco = "all";
let activeUpdateSort = "default";

function updateUpdatesURLState() {
  const url = new URL(window.location);
  
  if (currentRelease) url.searchParams.set("release", currentRelease);
  else url.searchParams.delete("release");
  
  if (activeUpdateQuery) url.searchParams.set("q", activeUpdateQuery);
  else url.searchParams.delete("q");
  
  if (activeBadgeFilter !== "all") url.searchParams.set("badge", activeBadgeFilter);
  else url.searchParams.delete("badge");
  
  if (activeUpdateEco !== "all") url.searchParams.set("eco", activeUpdateEco);
  else url.searchParams.delete("eco");
  
  if (activeUpdateSort !== "default") url.searchParams.set("sort", activeUpdateSort);
  else url.searchParams.delete("sort");

  const elTools = document.getElementById("filterToolsOnly");
  const elVerified = document.getElementById("filterVerifiedOnly");

  if (elTools && elTools.checked) url.searchParams.set("tools", "1");
  else url.searchParams.delete("tools");

  if (elVerified && elVerified.checked) url.searchParams.set("verified", "1");
  else url.searchParams.delete("verified");

  history.replaceState(null, "", url);

  const resetBtn = document.getElementById("resetUpdateFiltersBtn");
  if (resetBtn) {
    const hasNonDefault = activeUpdateQuery || activeBadgeFilter !== "all" || activeUpdateEco !== "all" || activeUpdateSort !== "default" || 
                          (elTools && elTools.checked) || (elVerified && elVerified.checked);
    resetBtn.style.display = hasNonDefault ? "inline-flex" : "none";
  }
}

function initUpdatesFromURL() {
  const params = new URLSearchParams(window.location.search);
  
  activeUpdateQuery = params.get("q") || "";
  activeBadgeFilter = params.get("badge") || "all";
  activeUpdateEco = params.get("eco") || "all";
  activeUpdateSort = params.get("sort") || "default";
  
  const searchInput = document.getElementById("updateSearchInput");
  if (searchInput) searchInput.value = activeUpdateQuery;
  
  document.querySelectorAll(".badge-filter-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-badge") === activeBadgeFilter);
  });
  
  const ecoSelect = document.getElementById("updateEcoSelect");
  if (ecoSelect) ecoSelect.value = activeUpdateEco;
  
  const sortSelect = document.getElementById("updateSortSelect");
  if (sortSelect) sortSelect.value = activeUpdateSort;
  
  const elTools = document.getElementById("filterToolsOnly");
  const elVerified = document.getElementById("filterVerifiedOnly");
  
  if (elTools) elTools.checked = params.get("tools") === "1";
  if (elVerified) elVerified.checked = params.get("verified") === "1";
  
  updateUpdatesURLState();
}

function parseUpdateSearchQuery(rawQuery) {
  const q = (rawQuery || "").trim().toLowerCase();
  const result = { freeTextTokens: [], toolTerms: [], minTools: null };
  if (!q) return result;
  const tokens = q.split(/\s+/);
  for (const token of tokens) {
    if (token.startsWith("tool:")) result.toolTerms.push(token.substring(5));
    else if (token.startsWith("min-tools:")) {
      const val = parseInt(token.substring(10), 10);
      if (!isNaN(val)) result.minTools = val;
    }
    else result.freeTextTokens.push(token);
  }
  return result;
}

document.getElementById("updateSearchInput")?.addEventListener("input", (e) => {
  activeUpdateQuery = e.target.value;
  updateUpdatesURLState();
  renderGrid(updateData);
});

document.querySelectorAll(".badge-filter-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    activeBadgeFilter = e.target.getAttribute("data-badge");
    document.querySelectorAll(".badge-filter-btn").forEach(b => b.classList.remove("active"));
    e.target.classList.add("active");
    updateUpdatesURLState();
    renderGrid(updateData);
  });
});

document.getElementById("updateEcoSelect")?.addEventListener("change", (e) => {
  activeUpdateEco = e.target.value;
  updateUpdatesURLState();
  renderGrid(updateData);
});

document.getElementById("updateSortSelect")?.addEventListener("change", (e) => {
  activeUpdateSort = e.target.value;
  updateUpdatesURLState();
  renderGrid(updateData);
});

document.getElementById("filterVerifiedOnly")?.addEventListener("change", () => {
  updateUpdatesURLState();
  renderGrid(updateData);
});

document.getElementById("resetUpdateFiltersBtn")?.addEventListener("click", () => {
  activeUpdateQuery = "";
  activeBadgeFilter = "all";
  activeUpdateEco = "all";
  activeUpdateSort = "default";
  
  const searchInput = document.getElementById("updateSearchInput");
  if (searchInput) searchInput.value = "";
  
  document.querySelectorAll(".badge-filter-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-badge") === "all");
  });
  
  const ecoSelect = document.getElementById("updateEcoSelect");
  if (ecoSelect) ecoSelect.value = "all";
  
  const sortSelect = document.getElementById("updateSortSelect");
  if (sortSelect) sortSelect.value = "default";
  
  const elTools = document.getElementById("filterToolsOnly");
  const elVerified = document.getElementById("filterVerifiedOnly");
  
  if (elTools) elTools.checked = false;
  if (elVerified) elVerified.checked = false;
  
  updateUpdatesURLState();
  renderGrid(updateData);
});
