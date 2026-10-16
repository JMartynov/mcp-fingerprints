with open("web/app.js", "r") as f:
    js = f.read()

# Add logic for Zed and Windsurf to copyConfig if not there
js = js.replace("""      if (client === "claude" || client === "cursor") {""", """      if (client === "claude" || client === "cursor" || client === "zed" || client === "windsurf") {""")

with open("web/app.js", "w") as f:
    f.write(js)
