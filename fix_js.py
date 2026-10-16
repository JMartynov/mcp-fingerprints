with open("web/app.js", "r") as f:
    js = f.read()

# Remove risk tier badge from card HTML
js = js.replace('<span class="badge badge-${item.risk_tier}">${item.risk_tier}</span>', '')

# Remove risk_tier from dummy fallback catalog
js = js.replace('risk_tier: "low",\n', '')
js = js.replace('risk_tier: "high",\n', '')

# Make card clickable to open inspector
# Wrap the title in an a-href or just an onclick
js = js.replace("""<div class="card-title">
                  <label class="checkbox-container" style="color:var(--text); font-size:1.15rem; font-weight:700;">
                    <input type="checkbox" class="server-checkbox" data-name="${item.name}" ${isChecked} onchange="toggleSelection('${item.name}')">
                    ${item.name}
                  </label>
                </div>""", """<div class="card-title">
                  <label class="checkbox-container" style="color:var(--text); font-size:1.15rem; font-weight:700;">
                    <input type="checkbox" class="server-checkbox" data-name="${item.name}" ${isChecked} onchange="toggleSelection('${item.name}')">
                    <span style="cursor:pointer;" onclick="openInspectorModal('${item.name}')" title="Click for details">${item.name}</span>
                  </label>
                </div>""")

with open("web/app.js", "w") as f:
    f.write(js)
