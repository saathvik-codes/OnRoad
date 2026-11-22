"""
Videos for each model: walkarounds, feature explainers and reviews, played in the app with YouTube's own embedded
player (embedding is what YouTube licenses; nothing is downloaded or re-hosted).

Where the IDs come from, in order:
  1. the maker's own model page (official films), when its robots.txt allows the page;
  2. CarDekho / BikeDekho's videos page for the model (robots.txt allows /<brand>/<model>/videos).
Every ID is checked with YouTube's oEmbed endpoint: it must still exist, allow embedding, and its title must name the
model. Up to 8 per model, official first.

    python -m onroad.video_sync [limit]
"""
from __future__ import annotations

import datetime as dt
import re
import sys
import time

import httpx

from . import db
from .brochure_specs import UA
from .gallery_sync import _allowed
from .resale import BRAND_SLUG, _slug

ID = re.compile(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/|"videoId":")([A-Za-z0-9_-]{11})')
PER_MODEL = 8


def _init(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS model_videos (model_id TEXT, video_id TEXT, title TEXT, channel TEXT,
                    official INTEGER DEFAULT 0, rank INTEGER, fetched_at TEXT, PRIMARY KEY (model_id, video_id))""")


def ids_in(html: str) -> list[str]:
    seen, out = set(), []
    for v in ID.findall(html):
        if v not in seen:
            seen.add(v); out.append(v)
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _names_model(title: str, model: str, siblings: list[str] = ()) -> bool:
    """Title names this model (as a phrase) and no other model of the brand whose name isn't part of this one's
    (rejects a Tuono 457 video on the RS 457, a Creta N Line video on the Creta is allowed only if N Line isn't listed)."""
    t, m = _norm(title), _norm(model)
    if not m or m not in t:
        return False
    return not any(_norm(o) not in m and _norm(o) in t for o in siblings if len(_norm(o)) > 2 and _norm(o) != m)


def sync(limit: int | None = None) -> dict:
    conn = db.connect(); _init(conn)
    rows = conn.execute("""SELECT m.id, m.name, m.brand_slug, m.url, coalesce(m.vehicle_type, b.vehicle_type, 'car') FROM models m
                           JOIN brands b ON b.slug = m.brand_slug WHERE m.active = 1
                           ORDER BY (SELECT count(*) FROM model_videos v WHERE v.model_id = m.id), m.id""").fetchall()
    siblings: dict[str, list[str]] = {}
    for _, n, b, _, _ in rows:
        siblings.setdefault(b, []).append(n)
    done = kept = 0
    with httpx.Client(headers=UA, timeout=20, follow_redirects=True) as c:
        for mid, name, brand, url, vt in rows[:limit]:
            found: list[tuple[str, int]] = []
            if url and url.startswith("http") and _allowed(url):
                try:
                    found += [(v, 1) for v in ids_in(c.get(url).text)]
                except Exception:
                    pass
            site = "bikedekho" if vt == "bike" else "cardekho"
            page = f"https://www.{site}.com/{BRAND_SLUG.get(brand, _slug(brand.replace('_', ' ')))}/{_slug(name)}/videos"
            try:
                r = c.get(page)
                if r.status_code == 200:
                    found += [(v, 0) for v in ids_in(r.text)]
            except Exception:
                pass
            good = []
            for vid, official in found:
                if len(good) >= PER_MODEL or vid in {g[0] for g in good}:
                    continue
                try:
                    o = c.get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"})
                except Exception:
                    continue
                if o.status_code != 200:                    # removed, private or embedding disabled
                    continue
                j = o.json()
                if _names_model(j.get("title", ""), name, siblings.get(brand, [])):
                    good.append((vid, j["title"], j.get("author_name"), official))
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            conn.execute("DELETE FROM model_videos WHERE model_id = ?", (mid,))
            for rank, (vid, title, ch, off) in enumerate(sorted(good, key=lambda g: -g[3])):
                conn.execute("INSERT OR REPLACE INTO model_videos VALUES (?, ?, ?, ?, ?, ?, ?)", (mid, vid, title, ch, off, rank, now))
            conn.commit()
            done += 1; kept += len(good)
            time.sleep(1.0)                                   # gentle on every site
    return {"models": done, "videos": kept}


if __name__ == "__main__":
    print(sync(int(sys.argv[1]) if len(sys.argv) > 1 else None))
