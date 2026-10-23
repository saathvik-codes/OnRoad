"""
India Yamaha Motor - https://www.yamaha-motor-india.com  (robots.txt disallows /*?*state-list, /site-search.html)

Endpoints used:
  GET /yamaha-bikes.html                 model links (yamaha-<model>.html)
  GET /yamaha-<model>.html               og:title (model name), meta description (displacement) and the colour
                                         configurator's first transparent cut-out (.exp_360_bike_color img,
                                         /theme/v4/images/webp_images/.../color/<colour>.webp, 1200x800 RGBA)

Prices: NOT published. Model pages only state a "starting at Rs. x*" figure in the meta description; the
variant / state ex-showroom price (/products-on_road_price.html, type=getOnRoadPrice) is released only after an
OTP-verified enquiry form, which this adapter does not submit -> prices() raises NotSupported.
Dealers: the dealer-network search runs through ?state-list URLs that robots.txt disallows -> NotSupported.
Verified 2026-10-23: R15 V4 page lists 11 colour cut-outs (metallic_black.webp 1200x800); no ex-showroom table.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported
from ._2w_common import Site, cc_of, meta

BASE = "https://www.yamaha-motor-india.com"
SKIP = {"yamaha-bikes", "yamaha-scooters", "yamaha-bluesquare", "yamaha-buyersguide", "yamaha-gettingstarted",
        "yamaha-model-comparison", "yamaha-productenquiry", "yamaha-whatsnew"}


def _body(name: str) -> str:
    n = name.upper()
    if any(k in n for k in ("AEROX", "FASCINO", "RAY")):
        return "Scooter"
    if "R15" in n:
        return "Sports"
    return "Street"


class YamahaAdapter(BrandAdapter):
    brand = "Yamaha Motor India"
    slug = "yamaha"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE, headers={"Accept": "text/html"})
            self._s.c.timeout = 90
        return self._s

    def models(self) -> list[dict]:
        page = self.s.text("/yamaha-bikes.html")
        slugs = sorted(set(re.findall(r'href="(?:https://www\.yamaha-motor-india\.com)?/?(yamaha-[a-z0-9\-]+)\.html"', page)) - SKIP)
        out, seen_img = [], set()
        for sl in slugs:
            try:
                p = self.s.text(f"/{sl}.html")
            except Exception:
                continue
            title = meta(p, "og:title") or ""
            name = re.split(r"\s+Price\b", title)[0].strip() or sl.replace("yamaha-", "").upper()
            name = re.sub(r"^Yamaha\s+", "", name)
            imgs = re.findall(r'class="exp_360_bike_color[^"]*"[^>]*>\s*<img[^>]*src="([^"?]+)', p)
            img = next((BASE + i for i in imgs if BASE + i not in seen_img), None)
            if img:
                seen_img.add(img)
            out.append({"name": name, "url": f"{BASE}/{sl}.html", "body_type": _body(name), "image_url": img,
                        "engine_cc": cc_of(meta(p, "description"))})
        return out

    def prices(self, city: str = "Hyderabad"):
        raise NotSupported("Yamaha publishes only a 'starting at' figure; variant/state ex-showroom prices are shown "
                           "only after an OTP-verified enquiry form")

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("Yamaha dealer search uses ?state-list URLs, which robots.txt disallows")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = YamahaAdapter()
