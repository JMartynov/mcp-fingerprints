import json, glob
for f in glob.glob("data/fingerprints/*.json"):
    try:
        data = json.load(open(f))
        if "zoomeye" in f or "filesystem" in f:
            print(f, data.keys())
            if "versions" in data:
                print("version keys:", data["versions"][0].keys())
    except: pass
