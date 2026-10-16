import json, glob
count = 0
for f in glob.glob("data/fingerprints/*.json"):
    try:
        data = json.load(open(f))
        if data.get("versions"):
            v = data["versions"][0]
            if "required_env_vars" in v:
                print("Found required_env_vars in version:", v["required_env_vars"])
                count += 1
                if count >= 3: break
    except: pass
