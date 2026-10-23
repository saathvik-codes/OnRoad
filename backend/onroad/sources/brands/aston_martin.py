"""
Aston Martin adapter (astonmartin.com, global 'en' locale - there is no India locale).

Endpoints used (robots.txt: Allow /, Disallow /*/data/* - not used):
  - https://www.astonmartin.com/en/models                         model cards; the core range is every card whose
        name link is followed by an "Explore" link (Vantage, DB12, Vanquish, DBX families); special/limited cars below.
  - https://www.astonmartin.com/api/v1/dealers/bycountry?cultureName=en   JSON the dealer page (/en/dealers) calls
        (seen in /theme/.../mjs/app.bundle.js): [{IsoCountryCode, Dealerships:[{Name, Address, PhoneNumber,...}]}]
Verified 2026-10-19/20: India = one dealer, "Aston Martin New Delhi" (A16, Mohan Co-operative Industrial Estate,
Mathura Road, New Delhi 110044). None in Hyderabad -> [] (no nearest-city substitution).
Prices: none published -> NotSupported("price on request"). Offers: none -> NotSupported.
Gaps: no geo-coordinates in the by-country list; body_type is our reading of the name (Volante/Roadster =
Convertible, DBX = SUV, else Coupe); the model range is global.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, city_match, clean

BASE = "https://www.astonmartin.com"
MODELS_URL = BASE + "/en/models"
DEALERS_API = BASE + "/api/v1/dealers/bycountry?cultureName=en"


def _body(name: str) -> str:
    n = name.lower()
    if "volante" in n or "roadster" in n:
        return "Convertible"
    if "dbx" in n:
        return "SUV"
    return "Coupe"


class AstonMartinAdapter(BrandAdapter):
    brand = "Aston Martin"
    slug = "aston_martin"
    website = BASE + "/en"

    def models(self) -> list[dict]:
        with Polite() as p:
            page = p.text(MODELS_URL)
        links = [(m.group(1), clean(m.group(2)), m.start())
                 for m in re.finditer(r'<a[^>]+href="(/en/models/[^"#?]+)"[^>]*>(.*?)</a>', page, re.S)]
        out, seen = [], set()
        for i, (href, text, pos) in enumerate(links):
            if not text or text.lower() == "explore" or href in seen or href.endswith("past-models"):
                continue
            nxt = links[i + 1] if i + 1 < len(links) else None
            if not (nxt and nxt[0] == href and nxt[1].lower() == "explore"):
                continue                                # special series / hypercars without an Explore card
            seen.add(href)
            chunk = page[max(0, pos - 3000):pos]
            imgs = re.findall(r'(?:src|data-src)="(https://www\.astonmartin\.com/-/media/[^"]+)"', chunk)
            out.append({"name": text, "url": BASE + href, "body_type": _body(text),
                        "image_url": imgs[-1].replace("&amp;", "&") if imgs else None})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported("price on request: Aston Martin publishes no prices for India")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite(extra_headers={"Accept": "application/json"}) as p:
            data = p.json(DEALERS_API)
        out = []
        for c in data:
            if c.get("IsoCountryCode") != "IN":
                continue
            for d in c.get("Dealerships") or []:
                addr = d.get("Address") or ""
                if not city_match(city, d.get("Name", "").replace("Aston Martin", ""), *addr.split(",")):
                    continue
                pin = re.search(r"\b(\d{6})\b", addr)
                out.append(Dealer(name=d.get("Name"), address=addr, city=city, state="", pincode=pin.group(1) if pin else None,
                                  phone=(d.get("PhoneNumber") or "").strip() or None, email=None, lat=None, lng=None,
                                  kind="sales+service" if (d.get("DealerType") or {}).get("Name") == "Dealership" else "service",
                                  source_url=BASE + "/en/dealers", website=BASE + d["DealerPageUrl"] if d.get("DealerPageUrl") else None))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Aston Martin publishes no offers or finance schemes for India")


ADAPTER = AstonMartinAdapter()
