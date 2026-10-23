"""
TVS Motor Company - https://www.tvsmotor.com  (robots.txt: only one image path disallowed)

Endpoints used (the XHRs of the site's own "price in <city>" pages, /assets/js/All-brand-city-price.js):
  GET /price-city-sitemap.xml                      one "<model>-city-price-sitemap.xml" per model with city pages
  GET /<model path>/price-in-<city>                the city price page; its <sitecore-vehicles> block lists every
                                                   variant's data-vehiclemodelId / data-partid
  GET /api/getModelVariantCityprice?cityName=<city>          -> state code (e.g. "420000035" for Hyderabad)
  GET /api/GetVehicleDetails?vehicle=<name>&stateCode=&modelIds=&partIds=
                                                   -> [{"VariantNameExtension": "Disc", "Price": "90650"}, ...]
                                                   the ex-showroom price per variant that the page renders
City: prices are per state code resolved from the city name (Hyderabad first).
Verified 2026-10-22 (Hyderabad): Ntorq 125 Disc Rs 90,650 and XT Rs 1,05,200 (API). The server-rendered table can be
stale (Jupiter DRUM showed Rs 74,400 in HTML while the API the page then renders gives Rs 77,450); the API is used.
Images: the price page's own bike picture (500-800 px) or the header-navigation thumbnail (372x218).
Gaps: iQube / TVS X / Orbiter electric price pages answered HTTP 503 and are not in the city-price sitemap (no prices read);
the dealer locator (/tvs-dealer-locator/...) loads no dealer data we could find as text/XHR -> NotSupported;
offers not read; engine cc / specs not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import Site, clean, inr, meta, trans_2w

BASE = "https://www.tvsmotor.com"

# sitemap key -> (page path, vehicle name the page's JS sends to the API, display name, body type)
MODELS = {
    "tvs-jupiter": ("/tvs-jupiter", "jupiter", "Jupiter", "Scooter"),
    "tvs-jupiter-125": ("/tvs-jupiter-125", "jupiter 125", "Jupiter 125", "Scooter"),
    "tvs-ntorq": ("/tvs-ntorq", "tvs ntorq 125", "Ntorq 125", "Scooter"),
    "tvs-zest": ("/tvs-zest", "tvs zest 110", "Zest 110", "Scooter"),
    "tvs-xl100": ("/tvs-xl100", "tvs xl 100", "XL100", "Commuter"),
    "tvs-sport": ("/tvs-sport", "tvs sport", "Sport", "Commuter"),
    "tvs-radeon": ("/commuter/tvs-radeon", "tvs radeon 110", "Radeon", "Commuter"),   # moved under /commuter/ (2026-10)
    # tvs-star-city-plus: discontinued; tvsmotor.com 301-redirects it to the Radeon page (checked 2026-10-23)
    "tvs-raider": ("/tvs-raider", "tvs raider", "Raider 125", "Commuter"),
    "tvs-ronin": ("/tvs-ronin", "tvs ronin", "Ronin", "Cruiser"),
    "apache-rtr-160-2v": ("/tvs-apache/apache-rtr-160-2v", "apache rtr 160 2v", "Apache RTR 160", "Street"),
    "apache-rtr-160-4v": ("/tvs-apache/apache-rtr-160-4v", "apache rtr 160 4v", "Apache RTR 160 4V", "Street"),
    "apache-rtr-180": ("/tvs-apache/apache-rtr-180", "apache rtr 180", "Apache RTR 180", "Street"),
    "apache-rtr-200-4v": ("/tvs-apache/apache-rtr-200-4v", "apache rtr 200 4V", "Apache RTR 200 4V", "Street"),
    "apache-rtr-310": ("/tvs-apache/apache-rtr-310", "APACHE RTR 310", "Apache RTR 310", "Street"),
    "apache-rr-310": ("/tvs-apache/rr-310", "apache rr 310", "Apache RR 310", "Sports"),
}


NAV_NAME = {'tvs-jupiter': 'TVS Jupiter', 'tvs-jupiter-125': 'TVS Jupiter 125', 'tvs-ntorq': 'TVS Ntorq 125', 'tvs-zest': 'TVS Zest 110', 'tvs-xl100': 'TVS XL100', 'tvs-sport': 'TVS Sport', 'tvs-radeon': 'Radeon', 'tvs-star-city-plus': '', 'tvs-raider': 'TVS Raider', 'tvs-ronin': 'TVS Ronin', 'apache-rtr-160-2v': 'Apache RTR 160', 'apache-rtr-160-4v': 'Apache RTR 160 4V', 'apache-rtr-180': 'Apache RTR 180', 'apache-rtr-200-4v': 'Apache RTR 200 4V', 'apache-rtr-310': 'Apache RTR 310', 'apache-rr-310': 'Apache RR 310'}


def _abs(u: str) -> str:
    u = re.sub(r"^/[a-z0-9\-]+/-/media/", "/-/media/", u) if u.startswith("/") else u
    return BASE + u if u.startswith("/") else u


class TVSAdapter(BrandAdapter):
    brand = "TVS Motor Company"
    slug = "tvs"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._keys = None
        self._img = {}
        self._url = {}
        self._nav = {}

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _model_keys(self) -> list[str]:
        if self._keys is None:
            sm = self.s.text("/price-city-sitemap.xml")
            keys = re.findall(r"/([a-z0-9\-]+)-city-price-sitemap\.xml", sm)
            self._keys = [k for k in keys if k in MODELS]
            if not self._keys:
                raise NotSupported("TVS price-city sitemap changed")
        return self._keys

    def models(self) -> list[dict]:
        out = []
        for k in self._model_keys():
            path, _, name, body = MODELS[k]
            out.append({"name": name, "url": self._url.get(k, BASE + path), "body_type": body, "image_url": self._img.get(k)})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        ref0 = f"{BASE}/tvs-jupiter/price-in-{city.lower().replace(' ', '-')}"
        code = self.s.json("/api/getModelVariantCityprice", params={"cityName": city.lower()},
                           headers={"Referer": ref0, "X-Requested-With": "XMLHttpRequest"})
        code = str(code).strip()
        if not code.isdigit():
            raise NotSupported(f"TVS has no price state for {city!r}")
        out = []
        for k in self._model_keys():
            path, vname, name, body = MODELS[k]
            page_url = f"{BASE}{path}/price-in-{city.lower().replace(' ', '-')}"
            r = self.s.get(page_url, ok=(200, 404))
            if r.status_code == 404:
                continue
            page = r.text
            if not self._nav:
                for h, im, alt in re.findall(r'<a href="([^"]+)" onclick="PushDatalayerHeader\([^)]*\)">\s*<img data-src="([^"]+)" alt="([^"]+)"', page):
                    self._nav.setdefault(alt.strip(), (BASE + h, _abs(im)))
            # the price page's own bike picture (about 500-800 px); otherwise the navigation thumbnail (372 px)
            pics = [p for p in re.findall(r'src="([^"]*/-/media/Feature/BrandPriceCity/[^"]+)"', page)
                    if not re.search(r"(?i)logo|brand|ban\.", p.rsplit("/", 1)[-1])]
            img = _abs(pics[0]) if pics else None
            nav_url, nav_img = self._nav.get(NAV_NAME.get(k) or "-", (None, None))
            if not img or img in self._img.values():
                img = nav_img
            if img:
                self._img[k] = img
            if nav_url:
                self._url[k] = nav_url
            ids = re.findall(r'data-partid="([^"]*)"\s+data-vehiclemodelId="([^"]*)"', page)
            params = {"vehicle": vname, "stateCode": code}
            if ids and vname.upper() != "APACHE RTR 310":
                params["modelIds"] = ",".join(f"'{m}'" for _, m in ids)
                params["partIds"] = ",".join(f"'{p}'" for p, _ in ids)
            rows = self.s.json("/api/GetVehicleDetails", params=params,
                               headers={"Referer": page_url, "X-Requested-With": "XMLHttpRequest"}) or []
            seen = set()
            for row in rows:
                ext = clean(row.get("VariantNameExtension"))
                price = inr(row.get("Price"))
                if not ext or not price or ext in seen:
                    continue
                seen.add(ext)
                out.append(Variant(model=name, variant=ext, fuel="Petrol", transmission=trans_2w(body, "Petrol"),
                                   ex_showroom_inr=price, city=city, source_url=page_url, body_type=body,
                                   model_url=self._url.get(k, BASE + path), image_url=self._img.get(k)))
        if not out:
            raise NotSupported(f"TVS publishes no prices for {city!r}")
        return out

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("TVS dealer locator (/tvs-dealer-locator/tvs-2-wheeler) exposes no dealer list as text or XHR we can read")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = TVSAdapter()
