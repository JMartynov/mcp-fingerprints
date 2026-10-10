    let catalog = [];
    let activeEco = "all";
    let activeQuery = "";
    let selectedServers = new Map();
    let activeModalClient = "claude";

    async function loadCatalog() {
      try {
        const resp = await fetch("catalog.json");
        if (!resp.ok) throw new Error("Catalog file not found");
        catalog = await resp.json();
      } catch (err) {
        console.warn("Could not load catalog.json, using fallback sample data:", err);
        catalog = [
          {
            name: "@modelcontextprotocol/server-filesystem",
            ecosystem: "npm",
            version: "1.0.0",
            description: "Direct local filesystem reader and writer toolset for Claude and Cursor.",
            tool_count: 5,
            tools: [{name: "read_file"}, {name: "write_file"}, {name: "list_directory"}],
            risk_tier: "low",
            command: "npx -y @modelcontextprotocol/server-filesystem"
          },
          {
            name: "postgres-mcp-server",
            ecosystem: "pypi",
            version: "1.2.0",
            description: "Execute read and write SQL statements against PostgreSQL databases.",
            tool_count: 4,
            tools: [{name: "execute_query"}, {name: "list_tables"}],
            risk_tier: "high",
            command: "uvx postgres-mcp-server"
          }
        ];
      }
      render();
    }

    function render() {
      const q = activeQuery.toLowerCase().trim();
      const filtered = catalog.filter(item => {
        if (activeEco !== "all" && item.ecosystem.toLowerCase() !== activeEco) return false;
        if (!q) return true;
        if (item.name.toLowerCase().includes(q)) return true;
        if (item.description.toLowerCase().includes(q)) return true;
        return item.tools.some(t => t.name.toLowerCase().includes(q));
      });

      document.getElementById("metricsDisplay").innerText = 
        `Showing ${filtered.length.toLocaleString()} of ${catalog.length.toLocaleString()} MCP servers`;

      const grid = document.getElementById("serverGrid");
      grid.innerHTML = "";

      filtered.slice(0, 100).forEach(item => {
        const card = document.createElement("div");
        card.className = "card";
        
        const safeKey = item.name.replace(/[@/_]/g, "-");
        card.id = 'server-' + safeKey;
        const displayedTools = item.tools.slice(0, 6);

        const isChecked = selectedServers.has(item.name) ? 'checked' : '';
        card.innerHTML = `
          <div>
            <div class="card-header">
              <div class="card-title">
                <label class="checkbox-container" style="color:var(--text); font-size:1.15rem; font-weight:700;">
                  <input type="checkbox" class="server-checkbox" data-name="${item.name}" ${isChecked} onchange="toggleSelection('${item.name}')">
                  ${item.name}
                </label>
              </div>
              <div style="display: flex; gap: 0.35rem; align-items: center; flex-wrap: wrap; justify-content: flex-end;">
                <span class="badge badge-eco">${item.ecosystem}</span>
                <span class="badge badge-${item.risk_tier}">${item.risk_tier}</span>
                ${(item.advisory_count > 0 || (item.advisories && item.advisories.length > 0)) ? 
                    `<span class="badge badge-advisory" title="${(item.advisories || []).map(a => a.id).join(', ')}">
                      ⚠️ ${item.advisory_count || item.advisories.length} Advisory
                    </span>` : ''}
              </div>
            </div>
            <div class="card-desc">${item.description || "No description provided."}</div>
            ${(item.advisories && item.advisories.length > 0) ? `
              <div class="advisories-list" style="margin-bottom: 0.75rem; font-size: 0.8rem;">
                <strong>Advisories:</strong> 
                ${item.advisories.map(a => `<a href="https://osv.dev/vulnerability/${a.id || a}" target="_blank" style="color: var(--risk-crit); margin-right: 0.5rem;">${a.id || a}</a>`).join("")}
              </div>
            ` : ""}
            
            ${item.tool_count > 0 ? `
              <div class="tools-section">
                <div class="tools-label">Tools (${item.tool_count})</div>
                <div class="tool-tags">
                  ${displayedTools.map(t => `<span class="tool-tag">${t.name}</span>`).join("")}
                  ${item.tool_count > 6 ? `<span class="tool-tag">+${item.tool_count - 6} more</span>` : ""}
                </div>
              </div>
            ` : `<div style="font-size:0.8rem; color:var(--text-muted); margin-bottom: 0.5rem;">Zero static tools recorded</div>`}
          </div>

          <div class="card-actions">
            <button class="btn-copy" onclick="copyShareLink('${item.name}', this)" title="Copy Share Link">🔗</button>
            <button class="btn-copy" onclick="copyConfig('${item.name}', '${item.ecosystem}', '${item.command}', 'claude', this)">Claude</button>
            <button class="btn-copy" onclick="copyConfig('${item.name}', '${item.ecosystem}', '${item.command}', 'cursor', this)">Cursor</button>
            <button class="btn-copy" onclick="copyConfig('${item.name}', '${item.ecosystem}', '${item.command}', 'cline', this)">Cline</button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function copyConfig(name, eco, cmd, client, btn) {
      const safeKey = name.replace(/[@/_]/g, "-");
      const parts = cmd.split(" ");
      const command = parts[0] || (eco === "pypi" ? "uvx" : "npx");
      const args = parts.slice(1);

      let payload = {};
      if (client === "claude" || client === "cursor") {
        payload = {
          mcpServers: {
            [safeKey]: { command, args }
          }
        };
      } else if (client === "cline") {
        payload = {
          mcpServers: {
            [safeKey]: { command, args, disabled: false, autoApprove: [] }
          }
        };
      }

      navigator.clipboard.writeText(JSON.stringify(payload, null, 2)).then(() => {
        showToast();
        btn.classList.add("copied");
        setTimeout(() => btn.classList.remove("copied"), 1500);
      });
    }

    function showToast() {
      const t = document.getElementById("toast");
      t.classList.add("show");
      setTimeout(() => t.classList.remove("show"), 2000);
    }

    function updateURLState() {
      const url = new URL(window.location);
      if (activeQuery) {
        url.searchParams.set('q', activeQuery);
      } else {
        url.searchParams.delete('q');
      }
      if (activeEco !== 'all') {
        url.searchParams.set('eco', activeEco);
      } else {
        url.searchParams.delete('eco');
      }
      history.replaceState(null, '', url);
    }

    document.getElementById("searchInput").addEventListener("input", e => {
      activeQuery = e.target.value;
      updateURLState();
      render();
    });

    document.querySelectorAll(".filter-btn").forEach(btn => {
      btn.addEventListener("click", e => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        e.target.classList.add("active");
        activeEco = e.target.getAttribute("data-val");
        updateURLState();
        render();
      });
    });

    function initFromURL() {
      const params = new URLSearchParams(window.location.search);
      const hashParams = new URLSearchParams(window.location.hash.slice(1));
      
      const q = params.get('q') || hashParams.get('q');
      const eco = params.get('eco') || hashParams.get('eco');
      
      if (q) {
        activeQuery = q;
        document.getElementById('searchInput').value = q;
      }
      
      if (eco) {
        activeEco = eco;
        document.querySelectorAll('.filter-btn').forEach(b => {
          if (b.getAttribute('data-val') === eco) {
            b.classList.add('active');
          } else {
            b.classList.remove('active');
          }
        });
      }
    }

    initFromURL();
    loadCatalog().then(() => {
        const params = new URLSearchParams(window.location.search);
        const hashParams = new URLSearchParams(window.location.hash.slice(1));
        const targetServer = params.get('server') || hashParams.get('server');
        
        if (targetServer) {
            setTimeout(() => {
                const el = document.getElementById('server-' + targetServer.replace(/[@/_]/g, "-"));
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    el.classList.add('highlight-card');
                    setTimeout(() => el.classList.remove('highlight-card'), 2000);
                }
            }, 100);
        }
    });

    function toggleSelection(name) {
      if (selectedServers.has(name)) {
        selectedServers.delete(name);
      } else {
        const item = catalog.find(i => i.name === name);
        if (item) selectedServers.set(name, item);
      }
      updateDrawer();
    }

    function updateDrawer() {
      const drawer = document.getElementById("bottomDrawer");
      const count = document.getElementById("selectedCount");
      count.innerText = selectedServers.size;
      if (selectedServers.size > 0) {
        drawer.classList.add("show");
      } else {
        drawer.classList.remove("show");
      }
    }

    function detectCollisions() {
      const toolMap = new Map();
      const collisions = new Map();

      selectedServers.forEach(server => {
        if (!server.tools) return;
        server.tools.forEach(tool => {
          if (!toolMap.has(tool.name)) {
            toolMap.set(tool.name, [server.name]);
          } else {
            const servers = toolMap.get(tool.name);
            servers.push(server.name);
            collisions.set(tool.name, servers);
          }
        });
      });

      return collisions;
    }

    function updateCollisionUI(collisions) {
      const warningDiv = document.getElementById("collisionWarning");
      const listElement = document.getElementById("collisionList");
      
      if (collisions.size > 0) {
        listElement.innerHTML = "";
        collisions.forEach((servers, toolName) => {
          const li = document.createElement("li");
          li.innerHTML = `Tool <code>${toolName}</code> is declared in: ${servers.join(", ")}`;
          listElement.appendChild(li);
        });
        warningDiv.classList.add("show");
      } else {
        warningDiv.classList.remove("show");
      }
    }

    function generateCombinedConfig(client) {
      let mcpServers = {};
      
      selectedServers.forEach(item => {
        const safeKey = item.name.replace(/[@/_]/g, "-");
        const parts = (item.command || "").split(" ");
        const command = parts[0] || (item.ecosystem === "pypi" ? "uvx" : "npx");
        const args = parts.slice(1);
        
        if (client === "claude" || client === "cursor" || client === "zed" || client === "windsurf") {
          mcpServers[safeKey] = { command, args };
        } else if (client === "cline") {
          mcpServers[safeKey] = { command, args, disabled: false, autoApprove: [] };
        } else if (client === "docker") {
           mcpServers[safeKey] = {
             command: "docker",
             args: ["run", "-i", "--rm", item.name]
           };
        }
      });
      
      return { mcpServers };
    }

    function updateConfigOutput() {
      const config = generateCombinedConfig(activeModalClient);
      document.getElementById("configOutput").innerText = JSON.stringify(config, null, 2);
    }

    function switchTab(client) {
      activeModalClient = client;
      document.querySelectorAll(".tab-btn").forEach(btn => {
        if (btn.getAttribute("data-client") === client) {
          btn.classList.add("active");
        } else {
          btn.classList.remove("active");
        }
      });
      updateConfigOutput();
    }

    function openConfigModal() {
      const collisions = detectCollisions();
      updateCollisionUI(collisions);
      updateConfigOutput();
      document.getElementById("configModal").classList.add("show");
    }

    function closeConfigModal() {
      document.getElementById("configModal").classList.remove("show");
    }

    function copyCombinedConfig() {
      const text = document.getElementById("configOutput").innerText;
      navigator.clipboard.writeText(text).then(() => {
        showToast();
      });
    }

    function downloadCombinedConfig() {
      const text = document.getElementById("configOutput").innerText;
      const blob = new Blob([text], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "config.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    function copyShareLink(name, btn) {
      const url = new URL(window.location);
      url.searchParams.set('server', name);
      navigator.clipboard.writeText(url.toString()).then(() => {
        showToast();
        btn.classList.add("copied");
        setTimeout(() => btn.classList.remove("copied"), 1500);
      });
    }
