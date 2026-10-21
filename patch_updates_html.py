with open("web/updates.html", "r") as f:
    content = f.read()

old_str = """      <div style="display: flex; gap: 1rem; align-items: center;">
        <label for="releaseSelect" style="font-weight: 600; color: var(--text-muted);">Release Version:</label>
        <select id="releaseSelect" style="padding: 0.5rem; border-radius: 6px; background: var(--bg); border: 1px solid var(--border); color: var(--text);">
          <option value="latest">Loading...</option>
        </select>
      </div>"""

new_str = """      <div style="display: flex; gap: 1rem; align-items: center;">
        <label for="releaseSelect" style="font-weight: 600; color: var(--text-muted);">Release Version:</label>
        <select id="releaseSelect" style="padding: 0.5rem; border-radius: 6px; background: var(--bg); border: 1px solid var(--border); color: var(--text);">
          <option value="latest">Loading...</option>
        </select>
        <label class="filter-checkbox" style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; color: var(--text-muted); font-size: 0.9rem;">
          <input type="checkbox" id="filterToolsOnly" style="accent-color: var(--accent); width: 1.1rem; height: 1.1rem; cursor: pointer;"> Has Tools Only
        </label>
      </div>"""

if old_str in content:
    content = content.replace(old_str, new_str)
else:
    print("WARNING: Could not find target HTML in updates.html")

with open("web/updates.html", "w") as f:
    f.write(content)
