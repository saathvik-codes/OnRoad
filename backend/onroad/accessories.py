"""
Genuine accessories with prices, read from manufacturers' own accessory catalogues (robots.txt allows the pages and
feeds used). Stored in the `accessories` table and shown on each model's Insurance & RTA > Accessories tab; brands
whose catalogue can't be read keep a link to their accessories store instead.

    python -m onroad.accessories            # refresh every supported brand
"""
from __future__ import annotations

import re
import time
from contextlib import closing

import httpx

from . import db

UA = {"User-Agent": "Mozilla/5.0 (compatible; OnRoadBot/1.0; +https://onroad-frontend.onrender.com)"}


def _table(conn) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS accessories (model_id TEXT, code TEXT, name TEXT, category TEXT, price_inr INTEGER,
                    image_url TEXT, description TEXT, source_url TEXT, fetched_at TEXT, PRIMARY KEY (model_id, code))""")


def kia(c: httpx.Client) -> list[dict]:
    page = "https://www.kia.com/in/service/kia-owners/accessories.html"
    html = c.get(page).text
    models = re.findall(r'<option value="([A-Z0-9]{2})">([^<]+)</option>', html)
    out = []
    for code, name in models:
        n, total = 1, None
        while True:
            r = c.post("https://www.kia.com/api/kia2_in/accessories.getAccItems.do",
                       data={"pageNo": n, "pageSize": 60, "pageBlock": 5, "filter": f"all-{code}"},
                       headers={"Referer": page, "X-Requested-With": "XMLHttpRequest"})
            d = (r.json() or {}).get("data") or {}
            items = d.get("accList") or []
            total = d.get("total", 0)
            for it in items:
                out.append({"model_name": name.strip(), "code": it.get("accCode"), "name": re.sub(r"\s+", " ", it.get("accName") or it.get("introTitle") or "").strip(),
                            "category": it.get("accCategory"), "price_inr": it.get("partListPrice"),
                            "image_url": ("https://www.kia.com" + it["imgD"]) if it.get("imgD") else None,
                            "description": (it.get("introDesc") or "").strip(), "source_url": page})
            if not items or n * 60 >= total:
                break
            n += 1
            time.sleep(1)
        time.sleep(1)
    return out


READERS = {"kia": kia}


def _model_id(conn, brand: str, name: str) -> str | None:
    want = re.sub(r"[^a-z0-9]", "", re.sub(r"^new\s+", "", name.lower()))
    for mid, mname in conn.execute("SELECT id, name FROM models WHERE brand_slug = ? AND active = 1", (brand,)):
        have = re.sub(r"[^a-z0-9]", "", mname.lower())
        if have == want or have.endswith(want) or want.endswith(have):
            return mid
    for mid, mname in conn.execute("SELECT id, name FROM models WHERE brand_slug = ? AND active = 1", (brand,)):
        if want in re.sub(r"[^a-z0-9]", "", mname.lower()):
            return mid
    return None


def run() -> dict:
    db.init()
    res = {}
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with closing(db.connect()) as conn, httpx.Client(headers=UA, timeout=40, follow_redirects=True) as c:
        _table(conn)
        for brand, read in READERS.items():
            try:
                items = read(c)
            except Exception as e:
                res[brand] = f"error: {str(e)[:80]}"
                continue
            n = 0
            for it in items:
                mid = _model_id(conn, brand, it["model_name"])
                if not mid or not it["code"] or not it["name"]:
                    continue
                conn.execute("INSERT OR REPLACE INTO accessories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (mid, it["code"], it["name"], it["category"], it["price_inr"], it["image_url"], it["description"], it["source_url"], now))
                n += 1
            # items the maker no longer lists drop out
            conn.execute("DELETE FROM accessories WHERE model_id LIKE ? AND fetched_at < ?", (brand + "/%", now))
            conn.commit()
            res[brand] = n
    return res


def for_model(conn, model_id: str) -> list[dict]:
    try:
        return [dict(r) for r in conn.execute("""SELECT code, name, category, price_inr, image_url, description, source_url FROM accessories
                                                  WHERE model_id = ? ORDER BY category, price_inr""", (model_id,))]
    except Exception:
        return []


if __name__ == "__main__":
    print(run())
