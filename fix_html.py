import re

with open("web/index.html", "r") as f:
    html = f.read()

# Remove --risk-* variables
html = re.sub(r'\s*--risk-low:.*?;', '', html)
html = re.sub(r'\s*--risk-med:.*?;', '', html)
html = re.sub(r'\s*--risk-high:.*?;', '', html)
html = re.sub(r'\s*--risk-crit:.*?;', '', html)

# Remove .badge-low, .badge-medium, .badge-high, .badge-critical classes
html = re.sub(r'\s*\.badge-low\s*{.*?}', '', html)
html = re.sub(r'\s*\.badge-medium\s*{.*?}', '', html)
html = re.sub(r'\s*\.badge-high\s*{.*?}', '', html)
html = re.sub(r'\s*\.badge-critical\s*{.*?}', '', html)

# Update #collisionWarning border color to use orange instead of var(--risk-high)
html = html.replace('border: 1px solid var(--risk-high);', 'border: 1px solid #f97316;')
html = html.replace('color: var(--risk-high);', 'color: #f97316;')

with open("web/index.html", "w") as f:
    f.write(html)
