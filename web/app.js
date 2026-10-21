let catalog = [];
let filteredCatalog = [];
let activeEco = "all";
let activeQuery = "";
let selectedServers = new Map();
let activeModalClient = "claude";

// Version & Drawer State
const cardActiveVersions = new Map();
const openDrawers = new Set();
const drawerQueries = new Map();

// Infinite Batch Rendering
const BATCH_SIZE = 48;
let renderedCount = 0;
let sentinelObserver = null;

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function getSafeId(name) {
  return "server-" + name.replace(/[^a-zA-Z0-9_-]/g, "-");
}

function getVisibleRange(scrollTop, containerHeight, itemHeight, itemCount, columns) {
  const buffer = 2;
  const GAP = 20;
  const totalItemHeight = itemHeight + GAP;
  const startRow = Math.max(0, Math.floor(scrollTop / totalItemHeight) - buffer);
  const visibleRows = Math.ceil(containerHeight / totalItemHeight) + (buffer * 2);
  const startIndex = startRow * columns;
  const endIndex = Math.min(itemCount, startIndex + (visibleRows * columns));
  return { startIndex, endIndex };
}

function getActiveVersionForServer(item) {
  if (cardActiveVersions.has(item.name)) {
    return cardActiveVersions.get(item.name);
  }
  const defaultVer =
    item.latest_version ||
    item.version ||
    (item.versions && item.versions[0] ? item.versions[0].version : "1.0.0");
  cardActiveVersions.set(item.name, defaultVer);
  return defaultVer;
}

function getVersionData(item, versionStr) {
  if (item.versions && item.versions.length > 0) {
    const found = item.versions.find((v) => v.version === versionStr);
    if (found) return found;
  }
  return {
    version: versionStr || item.version || "1.0.0",
    tools: item.tools || [],
    tool_count: (item.tools || []).length,
    command: item.command || item.name,
    required_env_vars: item.required_env_vars || [],
    transports: item.transports || [],
  };
}

// Initialize on Load
window.addEventListener("DOMContentLoaded", () => {
  setupSentinelObserver();
  initFromURL();
  loadCatalog();
});

function setupSentinelObserver() {
  const sentinel = document.getElementById("scrollSentinel");
  if (!sentinel) return;

  sentinelObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && renderedCount < filteredCatalog.length) {
          renderNextBatch();
        }
      });
    },
    { rootMargin: "400px" },
  );

  sentinelObserver.observe(sentinel);
}

async function loadCatalog() {
  const metrics = document.getElementById("metricsDisplay");
  try {
    const resp = await fetch("catalog.json");
    if (!resp.ok) throw new Error("Catalog file not found");
    catalog = await resp.json();
  } catch (err) {
    console.warn("Could not load catalog.json, using fallback data:", err);
    catalog = [
      {
        name: "@modelcontextprotocol/server-filesystem",
        ecosystem: "npm",
        version: "1.0.0",
        description:
          "Direct local filesystem reader and writer toolset for AI coding assistants.",
        tool_count: 3,
        tools: [
          {
            name: "read_file",
            description: "Read file contents from filesystem",
            parameters: [
              { name: "path", type: "string", required: true, description: "Path to file" },
            ],
          },
          {
            name: "write_file",
            description: "Write contents to local file",
            parameters: [
              { name: "path", type: "string", required: true, description: "Path to file" },
              { name: "content", type: "string", required: true, description: "File content" },
            ],
          },
          {
            name: "list_directory",
            description: "List directory files and subdirectories",
            parameters: [
              { name: "path", type: "string", required: true, description: "Directory path" },
            ],
          },
        ],
        command: "npx -y @modelcontextprotocol/server-filesystem",
      },
    ];
  }

  render();
}

