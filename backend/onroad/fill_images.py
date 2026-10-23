"""
Fills in images for active models that still have none, from each model's OWN official page (models.url):
og:image / twitter:image first, else the largest image whose file name mentions the model. Logos, icons and tiny
thumbnails are skipped; an image another model already uses is never reused. Runs after every refresh.
    python -m onroad.fill_images
"""
from __future__ import annotations

import html as _html
import io
import re
import time
from contextlib import closing
from urllib.parse import urljoin

import httpx

from . import db
from .sources.base import USER_AGENT

H = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN"}
SKIP = re.compile(r"logo|icon|favicon|sprite|placeholder|avatar|dealer|banner-mobile|-mobile|thumb", re.I)


def _width(client: httpx.Client, url: str) -> int:
    from PIL import Image
    try:
        return Image.open(io.BytesIO(client.get(url, timeout=25).content)).size[0]
    except Exception:
        return 0


def candidates(page: str, page_url: str, name: str) -> list[str]:
    h = _html.unescape(page)
    out = [m.group(1) for m in re.finditer(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)', h)]
    words = [w for w in re.split(r"[^a-z0-9]+", name.lower()) if len(w) >= 3]
    for u in re.findall(r'(?:src|data-src|href)=["\']([^"\']+\.(?:png|webp|jpe?g)(?:\?[^"\']*)?)["\']', h):
        fname = u.split("?")[0].rsplit("/", 1)[-1].lower()
        if any(w in fname for w in words):
            out.append(u)
    return [urljoin(page_url, u) for u in dict.fromkeys(out) if not SKIP.search(u.split("?")[0].rsplit("/", 1)[-1])]


COMMONS = "https://commons.wikimedia.org/w/api.php"
CREDITS = db.ROOT / "data" / "image_credits.md"


def commons(client: httpx.Client, brand: str, name: str) -> tuple[str, str] | None:
    """Freely licensed photo from Wikimedia Commons whose title names the brand and the model; (url, credit line)."""
    r = client.get(COMMONS, params={"action": "query", "generator": "search", "gsrsearch": f"{brand} {name} filetype:bitmap",
                                     "gsrnamespace": 6, "gsrlimit": 10, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
                                     "iiurlwidth": 1200, "format": "json"}, timeout=30)
    words = [w for w in re.split(r"[^a-z0-9]+", f"{brand} {name}".lower()) if len(w) >= 3]
    for page in sorted((r.json().get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        title = page.get("title", "").lower()
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        lic = (meta.get("LicenseShortName") or {}).get("value", "")
        norm = lambda t: re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
        if f" {norm(brand)} {norm(name)} " not in f" {norm(title)} " or info.get("width", 0) < 800 or not re.search(r"CC|Public domain", lic, re.I):
            continue
        author = re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "unknown"))
        return info.get("thumburl") or info["url"], f"{page['title']} by {author.strip()}, {lic}, {info.get('descriptionurl')}"
    return None


def dedupe() -> int:
    """No two models share one picture: keep a shared image on the model whose slug best matches the file name
    (else the shortest name) and clear it on the others, so they get their own image below."""
    cleared = 0
    with closing(db.connect()) as conn, conn:
        for (url,) in conn.execute("""SELECT image_url FROM models WHERE active = 1 AND image_url IS NOT NULL
                                      GROUP BY image_url HAVING COUNT(*) > 1""").fetchall():
            ids = [r[0] for r in conn.execute("SELECT id FROM models WHERE active = 1 AND image_url = ?", (url,))]
            fname = url.split("?")[0].rsplit("/", 1)[-1].lower()
            keep = max(ids, key=lambda i: (i.split("/", 1)[1].replace("-", "") in fname.replace("-", "").replace("_", ""), -len(i)))
            for i in ids:
                if i != keep:
                    conn.execute("UPDATE models SET image_url = NULL WHERE id = ?", (i,)); cleared += 1
    return cleared


def run() -> dict:
    cleared = dedupe()
    with closing(db.connect()) as conn:
        todo = conn.execute("SELECT id, name, url FROM models WHERE active = 1 AND (image_url IS NULL OR image_url = '') AND url LIKE 'http%'").fetchall()
        used = {r[0] for r in conn.execute("SELECT image_url FROM models WHERE image_url IS NOT NULL")}
    filled = []
    with httpx.Client(headers=H, follow_redirects=True) as client:
        for mid, name, url in todo:
            try:
                page = client.get(url, timeout=30).text
            except Exception:
                continue
            for c in candidates(page, url, name):
                if c in used:
                    continue
                if _width(client, c) >= 600:
                    with closing(db.connect()) as conn, conn:
                        conn.execute("UPDATE models SET image_url = ? WHERE id = ?", (c, mid))
                    used.add(c); filled.append(mid)
                    break
                time.sleep(0.4)
            time.sleep(0.8)
        # second pass: models with no usable image on their official page -> Wikimedia Commons (free licence, credited)
        with closing(db.connect()) as conn:
            left = conn.execute("""SELECT m.id, m.name, b.name FROM models m JOIN brands b ON b.slug = m.brand_slug
                                   WHERE m.active = 1 AND (m.image_url IS NULL OR m.image_url = '')""").fetchall()
        for mid, name, brand in left:
            try:
                got = commons(client, brand, name)
            except Exception:
                got = None
            if got and got[0] not in used:
                with closing(db.connect()) as conn, conn:
                    conn.execute("UPDATE models SET image_url = ? WHERE id = ?", (got[0], mid))
                with CREDITS.open("a", encoding="utf-8") as f:
                    f.write(f"- {mid}: {got[1]}" + chr(10))
                used.add(got[0]); filled.append(mid)
            time.sleep(0.5)
    return {"deduped": cleared, "missing": len(todo), "filled": len(filled), "still_missing": [m for m, _, _ in todo if m not in filled]}


if __name__ == "__main__":
    print(run())
