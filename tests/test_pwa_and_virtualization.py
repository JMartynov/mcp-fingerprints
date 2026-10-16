import json
import re
from pathlib import Path
from scripts.generate_web_catalog import compile_web_catalog


def test_manifest_validity():
    manifest_path = Path("web/manifest.json")
    assert manifest_path.exists()
    content = json.loads(manifest_path.read_text())
    assert "name" in content
    assert "start_url" in content
    assert "display" in content


def test_sw_version_injection(tmp_path):
    out_dir = tmp_path / "web"
    out_dir.mkdir()
    sw_path = out_dir / "sw.js"
    sw_path.write_text("const CACHE_NAME = 'mcp-catalog-v__CACHE_VERSION__';")

    passports_dir = tmp_path / "data"
    passports_dir.mkdir()

    compile_web_catalog(str(passports_dir), str(out_dir))

    sw_content = sw_path.read_text()
    assert "__CACHE_VERSION__" not in sw_content
    assert re.search(r"mcp-catalog-v\d+", sw_content) is not None


def test_virtual_range_calculation(tmp_path):
    app_js_path = Path("web/app.js")
    content = app_js_path.read_text()

    match = re.search(
        r"function getVisibleRange\([^)]*\)\s*{[^}]*}", content, re.DOTALL
    )
    assert match is not None
    # We add the missing semicolon/closing brace logic if needed, but looking at our regex, it might have missed the closing brace due to nested braces? Wait, no nested braces in that function. Oh, the regex `{[^}]*}` might match up to the first closing brace, which is fine since the function only has one closing brace. Wait, `return { startIndex, endIndex };` has a nested brace!

    func_code = """
function getVisibleRange(scrollTop, containerHeight, itemHeight, itemCount, columns) {
  const buffer = 2; // Buffer rows
  const GAP = 20;
  const totalItemHeight = itemHeight + GAP;
  const startRow = Math.max(0, Math.floor(scrollTop / totalItemHeight) - buffer);
  const visibleRows = Math.ceil(containerHeight / totalItemHeight) + (buffer * 2);
  
  const startIndex = startRow * columns;
  const endIndex = Math.min(itemCount, startIndex + (visibleRows * columns));
  
  return { startIndex, endIndex };
}
"""
    # But wait, we should test the ACTUAL code from app.js. Let's fix the regex.
    match = re.search(
        r"function getVisibleRange\([^)]*\)\s*{.*?\n\s*}", content, re.DOTALL
    )
    assert match is not None
    func_code = match.group(0)

    # We can evaluate this function via a simple embedded node.js script
    import subprocess

    node_script = f"""
    const GAP = 20;
    {func_code}
    
    console.log(JSON.stringify([
      getVisibleRange(0, 800, 280, 100, 3),
      getVisibleRange(600, 800, 280, 100, 3),
      getVisibleRange(1500, 800, 280, 100, 3)
    ]));
    """
    script_path = tmp_path / "test.js"
    script_path.write_text(node_script)

    result = subprocess.run(
        ["node", str(script_path)], capture_output=True, text=True, check=True
    )
    ranges = json.loads(result.stdout)

    assert ranges[0]["startIndex"] == 0
    assert ranges[0]["endIndex"] == 21

    assert ranges[1]["startIndex"] == 0
    assert ranges[1]["endIndex"] == 21

    assert ranges[2]["startIndex"] == 9
