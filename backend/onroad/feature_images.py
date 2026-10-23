"""
Feature photos from manufacturers' own model pages (e.g. VW 'sunroof-11', Kia 'ventilated-seats'), matched to OnRoad's
equipment keys by file name / alt text. Stored per model so a variant shows ITS model's real photo of a feature.
    python -m onroad.feature_images [brand_slug ...]
"""
from __future__ import annotations

import html as _html
import re
import sys
import time
from contextlib import closing
from urllib.parse import urljoin

import httpx

from . import db
from .sources.base import USER_AGENT, now

# feature key -> keywords looked for in the image file name / alt text (first match wins, most specific first)
KEYWORDS = [
    ("panoramic_sunroof", r"panoram"), ("sunroof", r"sun-?roof|sunroof"), ("camera_360", r"360|surround[- ]?view"),
    ("adas", r"adas|level-?2|lane[- ]?keep|collision"), ("ventilated_seats", r"ventilat|cooled[- ]?seat"),
    ("wireless_charger", r"wireless[- ]?charg"), ("ambient_lighting", r"ambient"), ("hud", r"head[- ]?up|hud"),
    ("digital_cluster", r"digital[- ]?(cluster|cockpit|instrument)|virtual[- ]?cockpit"),
    ("touchscreen", r"infotain|touch[- ]?screen|touchscreen"), ("premium_audio", r"bose|harman|jbl|sony|audio|speaker"),
    ("auto_climate", r"climat|auto[- ]?ac|air[- ]?care"), ("rear_ac_vents", r"rear[- ]?ac"),
    ("powered_driver_seat", r"power(ed)?[- ]?seat|electric[- ]?seat"), ("connected_car", r"connected|blue[- ]?link|i-?connect|uvo|adrenox"),
    ("airbags_6", r"airbag"), ("esc", r"\besc\b|stability"), ("hill_hold", r"hill[- ]?(start|hold|assist)"),
    ("tpms", r"tpms|tyre[- ]?pressure"), ("rear_camera", r"rear[- ]?(view[- ]?)?camera|reverse[- ]?camera"),
    ("cruise_control", r"cruise"), ("push_button_start", r"push[- ]?button|start[- ]?stop"), ("keyless_entry", r"keyless|smart[- ]?key"),
    ("led_headlamps", r"led[- ]?head|headlamp|headlight|light[- ]?band"), ("led_drl", r"\bdrl"), ("alloy_wheels", r"alloy|wheel"),
    ("fog_lamps", r"fog"), ("roof_rails", r"roof[- ]?rail"), ("electric_parking_brake", r"parking[- ]?brake|\bepb\b"),
]
SKIP = re.compile(r"logo|icon|banner|mobile|thumb|sprite|placeholder|brochure|dealer|test[- ]?drive|book", re.I)
H = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN"}


def classify(text: str) -> str | None:
    t = text.lower()
    for key, pat in KEYWORDS:
        if re.search(pat, t):
            return key
    return None


def harvest(page_url: str, client: httpx.Client) -> dict[str, tuple[str, str]]:
    """key -> (image_url, alt) for feature photos on one official model page."""
    h = _html.unescape(client.get(page_url, timeout=30).text)
    found: dict[str, tuple[str, str]] = {}
    for tag in re.findall(r"<img\b[^>]*>", h, re.I):
        src = re.search(r'\b(?:data-src|src)=["\']([^"\']+)["\']', tag)
        if not src:
            continue
        alt = (re.search(r'\balt=["\']([^"\']*)["\']', tag) or [None, ""])[1]
        u = urljoin(page_url, src.group(1))
        name = u.split("?")[0].rsplit("/", 1)[-1]
        if SKIP.search(name) or not re.search(r"\.(jpe?g|png|webp)|/is/image/", u, re.I):
            continue
        key = classify(name)          # file name only: carousel alt texts often describe a different slide
        if key and key not in found:
            found[key] = (u, alt)
    # images referenced outside <img> (JSON, srcset) on CDN paths with descriptive names
    for u in re.findall(r"https://[^\"'\s,)]+?/(?:is/image/[^\"'\s,)]+|[^\"'\s,)]+\.(?:jpe?g|png|webp))", h):
        name = u.split("?")[0].rsplit("/", 1)[-1]
        if SKIP.search(name):
            continue
        key = classify(name)
        if key and key not in found:
            found[key] = (u, "")
    return found


def run(only: list[str] | None = None) -> dict:
    db.init()
    with closing(db.connect()) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS feature_images (model_id TEXT, key TEXT, image_url TEXT, alt TEXT, source_url TEXT,
                        fetched_at TEXT, PRIMARY KEY (model_id, key))""")
        rows = conn.execute("SELECT m.id, m.url FROM models m JOIN brands b ON b.slug = m.brand_slug WHERE m.active = 1 AND m.url LIKE 'http%'"
                            + (f" AND m.brand_slug IN ({','.join('?' * len(only))})" if only else ""), tuple(only or ())).fetchall()
    total = 0
    with httpx.Client(headers=H, follow_redirects=True) as client:
        for mid, url in rows:
            try:
                found = harvest(url, client)
            except Exception as e:
                print(mid, "ERR", type(e).__name__)
                continue
            with closing(db.connect()) as conn, conn:
                for key, (img, alt) in found.items():
                    conn.execute("INSERT OR REPLACE INTO feature_images VALUES (?, ?, ?, ?, ?, ?)", (mid, key, img, alt, url, now()))
            total += len(found)
            print(mid, len(found), sorted(found))
            time.sleep(0.8)
    return {"models": len(rows), "images": total}


if __name__ == "__main__":
    print(run(sys.argv[1:] or None))
