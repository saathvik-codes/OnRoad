"""
Keeps every model's photos its own. Image addresses usually name the car (".../hero/xoom-160/...",
".../new-magnite/TEKNA_VLP.png"), so a photo is removed from a model when its address names a different model of the
same brand and not this one, or when one address is shared by several models and does not name the one it is on.
A model left without a main photo takes the first remaining photo from its own gallery. Runs before every snapshot.
"""
from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

STOP = {"new", "the", "plus", "pro", "max", "edition", "special", "series", "ev", "electric", "hybrid", "strong", "s", "x",
        "e", "i", "n", "r", "t", "sport", "tech", "black", "dark", "launch"}


def _tokens(name: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (name or "").lower()) if t not in STOP and len(t) > 1}


def _path(url: str) -> str:
    p = unquote(urlparse(url).path).lower()
    return " " + re.sub(r"[^a-z0-9]+", " ", p) + " "


def _names(path: str, tokens: set[str]) -> bool:
    """Does the address name this model (every distinctive word of its name appears as a word)?"""
    compact = path.replace(" ", "")
    return bool(tokens) and all(f" {t} " in path or re.search(rf" {re.escape(t)}\d* ", path)
                                or (len(t) >= 5 and t in compact) for t in tokens)


def repair(conn, dry_run: bool = False) -> dict:
    models = conn.execute("SELECT id, brand_slug, name, image_url FROM models WHERE active = 1").fetchall()
    by_brand: dict[str, list] = {}
    for mid, b, name, img in models:
        by_brand.setdefault(b, []).append((mid, _tokens(name), img))

    def wrong(mid: str, brand: str, url: str, shared_with: int) -> bool:
        path = _path(url)
        own = next(t for m, t, _ in by_brand[brand] if m == mid)
        if _names(path, own):
            return False
        # names another model of this brand (its distinctive words, at least one word longer than 2 letters)
        if any(m != mid and t - own and _names(path, t) and max(map(len, t - own)) > 2 for m, t, _ in by_brand[brand]):
            return True
        return shared_with > 1                      # one generic picture used for several models

    n = {"main_cleared": 0, "gallery_removed": 0, "main_refilled": 0}
    shared = {}
    for mid, b, name, img in models:
        if img:
            shared[img] = shared.get(img, 0) + 1
    for mid, b, name, img in models:
        if img and not img.startswith("/models/") and wrong(mid, b, img, shared[img]):
            n["main_cleared"] += 1
            if not dry_run:
                conn.execute("UPDATE models SET image_url = NULL WHERE id = ?", (mid,))
        elif img and img.startswith("/models/") and shared[img] > 1 and not _names(_path(img), _tokens(name)):
            n["main_cleared"] += 1                   # our own cut-out of a sibling model
            if not dry_run:
                conn.execute("UPDATE models SET image_url = NULL WHERE id = ?", (mid,))

    brand_of = {mid: b for mid, b, _, _ in models}
    g_shared = dict(conn.execute("SELECT url, COUNT(DISTINCT model_id) FROM model_gallery GROUP BY url").fetchall())
    for rowid, mid, url in conn.execute("SELECT rowid, model_id, url FROM model_gallery").fetchall():
        if mid in brand_of and wrong(mid, brand_of[mid], url, g_shared.get(url, 1)):
            n["gallery_removed"] += 1
            if not dry_run:
                conn.execute("DELETE FROM model_gallery WHERE rowid = ?", (rowid,))
    if not dry_run:
        for (mid,) in conn.execute("SELECT id FROM models WHERE active = 1 AND (image_url IS NULL OR image_url = '')").fetchall():
            g = conn.execute("SELECT url FROM model_gallery WHERE model_id = ? ORDER BY rowid LIMIT 1", (mid,)).fetchone()
            if g:
                conn.execute("UPDATE models SET image_url = ? WHERE id = ?", (g[0], mid))
                n["main_refilled"] += 1
    return n
