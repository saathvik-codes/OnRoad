"""
Lotus adapter (lotuscars.com/en-IN, Lotus India locale; importer/dealer Exclusive Motors, New Delhi).

Endpoints used (robots.txt disallows only configurators, my-lotus and direct_url query strings - none used):
  - https://www.lotuscars.com/en-IN                 footer "MODELS" menu -> model links; og:image of each model page
  - https://m-lcmsam.lotuscars.com/api/sale/store/customer/pageQueryStore?pageNum=1&pageSize=999&countryCode=IN
        the store-locator API that /en-IN/lotus-centres/search calls (store.query in the portal bundle; host from the
        bundle's apiHost config). storeType: 1 = sales, 2 = service, 4 = other.
Verified 2026-10-19/20: India stores = "Lotus New Delhi - Showroom" (7/17 Sarvpriya Vihar, New Delhi; storeType 1,2,4)
and "Lotus New Delhi - Service Centre" (Gurugram). None in Hyderabad -> [] (no nearest-city substitution).
Models in the India site's footer MODELS menu: Emeya, Eletre, Emira, Evija (Evija is a limited-run hypercar).
Prices: the India model pages carry only a pricing disclaimer ("Lotus Cars reserves the right to revise prices ...")
and no amounts -> NotSupported("price on request"). Offers: none -> NotSupported.
Gaps: body_type not published (None).
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, city_match, clean

BASE = "https://www.lotuscars.com"
HOME = BASE + "/en-IN"
STORE_API = "https://m-lcmsam.lotuscars.com/api/sale/store/customer/pageQueryStore"


class LotusAdapter(BrandAdapter):
    brand = "Lotus"
    slug = "lotus"
    website = HOME

    def models(self) -> list[dict]:
        with Polite() as p:
            home = p.text(HOME)
            i = home.find('category-title">MODELS<')
            if i < 0:
                raise RuntimeError("Lotus home: footer MODELS menu not found")
            chunk = home[i:]
            j = chunk.find("category-title", 30)
            chunk = chunk[:j] if j > 0 else chunk[:5000]
            out = []
            for href, name in re.findall(r'<a href="(/en-IN/[a-z0-9-]+)"[^>]*>(.*?)</a>', chunk):
                url = BASE + href
                og = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', p.text(url))
                out.append({"name": clean(name), "url": url, "body_type": None, "image_url": og.group(1) if og else None})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported("price on request: Lotus India model pages publish no prices (disclaimer only)")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite(extra_headers={"Accept": "application/json"}) as p:
            data = p.json(STORE_API, params={"pageNum": "1", "pageSize": "999", "countryCode": "IN"})
        out = []
        for s in data.get("data") or []:
            if s.get("country2Code") != "IN" or s.get("storeStatus") != "ENABLE":
                continue
            addr = s.get("addressDetail") or ""
            if not city_match(city, s.get("cityName"), s.get("districtName"), *addr.split(",")):
                continue
            types = set((s.get("storeType") or "").split(","))
            kind = "sales+service" if {"1", "2"} <= types else ("sales" if "1" in types else "service")
            ex = s.get("extra") or {}
            out.append(Dealer(name=s.get("storeName"), address=addr, city=s.get("districtName") or s.get("cityName") or city,
                              state="", pincode=ex.get("storeZipCode"), phone=s.get("serviceCall") or ex.get("salesLine"),
                              email=ex.get("lotusCentreEmail") or None,
                              lat=float(s["latitude"]) if s.get("latitude") else None,
                              lng=float(s["longitude"]) if s.get("longitude") else None, kind=kind,
                              source_url=HOME + "/lotus-centres/search", website=ex.get("officialWebsiteUrl") or None))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Lotus India publishes no offers or finance schemes")


ADAPTER = LotusAdapter()
