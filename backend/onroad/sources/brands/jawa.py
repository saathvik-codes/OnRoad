"""
Jawa Yezdi Motorcycles (Classic Legends) - https://www.jawayezdimotorcycles.com  (Shopify store; robots.txt only
blocks cart/checkout/account/collection-sort paths)

Endpoints used:
  GET /products.json?limit=250          every motorcycle (Shopify product) with its colour variants; the Shopify
                                        "price" is the Rs 999 booking amount and is NOT used as a price. Each
                                        variant's featured_image is the colour render (e.g. 3840x2160 PNG).
  GET /products/<handle>                window.variantLocationPrices["<variant id>"] =
                                        {"default": {"price", "location": "Delhi"}, "states": {"<State>": {"price"}}}
                                        - the ex-showroom price the product page shows for the visitor's state
  GET /cdn/shop/t/<theme>/assets/dealers.json   (URL taken from the product page) the dealer list behind the
                                        page's dealer dropdown: dealer code, name, city, state
City: prices are per state (Hyderabad -> Telangana) per colour variant.
Verified 2026-10-23: Yezdi Roadster "Shadow Black" Delhi Rs 2,11,969 (default), Telangana from the same object.
Gaps: BSA (Classic Legends) is not on this site; dealer rows carry no street address/phone; specs and offers not read.
"""

from __future__ import annotations

import html as _html
import json
import re

from ..base import BrandAdapter, Dealer, NotSupported, Variant
from ._2w_common import Site, clean, inr
from ._geo import geo

BASE = "https://www.jawayezdimotorcycles.com"


def _body(title: str) -> str:
    t = title.lower()
    if "adventure" in t:
        return "Adventure"
    if any(k in t for k in ("bobber", "perak", "jawa 350")):
        return "Cruiser"
    return "Street"


class JawaAdapter(BrandAdapter):
    brand = "Jawa Yezdi Motorcycles"
    slug = "jawa"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._products = None
        self._pages = {}

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _prods(self):
        if self._products is None:
            self._products = self.s.json("/products.json", params={"limit": 250}).get("products") or []
            if not self._products:
                raise NotSupported("Jawa Yezdi store lists no products")
        return self._products

    def _page(self, handle: str) -> str:
        if handle not in self._pages:
            self._pages[handle] = self.s.text(f"/products/{handle}")
        return self._pages[handle]

    @staticmethod
    def _image(p) -> str | None:
        for v in p.get("variants") or []:
            fi = v.get("featured_image") or {}
            if fi.get("src"):
                return fi["src"]
        ims = p.get("images") or []
        return max(ims, key=lambda i: i.get("width") or 0)["src"] if ims else None

    def models(self) -> list[dict]:
        return [{"name": p["title"], "url": f"{BASE}/products/{p['handle']}", "body_type": _body(p["title"]),
                 "image_url": self._image(p)} for p in self._prods()]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown")
        out = []
        for p in self._prods():
            page = self._page(p["handle"])
            data = {}
            for vid, blob in re.findall(r'window\.variantLocationPrices\["(\d+)"\]\s*=\s*(\{.*?\});', page, re.S):
                try:
                    data[vid] = json.loads(blob)
                except ValueError:
                    continue
            url = f"{BASE}/products/{p['handle']}"
            body = _body(p["title"])
            for v in p.get("variants") or []:
                d = data.get(str(v["id"]))
                st = (d or {}).get("states", {}).get(g[0]) if d else None
                price = inr((st or {}).get("price"))
                if not price:
                    continue
                out.append(Variant(model=p["title"], variant=clean(v.get("title")), fuel="Petrol", transmission="Manual",
                                   ex_showroom_inr=price, city=city, source_url=f"{url}#variantLocationPrices.{v['id']}.{g[0]}",
                                   body_type=body, model_url=url, image_url=self._image(p)))
        if not out:
            raise NotSupported(f"Jawa Yezdi publishes no price for {g[0]}")
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        page = self._page(self._prods()[0]["handle"])
        m = re.search(r"dealerUrl\s*=\s*'([^']+dealers\.json[^']*)'", page)
        if not m:
            raise NotSupported("dealer list URL not found on the product page")
        url = "https:" + m.group(1) if m.group(1).startswith("//") else m.group(1)
        g = geo(city)
        out = []
        for d in self.s.json(url):
            if (d.get("city") or "").strip().lower() != city.lower():
                continue
            out.append(Dealer(name=_html.unescape(d.get("dealer", "")).strip(), address="", city=city,
                              state=d.get("state") or (g[0] if g else ""), pincode=None, phone=None, email=None,
                              lat=None, lng=None, kind="sales", source_url=url))
        return out

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = JawaAdapter()
