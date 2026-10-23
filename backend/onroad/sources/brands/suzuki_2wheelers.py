"""
Suzuki Motorcycle India - https://www.suzukimotorcycle.co.in  (robots.txt: "Disallow:" - everything allowed)

Endpoints used (the product page's own "Price" tab, a Laravel form that sends the page's csrf-token):
  GET  /                                     model links (/product-details/<slug>)
  GET  /product-details/<slug>               csrf-token meta, hidden product_id (base64) + numeric id in its JS,
                                             state <select id="price_state_district"> (Telangana = 28),
                                             colour cut-outs on Suzuki's S3 bucket (uploads/color-images/original/)
  POST /get-touch-point-district             dealer_state=<id>&dealer_touch_points=1&product_id=<numeric>
                                             -> districts (Hyderabad = 229)
  POST /get-product-price                    district_id=&state_id=&product_id=<base64>
                                             -> [{"variant_name": "Avenis", "amount": "94 543"}, ...] ex-showroom
City: prices are per district (Hyderabad district).
Verified 2026-10-23 (Hyderabad): Avenis Rs 94,543, Avenis Special Edition Rs 94,877.
Gaps: the largest model pictures Suzuki publishes are 650x428 colour cut-outs; the dealer finder form is posted
by a script whose target is not exposed (plain POST answers 405) -> dealers NotSupported; offers/specs not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import Site, cc_of, clean, inr, meta, trans_2w
from ._geo import geo

BASE = "https://www.suzukimotorcycle.co.in"


def _body(slug: str) -> str:
    s = slug.lower()
    if s.startswith("e-"):
        return "Electric Scooter"
    if any(k in s for k in ("access", "burgman", "avenis")):
        return "Scooter"
    if "v-strom" in s:
        return "Adventure"
    if any(k in s for k in ("sf", "gsx", "hayabusa")):
        return "Sports"
    return "Street"


class SuzukiTwoWheelersAdapter(BrandAdapter):
    brand = "Suzuki Two Wheelers"
    slug = "suzuki_2wheelers"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._pages = {}

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _slugs(self) -> list[str]:
        home = self.s.text("/")
        return list(dict.fromkeys(re.findall(r'href="(?:https://www\.suzukimotorcycle\.co\.in)?/product-details/([a-z0-9\-]+)"', home)))

    def _page(self, slug: str) -> dict:
        if slug not in self._pages:
            p = self.s.text(f"/product-details/{slug}")
            title = meta(p, "og:title") or clean((re.search(r"<title>(.*?)</title>", p, re.S) or [None, slug])[1])
            name = re.split(r"\s+[|\-–]\s+|\s+Price\b", title)[0].replace("Suzuki ", "").strip() or slug
            cols = re.findall(r"(https://s3\.ap-south-1\.amazonaws\.com/suzuki-website-s3/public-live/uploads/color-images/original/[^\"' ]+\.(?:png|webp|jpe?g))", p)
            spin = re.search(r'"(https://s3\.ap-south-1\.amazonaws\.com/suzuki-website-s3/public-live/uploads/product-360-images/original/\d+/)"', p)
            self._pages[slug] = {
                "name": name, "url": f"{BASE}/product-details/{slug}",
                "token": (re.search(r'name="csrf-token" content="([^"]+)"', p) or [None, None])[1],
                "pid": (re.search(r'id="product_id"[^>]*value="([^"]+)"', p) or [None, None])[1],
                "raw": (re.search(r"var product_id = '(\d+)'", p) or [None, None])[1],
                "states": {clean(n).lower(): v for v, n in re.findall(r'<option value="(\d+)">([^<]+)</option>',
                           p[p.find('id="price_state_district"'):][:4000])},
                "image": cols[0] if cols else (spin.group(1) + "1.png" if spin else None),
                "cc": cc_of(meta(p, "description")),
            }
        return self._pages[slug]

    def models(self) -> list[dict]:
        out = []
        for sl in self._slugs():
            d = self._page(sl)
            out.append({"name": d["name"], "url": d["url"], "body_type": _body(sl), "image_url": d["image"]})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown")
        out = []
        for sl in self._slugs():
            d = self._page(sl)
            state_id = d["states"].get(g[0].lower())
            if not (d["token"] and d["pid"] and d["raw"] and state_id):
                continue
            h = {"X-CSRF-TOKEN": d["token"], "X-Requested-With": "XMLHttpRequest", "Referer": d["url"]}
            dist = self.s.post("/get-touch-point-district", headers=h,
                               data={"dealer_state": state_id, "dealer_touch_points": "1", "product_id": d["raw"]}).json()
            did = next((x["district_id"] for x in dist.get("data") or [] if x["district_name"].strip().lower() == city.lower()), None)
            if not did:
                continue
            res = self.s.post("/get-product-price", headers=h,
                              data={"district_id": did, "state_id": state_id, "product_id": d["pid"]}).json()
            body = _body(sl)
            fuel = "Electric" if body == "Electric Scooter" else "Petrol"
            for row in res.get("data") or []:
                price = inr(row.get("amount"))
                if not price:
                    continue
                out.append(Variant(model=d["name"], variant=clean(row.get("variant_name")), fuel=fuel,
                                   transmission=trans_2w(body, fuel), ex_showroom_inr=price, city=city,
                                   source_url=f"{BASE}/get-product-price#product={d['raw']}&state={state_id}&district={did}",
                                   body_type=body, engine_cc=d["cc"], model_url=d["url"], image_url=d["image"]))
        if not out:
            raise NotSupported(f"Suzuki publishes no prices for {city!r}")
        return out

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("Suzuki find-dealer form is posted by a script whose endpoint is not exposed (plain POST -> 405)")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = SuzukiTwoWheelersAdapter()
