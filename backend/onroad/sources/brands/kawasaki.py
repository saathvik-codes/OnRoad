"""
India Kawasaki Motors - https://www.kawasaki-india.com  (robots.txt: "User-agent: *" Allow; AI-training bots blocked)

Endpoints used (AEM pages, server-rendered):
  GET /                                  model links /en/motorcycles/<family>/<model>-<year>.html (+ family pages
                                         /en/motorcycles/<family>.html for models not on the home page)
  GET /en/motorcycles/<family>/<model>.html
        og:title ("VERSYS 650 | 2027"), span.productsummary__baseprice-value ("Rs 8,63,000.00", tooltip: "This is the
        ex-showroom price"), og:image (DAM rendition cq5dam.web.1280.1280), spec table tr.prodspecs__row (th/td)
City: one national ex-showroom price per model -> city="India (national)".
Verified 2026-10-23: Versys 650 (2027) Rs 8,63,000.
Gaps: one price per model (no colour/state prices); dealers (/en/tools/locate-a-dealer.html) and offers not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import NATIONAL, Site, clean, inr, meta, spec_rows, table_rows

BASE = "https://www.kawasaki-india.com"
FAMILIES = ["ninja", "z", "versys", "vulcan", "klx", "kx", "w", "eliminator"]


def _body(path: str, name: str) -> str:
    p = path.lower()
    if "/versys/" in p or "/klx/" in p or "/kx/" in p:
        return "Adventure"
    if "/vulcan/" in p or "eliminator" in p:
        return "Cruiser"
    if "/ninja/" in p:
        return "Sports"
    return "Street"


class KawasakiAdapter(BrandAdapter):
    brand = "Kawasaki Motors"
    slug = "kawasaki"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._data = None

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _load(self):
        if self._data is not None:
            return self._data
        paths = set(re.findall(r'href="(/en/motorcycles/[a-z0-9]+/[a-z0-9\-]+\.html)"', self.s.text("/")))
        for fam in FAMILIES:
            r = self.s.get(f"/en/motorcycles/{fam}.html", ok=(200, 404))
            if r.status_code == 200:
                paths |= set(re.findall(r'href="(/en/motorcycles/[a-z0-9]+/[a-z0-9\-]+\.html)"', r.text))
        out = []
        for path in sorted(paths):
            page = self.s.text(path)
            title = meta(page, "og:title") or path
            name = clean(title.split("|")[0]).title().replace("Zx", "ZX").replace("Klx", "KLX").replace("Kx", "KX").replace("Sx", "SX").replace("Rs", "RS")
            price = re.search(r'productsummary__baseprice-value"[^>]*>\s*<span>([^<]+)</span>', page)
            spec_html = page[page.find("prodspecs__row") - 200:] if "prodspecs__row" in page else ""
            rows = table_rows(spec_html[:200000])
            cc = next((re.search(r"(\d+(?:\.\d+)?)", clean(v)) for k, v in rows if "displacement" in clean(k).lower()), None)
            out.append({"name": name, "url": BASE + path, "price": inr(price.group(1)) if price else None,
                        "image": _hero_image(page), "rows": rows, "body": _body(path, name),
                        "cc": int(round(float(cc.group(1)))) if cc else None})
        self._data = out
        return out

    def models(self) -> list[dict]:
        return [{"name": m["name"], "url": m["url"], "body_type": m["body"], "image_url": m["image"]} for m in self._load()]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = [Variant(model=m["name"], variant=m["name"], fuel="Petrol", transmission="Manual", ex_showroom_inr=m["price"],
                       city=NATIONAL, source_url=m["url"], body_type=m["body"], engine_cc=m["cc"], model_url=m["url"],
                       image_url=m["image"]) for m in self._load() if m["price"]]
        if not out:
            raise NotSupported("Kawasaki model pages show no ex-showroom price")
        return out

    def specs(self):
        specs, feats = [], []
        for m in self._load():
            s, f = spec_rows(m["name"], m["name"], m["rows"], m["url"], "Petrol", "Manual")
            specs += s
            feats += f
        return specs, feats

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("Kawasaki dealer locator not read by this adapter")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = KawasakiAdapter()


def _hero_image(page: str) -> str | None:
    """og:image, unless it's Kawasaki's generic placeholder: then the first photo of the model's own product gallery."""
    og = meta(page, "og:image")
    if og and "placeholder" not in og:
        return og
    m = re.search(r"/content/dam/products/pim/gallery/[^\"' ]+?\.(?:jpg|png|webp)/_jcr_content/renditions/cq5dam\.web\.1280\.1280\.(?:png|jpeg)", page)
    return BASE + m.group(0) if m else None

