"""
Harley-Davidson India - https://www.harley-davidson.com/in/en/  (robots.txt "User-Agent: *": only /store/dealershop
and /dealerservices disallowed)

Endpoints used:
  GET /in/en/motorcycles/index.html   server-rendered bike catalogue (BikeCatalogProduct objects): name, modelCode,
                                      url.urlPath, priceFormatted ("INR. 2,35,000"), colour options with the colour
                                      render on H-D's asset host (/ctfasset/.../<year>-<model>-<colour>-motorcycle.jpg)
Price: the page states "Prices shown are Ex-showroom Delhi" and gives one price per model -> city="India (national)".
Only models with a priceFormatted value are priced; the rest say "See your local dealer for pricing information."
Verified 2026-10-23: Harley-Davidson X 440 INR 2,35,000; X 440 T INR 2,86,000 (all other 14 models unpriced).
Gaps: big-twin models have no published India price; dealers (Hero MotoCorp outlets) and offers not read; specs not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import NATIONAL, Site, clean, inr

BASE = "https://www.harley-davidson.com"
INDEX = "/in/en/motorcycles/index.html"
_PROD = re.compile(r'"name":"([^"]+)","formattedName":"[^"]*","modelCode":"([^"]*)","url":\{"__typename":"Link","sys":\{[^{}]*\},"urlPath":"([^"]+)"\},'
                   r'"priceFormatted":("[^"]*"|null)')


def _body(name: str) -> str:
    n = name.lower()
    if "pan america" in n:
        return "Adventure"
    if any(k in n for k in ("x 440", "x™ 440", "nightster", "sportster")):
        return "Street"
    return "Cruiser"


class HarleyDavidsonAdapter(BrandAdapter):
    brand = "Harley-Davidson India"
    slug = "harley_davidson"
    website = BASE + "/in/en/"
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._items = None

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _load(self):
        if self._items is None:
            page = self.s.text(INDEX)
            out, seen = [], set()
            for m in _PROD.finditer(page):
                name = clean(m.group(1)).replace("™", "").replace("  ", " ")
                if name in seen:
                    continue
                seen.add(name)
                tail = page[m.end():m.end() + 6000]
                img = re.search(r'"url":"(https://www\.harley-davidson\.com/ctfasset/[^"]+-motorcycle\.(?:jpg|png|webp))"', tail)
                price = m.group(4).strip('"') if m.group(4) != "null" else ""
                out.append({"name": name, "code": m.group(2), "url": f"{BASE}/in/en{m.group(3)}", "price": inr(price) if price else None,
                            "image": img.group(1) if img else None, "body": _body(name)})
            if not out:
                raise NotSupported("H-D India bike catalogue not found on the motorcycles page")
            self._items = out
        return self._items

    def models(self) -> list[dict]:
        return [{"name": i["name"], "url": i["url"], "body_type": i["body"], "image_url": i["image"]} for i in self._load()]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = [Variant(model=i["name"], variant=i["name"], fuel="Petrol", transmission="Manual", ex_showroom_inr=i["price"],
                       city=NATIONAL, source_url=BASE + INDEX, body_type=i["body"], model_url=i["url"], image_url=i["image"])
               for i in self._load() if i["price"]]
        if not out:
            raise NotSupported("H-D India publishes no prices (see your local dealer)")
        return out

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("H-D India dealer locator not read by this adapter")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = HarleyDavidsonAdapter()