function render() {
  const q = activeQuery.toLowerCase().trim();
  const filterToolsOnly = document.getElementById("filterToolsOnly")?.checked;

  filteredCatalog = catalog.filter((item) => {
    if (filterToolsOnly) {
      const activeVer = getActiveVersionForServer(item);
      const vData = getVersionData(item, activeVer);
      if (!vData.tools || vData.tools.length === 0) return false;
    }
    if (activeEco !== "all" && item.ecosystem.toLowerCase() !== activeEco) {
      return false;
    }
    if (!q) return true;
    if (item.name.toLowerCase().includes(q)) return true;
    if (item.description && item.description.toLowerCase().includes(q)) return true;
    // Check tools
    if (item.tools && item.tools.some((t) => t.name.toLowerCase().includes(q))) {
      return true;
    }
    // Check parameters
    if (
      item.tools &&
      item.tools.some(
        (t) =>
          t.parameters &&
          t.parameters.some((p) => p.name.toLowerCase().includes(q)),
      )
    ) {
      return true;
    }
    return false;
  });

  const metrics = document.getElementById("metricsDisplay");
  if (metrics) {
    metrics.innerHTML = `Showing <strong>${filteredCatalog.length.toLocaleString()}</strong> of <strong>${catalog.length.toLocaleString()}</strong> verified MCP servers`;
  }

  const grid = document.getElementById("serverGrid");
  if (grid) {
    grid.innerHTML = "";
  }

  renderedCount = 0;
  renderNextBatch();
}

function renderNextBatch() {
  const grid = document.getElementById("serverGrid");
  if (!grid) return;

  const nextItems = filteredCatalog.slice(
    renderedCount,
    renderedCount + BATCH_SIZE,
  );
  if (nextItems.length === 0) return;

  const fragment = document.createDocumentFragment();
  nextItems.forEach((item) => {
    const card = buildCardElement(item);
    fragment.appendChild(card);
  });

  grid.appendChild(fragment);
  renderedCount += nextItems.length;

  const sentinel = document.getElementById("scrollSentinel");
  if (sentinel) {
    if (renderedCount >= filteredCatalog.length) {
      sentinel.textContent =
        filteredCatalog.length > 0
          ? "✓ All servers displayed"
          : "No servers matching filter criteria.";
    } else {
      sentinel.textContent = "Loading more servers...";
    }
  }
}

function getEcosystemBadgeClass(eco) {
  switch ((eco || "").toLowerCase()) {
    case "npm":
      return "badge-eco-npm";
    case "pypi":
    case "python":
      return "badge-eco-pypi";
    case "github":
      return "badge-eco-github";
    case "golang":
    case "go":
      return "badge-eco-golang";
    default:
      return "badge-eco-generic";
  }
}

function buildCardElement(item) {
  const card = document.createElement("div");
  card.className = "card";
  card.id = getSafeId(item.name);
  card.setAttribute("data-name", item.name);

  updateCardContent(card, item);
  return card;
}

