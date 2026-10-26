import re
import json

def test():
    with open('web/updates/latest_update.json', 'r') as f:
        updates = json.load(f)
    print(f"Updates servers count: {len(updates.get('servers', []))}")
    
    with open('web/catalog.json', 'r') as f:
        catalog = json.load(f)
    print(f"Catalog length: {len(catalog)}")
test()
