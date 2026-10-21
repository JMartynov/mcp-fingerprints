with open("web/app.js", "r") as f:
    content = f.read()

# Add event listener
old_events = """const searchInput = document.getElementById("searchInput");
if (searchInput) {
  searchInput.addEventListener("input", (e) => {
    activeQuery = e.target.value;
    updateURLState();
    render();
  });
}"""

new_events = """const searchInput = document.getElementById("searchInput");
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
}"""

if old_events in content:
    content = content.replace(old_events, new_events)
else:
    print("WARNING: Could not find events block")

# Update render function
old_render = """function render() {
  const q = activeQuery.toLowerCase().trim();
  filteredCatalog = catalog.filter((item) => {"""

new_render = """function render() {
  const q = activeQuery.toLowerCase().trim();
  const filterToolsOnly = document.getElementById("filterToolsOnly")?.checked;

  filteredCatalog = catalog.filter((item) => {
    if (filterToolsOnly) {
      const activeVer = getActiveVersionForServer(item);
      const vData = getVersionData(item, activeVer);
      if (!vData.tools || vData.tools.length === 0) return false;
    }"""

if old_render in content:
    content = content.replace(old_render, new_render)
else:
    print("WARNING: Could not find filter logic")

with open("web/app.js", "w") as f:
    f.write(content)