function updateCardContent(card, item) {
  const activeVer = getActiveVersionForServer(item);
  const versionData = getVersionData(item, activeVer);
  const isChecked = selectedServers.has(item.name) ? "checked" : "";
  const safeName = escapeHtml(item.name);
  const isDrawerOpen = openDrawers.has(item.name);
  const currentQuery = drawerQueries.get(item.name) || "";

  const allVersions =
    item.versions && item.versions.length > 0
      ? item.versions
      : [{ version: item.version || "1.0.0" }];
  const hasMultipleVersions = allVersions.length > 1;

  // Version Badge HTML
  let versionHtml = "";
  if (hasMultipleVersions) {
    versionHtml = `
      <select class="badge badge-version-select" title="Switch server version" onchange="changeCardVersion(event, '${safeName}')">
        ${allVersions
          .map(
            (v) =>
              `<option value="${escapeHtml(v.version)}" ${
                v.version === activeVer ? "selected" : ""
              }>v${escapeHtml(v.version)}</option>`,
          )
          .join("")}
      </select>
    `;
  } else {
    versionHtml = `<span class="badge badge-version">v${escapeHtml(activeVer)}</span>`;
  }

  // Tools preview
  const tools = versionData.tools || [];
  const previewTools = tools.slice(0, 6);
  const remainingToolsCount = tools.length - 6;

  let toolsPreviewHtml = "";
  if (tools.length > 0) {
    toolsPreviewHtml = `
      <div class="tools-section">
        <div class="tools-header">
          <span class="tools-label">Tools (${tools.length})</span>
          <button class="btn-toggle-tools" onclick="toggleToolDrawer('${safeName}')">
            ${isDrawerOpen ? "Hide Tools ▴" : "Explore Tools ▾"}
          </button>
        </div>
        <div class="tool-tags">
          ${previewTools
            .map(
              (t) =>
                `<span class="tool-tag" title="${escapeHtml(t.description || t.name)}" onclick="openInspectorModal('${safeName}', '${escapeHtml(activeVer)}', '${escapeHtml(t.name)}')">${escapeHtml(t.name)}</span>`,
            )
            .join("")}
          ${
            remainingToolsCount > 0
              ? `<span class="tool-tag-more" onclick="toggleToolDrawer('${safeName}')">+${remainingToolsCount} more</span>`
              : ""
          }
        </div>
      </div>
    `;
  } else {
    toolsPreviewHtml = `
      <div class="tools-section">
        <div class="tools-label">Tools (0)</div>
        <div class="no-tools-badge">No static tools declared (Remote Endpoint / Gateway)</div>
      </div>
    `;
  }

  // Drawer HTML
  let drawerHtml = "";
  if (isDrawerOpen) {
    const qLower = currentQuery.toLowerCase().trim();
    const filteredTools = tools.filter((t) => {
      if (!qLower) return true;
      if (t.name.toLowerCase().includes(qLower)) return true;
      if (t.description && t.description.toLowerCase().includes(qLower)) return true;
      return false;
    });

    drawerHtml = `
      <div class="inline-tool-drawer">
        <div class="drawer-search-bar">
          <input 
            type="text" 
            class="drawer-search-input" 
            placeholder="Filter ${tools.length} tools..." 
            value="${escapeHtml(currentQuery)}" 
            oninput="filterDrawerTools('${safeName}', this.value)"
            autofocus
          />
          <span class="drawer-count-badge">${filteredTools.length} / ${tools.length}</span>
        </div>
        <div class="drawer-tools-container">
          ${
            filteredTools.length > 0
              ? filteredTools
                  .map((t) => {
                    const paramCount = t.parameters ? t.parameters.length : 0;
                    return `
                    <div class="drawer-tool-row" onclick="openInspectorModal('${safeName}', '${escapeHtml(activeVer)}', '${escapeHtml(t.name)}')">
                      <div class="drawer-tool-top">
                        <span class="drawer-tool-name">${escapeHtml(t.name)}</span>
                        <span class="drawer-tool-params-count">${paramCount} ${paramCount === 1 ? "param" : "params"}</span>
                      </div>
                      <div class="drawer-tool-desc">${escapeHtml(t.description || "No description provided.")}</div>
                    </div>
                  `;
                  })
                  .join("")
              : `<div style="text-align:center; padding:1rem; font-size:0.8rem; color:var(--text-muted);">No tools match "${escapeHtml(currentQuery)}"</div>`
          }
        </div>
      </div>
    `;
  }

  // Install command
  const installCmd = versionData.command || item.command || item.name;

  card.innerHTML = `
    <div>
      <div class="card-header">
        <div class="card-title">
          <label class="checkbox-container">
            <input 
              type="checkbox" 
              class="server-checkbox" 
              data-name="${safeName}" 
              ${isChecked} 
              onchange="toggleSelection('${safeName}')"
            />
            <span onclick="openInspectorModal('${safeName}', '${escapeHtml(activeVer)}')" title="Inspect server details">${safeName}</span>
          </label>
        </div>
        <div class="card-badges">
          <span class="badge ${getEcosystemBadgeClass(item.ecosystem)}">${escapeHtml(item.ecosystem)}</span>
          ${versionHtml}
        </div>
      </div>

      <div class="card-desc" title="${escapeHtml(item.description)}">
        ${escapeHtml(item.description || "No description provided.")}
      </div>

      ${toolsPreviewHtml}
      ${drawerHtml}
    </div>

    <div class="card-actions">
      <button class="btn-copy" onclick="copyConfig('${safeName}', '${escapeHtml(item.ecosystem)}', '${escapeHtml(installCmd)}', 'claude', this)">
        Copy Claude
      </button>
      <button class="btn-copy" onclick="copyConfig('${safeName}', '${escapeHtml(item.ecosystem)}', '${escapeHtml(installCmd)}', 'cursor', this)">
        Copy Cursor
      </button>
      <button class="btn-inspect" onclick="openInspectorModal('${safeName}', '${escapeHtml(activeVer)}')">
        Inspect
      </button>
    </div>
  `;
}

