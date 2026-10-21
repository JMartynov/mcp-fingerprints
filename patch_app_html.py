with open("web/index.html", "r") as f:
    content = f.read()

old_str = """          <button class="filter-btn" data-filter="eco" data-val="generic">
            Generic
          </button>
        </div>"""

new_str = """          <button class="filter-btn" data-filter="eco" data-val="generic">
            Generic
          </button>
          <label class="filter-checkbox" style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; color: var(--text-muted); font-size: 0.9rem; margin-left: 1rem;">
            <input type="checkbox" id="filterToolsOnly" style="accent-color: var(--accent); width: 1.1rem; height: 1.1rem; cursor: pointer;"> Has Tools Only
          </label>
        </div>"""

if old_str in content:
    content = content.replace(old_str, new_str)
else:
    print("WARNING: Could not find target HTML in index.html")

with open("web/index.html", "w") as f:
    f.write(content)
