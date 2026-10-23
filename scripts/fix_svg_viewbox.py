import re
from pathlib import Path

ROOT = Path('.').resolve()
if ROOT.name == 'backend': ROOT = ROOT.parent
LOGOS = ROOT / 'data' / 'logos'

items = [
    ('tvs', '375', '160'),
    ('ktm', '779.52753', '305.65234'),
    ('triumph', '500', '137'),
    ('suzuki_2wheelers', '195.81648', '131.24602')
]

for s, w, h in items:
    f = LOGOS / f'{s}.svg'
    txt = f.read_text(encoding='utf-8', errors='ignore')
    if 'viewBox' not in txt and 'viewbox' not in txt:
        new_txt = re.sub(r'<svg', f'<svg viewBox="0 0 {w} {h}"', txt, count=1)
        f.write_text(new_txt, encoding='utf-8')
        print(f'Added viewBox to {s}.svg')
    else:
        print(f'{s}.svg already has viewBox')
