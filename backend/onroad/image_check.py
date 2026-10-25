"""
Image health check: every picture address we store (model cut-outs, variant colour shots, gallery photos) is fetched
(the first few KB only) and dropped when the maker has removed it (404 / 410 / not an image), so carousels never show
"photo unavailable". A model whose main picture died takes its first working variant or gallery picture instead.
Site paths (/models/...) are checked against data/model_images.

    python -m onroad.image_check
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from . import db
from .brochure_specs import UA


def _alive(c: httpx.Client, u: str) -> bool:
    if u.startswith("/models/"):
        return (db.ROOT / "data" / "model_images" / u[len("/models/"):]).is_file()
    if not u.startswith("http"):
        return True                                  # other site paths are served by the web app
    for _ in range(2):
        try:
            with c.stream("GET", u) as r:
                if r.status_code in (404, 410):
                    return False
                if r.status_code != 200:
                    time.sleep(1); continue          # 403 / 429 / 5xx: not proof it's gone, keep it
                next(r.iter_bytes(2048), b"")
                return r.headers.get("content-type", "image/").startswith(("image/", "binary/", "application/octet-stream"))
        except Exception:
            time.sleep(1)
    return True


def run() -> dict:
    conn = db.connect()
    urls = set()
    for t, col in (("models", "image_url"), ("variants", "image_url"), ("model_gallery", "url")):
        urls |= {r[0] for r in conn.execute(f"SELECT DISTINCT {col} FROM {t} WHERE {col} IS NOT NULL AND {col} != ''")}
    with httpx.Client(headers=UA, timeout=20, follow_redirects=True) as c, ThreadPoolExecutor(8) as ex:
        dead = {u for u, ok in zip(urls, ex.map(lambda u: _alive(c, u), urls)) if not ok}
    n_g = n_v = n_m = 0
    for u in dead:
        n_g += conn.execute("DELETE FROM model_gallery WHERE url = ?", (u,)).rowcount
        n_v += conn.execute("UPDATE variants SET image_url = NULL WHERE image_url = ?", (u,)).rowcount
        for (mid,) in conn.execute("SELECT id FROM models WHERE image_url = ?", (u,)).fetchall():
            alt = conn.execute("""SELECT image_url FROM variants WHERE model_id = ? AND active = 1 AND image_url IS NOT NULL
                                  UNION ALL SELECT url FROM model_gallery WHERE model_id = ? LIMIT 1""", (mid, mid)).fetchone()
            conn.execute("UPDATE models SET image_url = ? WHERE id = ?", (alt[0] if alt else None, mid)); n_m += 1
    conn.commit()
    return {"checked": len(urls), "dead": len(dead), "gallery_removed": n_g, "variant_images_cleared": n_v, "models_repointed": n_m}


if __name__ == "__main__":
    print(json.dumps(run()))
