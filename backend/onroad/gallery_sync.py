"""
Photo galleries for each model from its own page (manufacturer site, or BikeDekho for models sourced there), so every
car and bike has a carousel, not just one cut-out.

A picture is kept only when:
  * it is a jpg / png / webp served by the page's site or its media CDN (brochure_specs._official);
  * its address or alt text names this model (navigation menus show other models' pictures; those never match);
  * it is not a logo, icon, badge, flag, thumbnail or placeholder, and is at least 640 px wide (checked by reading the
    image header, a few KB, not the whole file);
  * srcset entries collapse to the widest one; size variants of the same file count once.
Up to 12 per model, stored in model_gallery and appended to the API's gallery after the variant colour shots.

    python -m onroad.gallery_sync                # models with fewer than 4 pictures
    python -m onroad.gallery_sync jeep,tvs       # brands
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from . import db
from .brochure_specs import UA, _official

SKIP = re.compile(r"logo|icon|sprite|badge|flag|arrow|placeholder|loader|favicon|social|whatsapp|facebook|youtube|twitter|"
                  r"instagram|app-?store|play-?store|dealer|payment|qr|avatar|emoji|rating|star|ncap|award|offer|banner-?mob|"
                  r"/thumb|thumbnail|\.svg|\.gif|1x1|blank", re.I)
SMALL = re.compile(r"(?:[?&](?:w|width|imwidth)=(\d+))|(?:\.img\.(\d+)\.)|(?:/(\d{2,4})x\d{2,4}/)|(?:_(\d{2,4})x\d{2,4}\.)", re.I)
KIND = [(re.compile(r"interior|cabin|dashboard|seat|steering|console|infotainment|boot", re.I), "Interior"),
        (re.compile(r"exterior|front|rear|side|profile|3-?4|design|360", re.I), "Exterior")]
_robots: dict[str, RobotFileParser | None] = {}


def _allowed(url: str) -> bool:
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = RobotFileParser()
        try:
            r = httpx.get(base + "/robots.txt", headers=UA, timeout=15, follow_redirects=True)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except Exception:
            rp = None
        _robots[base] = rp
    rp = _robots[base]
    return True if rp is None else rp.can_fetch(UA["User-Agent"], url)


def _tokens(name: str) -> list[str]:
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) >= 3 and w not in ("new", "the", "all", "plus", "edition", "special")]
    return words or [re.sub(r"[^a-z0-9]", "", name.lower())]


def candidates(html: str, base: str, name: str) -> list[tuple[str, str]]:
    """[(url, alt)] of pictures on the page that name the model, widest srcset entry first."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    toks = _tokens(name)
    found: list[tuple[str, str]] = []

    def push(u: str, alt: str):
        u = urljoin(base, u.strip().replace("\\/", "/").replace("&amp;", "&"))
        if not re.search(r"\.(?:jpe?g|png|webp)(?:$|[?#.])", u, re.I) or SKIP.search(u) or SKIP.search(alt or ""):
            return
        hay = (urlparse(u).path + " " + (alt or "")).lower().replace("-", "").replace("_", "")
        if not any(t.replace("-", "") in hay for t in toks):
            return                                   # doesn't name this model: probably another model in a menu
        if not _official(u, base):
            return
        found.append((u, alt or ""))

    for tag in soup.find_all(["img", "source"]):
        alt = tag.get("alt") or tag.get("title") or ""
        srcset = tag.get("srcset") or tag.get("data-srcset") or ""
        if srcset:
            best = max((p.strip().split(" ") for p in srcset.split(",") if p.strip()),
                       key=lambda p: int(re.sub(r"\D", "", p[1]) or 0) if len(p) > 1 else 0)
            push(best[0], alt)
        for a in ("data-src", "data-lazy-src", "data-original", "src"):
            if tag.get(a) and not tag.get(a, "").startswith("data:"):
                push(tag[a], alt); break
    for m in soup.find_all("meta", property="og:image"):
        push(m.get("content", ""), name)
    for u in re.findall(r"""["'](https?:[^"'\s]+?\.(?:jpe?g|png|webp))["']""", html, re.I):
        push(u, "")
    return found


def _key(u: str) -> str:
    """Same picture in another size counts once: drop size markers from the path."""
    p = urlparse(u).path.lower()
    p = re.sub(r"\.img\.\d+\.\w+$|_\d{2,4}x\d{2,4}|/\d{2,4}x\d{2,4}/|-\d{2,4}x\d{2,4}", "", p)
    return re.sub(r"\.(?:jpe?g|png|webp)$", "", p)


def _width_ok(c: httpx.Client, u: str) -> bool:
    m = SMALL.search(u)
    if m and int(next(g for g in m.groups() if g)) < 640:
        return False
    try:
        from PIL import ImageFile
        with c.stream("GET", u) as r:
            if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
                return False
            p = ImageFile.Parser()
            for chunk in r.iter_bytes(8192):
                p.feed(chunk)
                if p.image:
                    return p.image.size[0] >= 640 and p.image.size[1] >= 300
                if r.num_bytes_downloaded > 400_000:
                    break
    except Exception:
        return False
    return False