function changeCardVersion(event, serverName) {
  const newVersion = event.target.value;
  cardActiveVersions.set(serverName, newVersion);

  const card = document.getElementById(getSafeId(serverName));
  const item = catalog.find((s) => s.name === serverName);
  if (card && item) {
    updateCardContent(card, item);
  }
}

function toggleToolDrawer(serverName) {
  if (openDrawers.has(serverName)) {
    openDrawers.delete(serverName);
  } else {
    openDrawers.add(serverName);
  }

  const card = document.getElementById(getSafeId(serverName));
  const item = catalog.find((s) => s.name === serverName);
  if (card && item) {
    updateCardContent(card, item);
  }
}

function filterDrawerTools(serverName, query) {
  drawerQueries.set(serverName, query);
  const card = document.getElementById(getSafeId(serverName));
  const item = catalog.find((s) => s.name === serverName);
  if (card && item) {
    updateCardContent(card, item);
  }
}

// Config Copying
function copyConfig(name, eco, cmd, client, btn) {
  const safeKey = name.replace(/[@/_]/g, "-");
  const parts = cmd.split(" ");
  const command = parts[0] || (eco === "pypi" ? "uvx" : "npx");
  const args = parts.slice(1);

  let payload = {};
  if (
    client === "claude" ||
    client === "cursor" ||
    client === "zed" ||
    client === "windsurf"
  ) {
    payload = {
      mcpServers: {
        [safeKey]: { command, args },
      },
    };
  } else if (client === "cline") {
    payload = {
      mcpServers: {
        [safeKey]: { command, args, disabled: false, autoApprove: [] },
      },
    };
  }

  navigator.clipboard.writeText(JSON.stringify(payload, null, 2)).then(() => {
    showToast();
    if (btn) {
      btn.classList.add("copied");
      const originalText = btn.innerText;
      btn.innerText = "Copied!";
      setTimeout(() => {
        btn.classList.remove("copied");
        btn.innerText = originalText;
      }, 1500);
    }
  });
}

function showToast(msg = "Copied configuration to clipboard!") {
  const t = document.getElementById("toast");
  if (!t) return;
  t.innerText = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2200);
}

// Search & Filter Listeners
const searchInput = document.getElementById("searchInput");
if (searchInput) {
  searchInput.addEventListener("input", (e) => {
    activeQuery = e.target.value;
    updateURLState();
    render();
  });
}

const filterToolsOnlyCheckbox = document.getElementById("filterToolsOnly");
if (filterToolsOnlyCheckbox) {
  filterToolsOnlyCheckbox.addEventListener("change", (e) => {
    render();
  });
}

document.querySelectorAll(".filter-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    document
      .querySelectorAll(".filter-btn")
      .forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    activeEco = e.target.getAttribute("data-val");
    updateURLState();
    render();
  });
});

