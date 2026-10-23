import urllib.request
import json

models = [
    ('mahindra', 'scorpio-n'),
    ('mahindra', 'thar'),
    ('tata', 'nexon'),
    ('hyundai', 'creta'),
    ('kia', 'seltos'),
    ('maruti_suzuki', 'swift'),
    ('royal_enfield', 'hunter_350'),
    ('royal_enfield', 'hunter-350'),
    ('tvs', 'raider-125'),
    ('tvs', 'raider_125')
]

for b, m in models:
    try:
        url = f'http://127.0.0.1:8100/api/models/{b}/{m}'
        data = json.loads(urllib.request.urlopen(url).read())
        g_len = len(data.get("gallery") or [])
        has_img = bool(data.get("image_url"))
        name = data.get("name")
        print(f"{b}/{m} -> OK: {name} (gallery: {g_len}, image_url: {has_img})")
    except Exception as e:
        print(f"{b}/{m} -> ERROR: {e}")
