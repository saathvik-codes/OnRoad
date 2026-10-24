"""
Fallback catalogue from BikeDekho for two-wheeler models a manufacturer's own site won't serve to us (e.g. Ather's /450
page answers our declared crawler with 403; we don't disguise it to get past that).

Each BikeDekho model page carries schema.org JSON-LD: an ItemList "<Model> variants" whose items have the variant name,
an Offer with the ex-showroom price (Delhi) and additionalProperty specs (battery, range, kerb weight, top speed ...).
Prices are stored as Delhi ex-showroom with the BikeDekho variant URL as source, so the app shows the city they apply to.
robots.txt (User-agent: *) allows these pages; one request per page, 3 s apart.
"""
from __future__ import annotations

import json
import re
import time

import httpx

from ._2w_common import USER_AGENT

BASE = "https://www.bikedekho.com"
_cache: dict[str, dict | None] = {}


def model(brand: str, slug: str) -> dict | None:
    """{'name', 'url', 'image', 'variants': [{'name', 'price', 'url', 'image', 'props': {label: value unit}}]} or None."""
    url = f"{BASE}/{brand}/{slug}"
    if url in _cache:
        return _cache[url]
    time.sleep(3)
    r = httpx.get(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-IN"}, follow_redirects=True, timeout=40)
    out = None
    if r.status_code == 200:
        group, items, kind = None, None, "bike"
        for m in re.finditer(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", r.text, re.S):
            try:
                d = json.loads(m.group(1))
            except ValueError:
                continue
            if isinstance(d, dict) and d.get("@type") == "BreadcrumbList" and "Scooters" in json.dumps(d):
                kind = "scooter"
            if isinstance(d, dict) and d.get("@type") == "ProductGroup":
                group = d
            if isinstance(d, dict) and d.get("@type") == "ItemList" and re.search(r"variants?$", str(d.get("name", ""))):
                items = d.get("itemListElement") or []
        title = (re.search(r"<title>(.*?)</title>", r.text, re.S) or [None, ""])[1]
        upcoming = bool(re.search(r"expected (?:price|launch)|launch date|is an upcoming|will be launched|estimated price|concept",
                                  str((group or {}).get("description", "")), re.I) or re.search(r"expected launch", title, re.I))
        if group and items and not upcoming and not re.search(r"discontinued", str((group or {}).get("description", "")), re.I):
            vs = []
            for it in items:
                x = it.get("item") or {}
                price = (x.get("offers") or {}).get("price")
                if not x.get("name") or not price:
                    continue
                props = {p.get("name"): f"{p.get('value')} {p.get('unitText') or ''}".strip() for p in x.get("additionalProperty") or []
                         if p.get("name") and p.get("value") not in (None, "")}
                vs.append({"name": x["name"], "price": int(float(price)), "url": x.get("url") or url, "image": x.get("image"), "props": props})
            out = {"name": group.get("name"), "brand": (group.get("brand") or {}).get("name", ""), "kind": kind,
                   "url": str(r.url), "image": group.get("image"), "variants": vs}
    _cache[url] = out
    return out


def brand_slugs(brand: str) -> list[str]:
    """Model slugs on BikeDekho's brand pages (bikes and scooters)."""
    out: list[str] = []
    for kind in ("bikes", "scooters"):
        time.sleep(3)
        r = httpx.get(f"{BASE}/{brand}-{kind}", headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=40)
        if r.status_code == 200:
            out += re.findall(rf'href="{re.escape(BASE)}/{re.escape(brand)}/([a-z0-9-]+)"', r.text)
    skip = {"images", "colors", "videos", "news", "reviews", "dealers", "service-center", "compare", "upcoming", "electric"}
    return [x for x in dict.fromkeys(out) if x not in skip and "concept" not in x]