function updateURLState() {
  const url = new URL(window.location);
  if (activeQuery) {
    url.searchParams.set("q", activeQuery);
  } else {
    url.searchParams.delete("q");
  }
  if (activeEco !== "all") {
    url.searchParams.set("eco", activeEco);
  } else {
    url.searchParams.delete("eco");
  }
  history.replaceState(null, "", url);
}

function initFromURL() {
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q");
  const eco = params.get("eco");

  if (q) {
    activeQuery = q;
    const input = document.getElementById("searchInput");
    if (input) input.value = q;
  }
  if (eco) {
    activeEco = eco;
    document.querySelectorAll(".filter-btn").forEach((b) => {
      if (b.getAttribute("data-val") === eco) {
        b.classList.add("active");
      } else {
        b.classList.remove("active");
      }
    });
  }
}

// Multi-Server Selection & Floating Bottom Drawer
function toggleSelection(name) {
  const item = catalog.find((s) => s.name === name);
  if (!item) return;

  if (selectedServers.has(name)) {
    selectedServers.delete(name);
  } else {
    selectedServers.set(name, item);
  }

  const count = selectedServers.size;
  const countEl = document.getElementById("selectedCount");
  if (countEl) countEl.innerText = count;

  const drawer = document.getElementById("bottomDrawer");
  if (drawer) {
    if (count > 0) {
      drawer.classList.add("show");
    } else {
      drawer.classList.remove("show");
    }
  }

  // Update checkbox state on card if visible
  const card = document.getElementById(getSafeId(name));
  if (card) {
    const cb = card.querySelector(".server-checkbox");
    if (cb) cb.checked = selectedServers.has(name);
  }
}

// Multi-Server Config Modal
function openConfigModal() {
  renderCombinedConfig();
  const modal = document.getElementById("configModal");
  if (modal) modal.classList.add("show");
}

function closeConfigModal() {
  const modal = document.getElementById("configModal");
  if (modal) modal.classList.remove("show");
}