def run(brands: list[str] | None = None, need_below: int = 4) -> dict:
    conn = db.connect()
    conn.execute("""CREATE TABLE IF NOT EXISTS model_gallery (model_id TEXT, url TEXT, label TEXT, kind TEXT, source_url TEXT,
                    fetched_at TEXT, PRIMARY KEY (model_id, url))""")
    rows = conn.execute("""SELECT m.id, m.name, m.url, m.image_url,
                             (SELECT COUNT(DISTINCT v.image_url) FROM variants v WHERE v.model_id = m.id AND v.active = 1 AND v.image_url IS NOT NULL)
                             + (SELECT COUNT(*) FROM model_gallery g WHERE g.model_id = m.id) AS pics
                           FROM models m WHERE m.active = 1 AND m.url IS NOT NULL
                           AND EXISTS (SELECT 1 FROM variants v WHERE v.model_id = m.id AND v.active = 1)""").fetchall()
    done, added = 0, 0
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        for mid, name, url, img, pics in rows:
            if brands and mid.split("/")[0] not in brands or pics >= need_below:
                continue
            if not _allowed(url):
                continue
            try:
                r = c.get(url)
            except Exception:
                continue
            if r.status_code != 200:
                continue
            seen = {_key(img)} if img else set()
            keep = []
            for u, alt in candidates(r.text, str(r.url), name):
                k = _key(u)
                if k in seen:
                    continue
                seen.add(k)
                if _width_ok(c, u):
                    label = next((lab for rx, lab in KIND if rx.search(u + " " + alt)), "Photo")
                    keep.append((u, (alt or label)[:80], label))
                if len(keep) >= 12:
                    break
            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            for u, alt, kind in keep:
                conn.execute("INSERT OR IGNORE INTO model_gallery VALUES (?, ?, ?, ?, ?, ?)", (mid, u, alt, kind, url, now))
            conn.commit()
            done += 1; added += len(keep)
            print(json.dumps({"model": mid, "added": len(keep)}), flush=True)
            time.sleep(2)
    return {"models": done, "pictures": added}


def _label(u: str) -> str:
    f = re.sub(r"-\d+$", "", urlparse(u).path.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    f = re.sub(r"[-_()]+", " ", f).strip()
    return f[:1].upper() + f[1:] if f else "Photo"


def aggregator(c: httpx.Client, mid: str, name: str, vehicle_type: str, model_url: str | None) -> list[tuple[str, str, str, str]]:
    """[(url, label, kind, page)] from CarDekho / BikeDekho photo pages, for models whose maker gives too few pictures.
    Only pictures filed under this model's own folder on their image server are taken."""
    from .online_specs import BRAND
    from .sources.brands._bd_fill import BD_BRAND
    brand, slug = mid.split("/", 1)
    toks = [t.replace("-", "") for t in _tokens(name)]
    out = []
    if vehicle_type == "bike":
        if model_url and "bikedekho.com" in model_url:
            page = model_url.rstrip("/") + "/images"
        else:
            page = f"https://www.bikedekho.com/{BD_BRAND.get(brand, brand.replace('_', '-'))}/{slug}/images"
        r = c.get(page)
        if r.status_code != 200 or re.search(r"-(?:bikes|scooters)/?$", str(r.url)):
            return []
        for u in dict.fromkeys(re.findall(r"(https://cdn\.bikedekho\.com/processedimages/[^\"'\s]+?\.(?:jpe?g|webp|png))", r.text)):
            folder = urlparse(u).path.split("/")[3] if len(urlparse(u).path.split("/")) > 3 else ""
            if any(t in folder.replace("-", "") for t in toks) and "/source/" in u or "/640X309/" in u and any(t in folder.replace("-", "") for t in toks):
                out.append((u, name, "Photo", page))
    else:
        page = f"https://www.cardekho.com/{BRAND.get(brand, brand.replace('_', '-'))}/{slug}/pictures"
        r = c.get(page)
        if r.status_code != 200:
            return []
        for u in dict.fromkeys(re.findall(r"(https://stimg\.cardekho\.com/images/car(ex|in)teriorimages/930x620/[^\"'\s]+?\.jpe?g)", r.text)):
            url, kind = u
            model_dir = urlparse(url).path.split("/")[5].lower().replace("-", "") if len(urlparse(url).path.split("/")) > 5 else ""
            if any(t in model_dir for t in toks):
                out.append((url, _label(url), "Exterior" if kind == "ex" else "Interior", page))
    ext = [x for x in out if x[2] != "Interior"][:9]
    return ext + [x for x in out if x[2] == "Interior"][:4]


def run_fallback(need_below: int = 4) -> dict:
    """Models still short of pictures after their maker's page: CarDekho / BikeDekho photo pages (robots allow them)."""
    conn = db.connect()
    rows = conn.execute("""SELECT m.id, m.name, COALESCE(b.vehicle_type, 'car'), m.url,
                             (SELECT COUNT(DISTINCT v.image_url) FROM variants v WHERE v.model_id = m.id AND v.active = 1 AND v.image_url IS NOT NULL)
                             + (SELECT COUNT(*) FROM model_gallery g WHERE g.model_id = m.id)
                           FROM models m JOIN brands b ON b.slug = m.brand_slug WHERE m.active = 1
                           AND EXISTS (SELECT 1 FROM variants v WHERE v.model_id = m.id AND v.active = 1)""").fetchall()
    n_models = n_pics = 0
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        for mid, name, vt, url, pics in rows:
            if pics >= need_below:
                continue
            try:
                got = aggregator(c, mid, name, vt, url)
            except Exception:
                got = []
            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            for u, label, kind, page in got:
                conn.execute("INSERT OR IGNORE INTO model_gallery VALUES (?, ?, ?, ?, ?, ?)", (mid, u, label, kind, page, now))
            conn.commit()
            n_models += bool(got); n_pics += len(got)
            print(json.dumps({"model": mid, "added": len(got)}), flush=True)
            time.sleep(2)
    return {"models": n_models, "pictures": n_pics}


if __name__ == "__main__":
    if sys.argv[1:] == ["--fallback"]:
        print(run_fallback())
    else:
        print(run(sys.argv[1].split(",") if len(sys.argv) > 1 else None))