function switchTab(client) {
  activeModalClient = client;
  document.querySelectorAll("#configModal .tab-btn").forEach((btn) => {
    if (btn.getAttribute("data-client") === client) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
  renderCombinedConfig();
}

function copyShareLink(name) {
  const url = new URL(window.location.origin + window.location.pathname);
  url.searchParams.set("q", name);
  navigator.clipboard.writeText(url.toString()).then(() => {
    showToast("Shareable link copied to clipboard!");
  });
}

function detectCollisions() {
  const toolMap = new Map();
  const collisions = [];
  selectedServers.forEach((item) => {
    const activeVer = getActiveVersionForServer(item);
    const vData = getVersionData(item, activeVer);
    if (vData.tools) {
      vData.tools.forEach((t) => {
        if (toolMap.has(t.name)) {
          collisions.push({
            tool: t.name,
            servers: [toolMap.get(t.name), item.name],
          });
        } else {
          toolMap.set(t.name, item.name);
        }
      });
    }
  });
  return collisions;
}

function generateCombinedConfig(client) {
  client = client || activeModalClient;
  let mcpServers = {};
  selectedServers.forEach((item) => {
    const activeVer = getActiveVersionForServer(item);
    const vData = getVersionData(item, activeVer);
    const safeKey = item.name.replace(/[@/_]/g, "-");
    const cmd = vData.command || item.command || item.name;
    const parts = cmd.split(" ");
    const command = parts[0] || (item.ecosystem === "pypi" ? "uvx" : "npx");
    const args = parts.slice(1);

    if (client === "cline") {
      mcpServers[safeKey] = { command, args, disabled: false, autoApprove: [] };
    } else {
      mcpServers[safeKey] = { command, args };
    }
  });
  return { mcpServers };
}

function renderCombinedConfig() {
  const output = document.getElementById("configOutput");
  if (!output) return;

  const collisions = detectCollisions();
  const collisionDiv = document.getElementById("collisionWarning");
  const collisionList = document.getElementById("collisionList");
  if (collisionDiv && collisionList) {
    if (collisions.length > 0) {
      collisionDiv.style.display = "block";
      collisionList.innerHTML = collisions
        .map(
          (c) =>
            `<li><code>${escapeHtml(c.tool)}</code> provided by both <strong>${escapeHtml(c.servers[0])}</strong> and <strong>${escapeHtml(c.servers[1])}</strong></li>`,
        )
        .join("");
    } else {
      collisionDiv.style.display = "none";
    }
  }

  const config = generateCombinedConfig(activeModalClient);
  output.innerText = JSON.stringify(config, null, 2);
}

function copyCombinedConfig() {
  const output = document.getElementById("configOutput");
  if (!output) return;
  navigator.clipboard.writeText(output.innerText).then(() => {
    showToast("Combined configuration copied!");
  });
}

function downloadCombinedConfig() {
  const output = document.getElementById("configOutput");
  if (!output) return;
  const blob = new Blob([output.innerText], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "mcp_config.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Interactive Inspector Modal
let currentInspectorServer = null;
let currentInspectorVersion = null;
let currentInspectorToolFilter = "";

function openInspectorModal(serverName, optionalVersion, optionalToolName) {
  const item = catalog.find((s) => s.name === serverName);
  if (!item) return;

  currentInspectorServer = item;
  currentInspectorVersion =
    optionalVersion || getActiveVersionForServer(item);
  currentInspectorToolFilter = "";

  renderInspectorModalContent(optionalToolName);

  const modal = document.getElementById("inspectorModal");
  if (modal) modal.classList.add("show");
}

function changeInspectorVersion(newVersion) {
  currentInspectorVersion = newVersion;
  cardActiveVersions.set(currentInspectorServer.name, newVersion);

  // Update card in grid as well
  const card = document.getElementById(getSafeId(currentInspectorServer.name));
  if (card) {
    updateCardContent(card, currentInspectorServer);
  }

  renderInspectorModalContent();
}

function filterInspectorTools(query) {
  currentInspectorToolFilter = query;
  renderInspectorModalTools();
}

function renderInspectorModalContent(targetToolName) {
  const item = currentInspectorServer;
  const activeVer = currentInspectorVersion;
  const vData = getVersionData(item, activeVer);

  const title = document.getElementById("inspectorTitle");
  if (title) {
    title.innerText = item.name;
  }

  const body = document.getElementById("inspectorBody");
  if (!body) return;

  const allVersions =
    item.versions && item.versions.length > 0
      ? item.versions
      : [{ version: item.version || "1.0.0" }];

  let versionSelectorHtml = "";
  if (allVersions.length > 1) {
    versionSelectorHtml = `
      <div class="inspector-meta-item">
        <strong>Version:</strong>
        <select class="badge badge-version-select" onchange="changeInspectorVersion(this.value)">
          ${allVersions
            .map(
              (v) =>
                `<option value="${escapeHtml(v.version)}" ${
                  v.version === activeVer ? "selected" : ""
                }>v${escapeHtml(v.version)}</option>`,
            )
            .join("")}
        </select>
      </div>
    `;
  } else {
    versionSelectorHtml = `<div class="inspector-meta-item"><strong>Version:</strong> v${escapeHtml(activeVer)}</div>`;
  }

  let html = `
    <div class="inspector-header-info">
      <div class="inspector-meta-item"><strong>Ecosystem:</strong> <span class="badge ${getEcosystemBadgeClass(item.ecosystem)}">${escapeHtml(item.ecosystem)}</span></div>
      ${versionSelectorHtml}
      ${
        item.repository_url
          ? `<div class="inspector-meta-item"><strong>Repo:</strong> <a href="${escapeHtml(item.repository_url)}" target="_blank" rel="noopener">${escapeHtml(item.repository_url)} ↗</a></div>`
          : ""
      }
      ${
        item.homepage_url
          ? `<div class="inspector-meta-item"><strong>Homepage:</strong> <a href="${escapeHtml(item.homepage_url)}" target="_blank" rel="noopener">${escapeHtml(item.homepage_url)} ↗</a></div>`
          : ""
      }
      ${item.author ? `<div class="inspector-meta-item"><strong>Author:</strong> ${escapeHtml(item.author)}</div>` : ""}
      ${item.license ? `<div class="inspector-meta-item"><strong>License:</strong> ${escapeHtml(item.license)}</div>` : ""}
      ${
        vData.transports && vData.transports.length > 0
          ? `<div class="inspector-meta-item"><strong>Transports:</strong> ${escapeHtml(vData.transports.join(", "))}</div>`
          : ""
      }
      ${
        vData.required_env_vars && vData.required_env_vars.length > 0
          ? `<div class="inspector-meta-item"><strong>Required Env:</strong> <code>${escapeHtml(vData.required_env_vars.join(", "))}</code></div>`
          : ""
      }
    </div>

    <div style="margin-bottom: 1.5rem; color: var(--text-muted); font-size: 0.95rem; line-height: 1.5;">
      ${escapeHtml(item.description || "No description provided.")}
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; gap: 1rem; flex-wrap: wrap;">
      <h3 style="color: var(--text); font-size: 1.15rem;">Tools Schema (${(vData.tools || []).length})</h3>
      <input 
        type="text" 
        id="modalToolSearch" 
        placeholder="Filter tools or parameters..." 
        style="background: #090d16; border: 1px solid var(--border-light); border-radius: 6px; padding: 0.4rem 0.8rem; font-size: 0.85rem; color: var(--text); outline: none; min-width: 240px;"
        oninput="filterInspectorTools(this.value)"
      />
    </div>

    <div id="inspectorToolsContainer">
      <!-- Tools injected by renderInspectorModalTools -->
    </div>

    ${
      item.prompts && item.prompts.length > 0
        ? `
      <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: var(--text);">Prompts (${item.prompts.length})</h3>
      ${item.prompts
        .map(
          (p) => `
        <div class="tool-detail-card">
          <div class="tool-detail-title">${escapeHtml(p.name)}</div>
          <div class="tool-detail-desc">${escapeHtml(p.description || "No description provided.")}</div>
        </div>
      `,
        )
        .join("")}
    `
        : ""
    }

    ${
      item.resources && item.resources.length > 0
        ? `
      <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: var(--text);">Resources (${item.resources.length})</h3>
      ${item.resources
        .map(
          (r) => `
        <div class="tool-detail-card">
          <div class="tool-detail-title">${escapeHtml(r.name || r.uri_template || "Unnamed Resource")}</div>
          <div class="tool-detail-desc">${escapeHtml(r.description || "No description provided.")}</div>
          ${r.uri_template ? `<div style="font-size:0.82rem; color:var(--text-muted); font-family:monospace;">URI Template: <code>${escapeHtml(r.uri_template)}</code></div>` : ""}
        </div>
      `,
        )
        .join("")}
    `
        : ""
    }

    <h3 style="margin-top: 2rem; margin-bottom: 0.75rem; color: var(--text);">Export Configuration</h3>
    <div class="copy-buttons-group">
      <button class="btn-copy" style="max-width: 140px;" onclick="copyConfig('${escapeHtml(item.name)}', '${escapeHtml(item.ecosystem)}', '${escapeHtml(vData.command || item.command || item.name)}', 'claude', this)">Copy Claude</button>
      <button class="btn-copy" style="max-width: 140px;" onclick="copyConfig('${escapeHtml(item.name)}', '${escapeHtml(item.ecosystem)}', '${escapeHtml(vData.command || item.command || item.name)}', 'cursor', this)">Copy Cursor</button>
      <button class="btn-copy" style="max-width: 140px;" onclick="copyConfig('${escapeHtml(item.name)}', '${escapeHtml(item.ecosystem)}', '${escapeHtml(vData.command || item.command || item.name)}', 'cline', this)">Copy Cline</button>
      <button class="btn-copy" style="max-width: 140px;" onclick="copyConfig('${escapeHtml(item.name)}', '${escapeHtml(item.ecosystem)}', '${escapeHtml(vData.command || item.command || item.name)}', 'zed', this)">Copy Zed</button>
      <button class="btn-copy" style="max-width: 140px;" onclick="copyConfig('${escapeHtml(item.name)}', '${escapeHtml(item.ecosystem)}', '${escapeHtml(vData.command || item.command || item.name)}', 'windsurf', this)">Copy Windsurf</button>
    </div>
  `;

  body.innerHTML = html;
  renderInspectorModalTools(targetToolName);
}

function renderInspectorModalTools(targetToolName) {
  const container = document.getElementById("inspectorToolsContainer");
  if (!container || !currentInspectorServer) return;

  const vData = getVersionData(
    currentInspectorServer,
    currentInspectorVersion,
  );
  const tools = vData.tools || [];
  const q = currentInspectorToolFilter.toLowerCase().trim();

  const filtered = tools.filter((t) => {
    if (!q) return true;
    if (t.name.toLowerCase().includes(q)) return true;
    if (t.description && t.description.toLowerCase().includes(q)) return true;
    if (
      t.parameters &&
      t.parameters.some(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          (p.description && p.description.toLowerCase().includes(q)),
      )
    ) {
      return true;
    }
    return false;
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div style="padding: 1.5rem; text-align: center; color: var(--text-muted); background: #090d16; border-radius: 8px;">No tools match "${escapeHtml(q)}"</div>`;
    return;
  }

  container.innerHTML = filtered
    .map((t) => {
      const isTarget = targetToolName && t.name === targetToolName;
      let paramsTable = "";
      if (t.parameters && t.parameters.length > 0) {
        paramsTable = `
        <table class="schema-table">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Type</th>
              <th>Required</th>
              <th>Default</th>
              <th>Enum</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            ${t.parameters
              .map(
                (p) => `
              <tr>
                <td class="param-name">${escapeHtml(p.name)}</td>
                <td>${escapeHtml(p.type || "string")}${p.items_type ? ` of ${escapeHtml(p.items_type)}` : ""}</td>
                <td>${p.required ? '<span style="color:#f87171; font-weight:700;">Yes</span>' : '<span style="color:var(--text-dim);">No</span>'}</td>
                <td>${p.default !== undefined && p.default !== null ? `<code>${escapeHtml(JSON.stringify(p.default))}</code>` : "-"}</td>
                <td>${p.enum && p.enum.length > 0 ? escapeHtml(p.enum.join(", ")) : "-"}</td>
                <td>${escapeHtml(p.description || "-")}</td>
              </tr>
            `,
              )
              .join("")}
          </tbody>
        </table>
      `;
      } else {
        paramsTable = `<div style="font-size: 0.8rem; color: var(--text-dim); margin-top: 0.4rem;">No parameters required for this tool.</div>`;
      }

      return `
      <div class="tool-detail-card" style="${isTarget ? "border-color: var(--accent); box-shadow: 0 0 12px var(--accent-glow);" : ""}">
        <div class="tool-detail-title">${escapeHtml(t.name)}</div>
        <div class="tool-detail-desc">${escapeHtml(t.description || "No description provided.")}</div>
        ${paramsTable}
      </div>
    `;
    })
    .join("");
}

function closeInspectorModal() {
  const modal = document.getElementById("inspectorModal");
  if (modal) modal.classList.remove("show");
}

// Global window clicks to close modals
window.addEventListener("click", (e) => {
  const inspector = document.getElementById("inspectorModal");
  if (e.target === inspector) {
    closeInspectorModal();
  }
  const configModal = document.getElementById("configModal");
  if (e.target === configModal) {
    closeConfigModal();
  }
});
