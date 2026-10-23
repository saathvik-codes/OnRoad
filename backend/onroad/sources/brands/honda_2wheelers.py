"""
Honda Motorcycle & Scooter India - https://www.honda2wheelersindia.com  (robots.txt: Allow /)

Endpoints used (the XHRs the site's own price widget / EMI calculator / dealer locator make):
  GET /api/form/model                                   every model: model_name, category, model_code
  GET /api/form/variant_v2?model_name=<model_name>      variants of a model (variant_name, model_code)
  GET /api/form/priceMasterState?model_code=<code>      states that have a price for the model
  GET /api/form/productPrice?model_code=&state=&variant=   {"ex_show_room_price": "89396"} for that state
  GET /api/dealer-locator/r?state=<state>&city=<city>   official dealer list (dealer_type Sales / Service / ...)
  GET /sitemap.xml + each model page (/scooter/..., /motorcycle/..., /ev/...)
        og:image (Sitecore CDN edge.sitecorecloud.io, 1200x630) and the "Displacement" spec value.
The /api/form/* endpoints answer only within a browser-like session (the page's cookies + Referer of the model
page), exactly as the site's own widget calls them; no token or protection is worked around.

City: Honda prices are per state; prices(city) asks for the city's state and labels rows with the city.
Verified 2026-10-22: Activa 110 "ACTIVA DLX" Telangana Rs 89,396 (productPrice); 57 Redwing + 14 EV + 7 BigWing
sales outlets in Hyderabad in the locator.
Gaps: colour-specific prices are not published (one price per variant); models listed twice with a trailing "."
(e.g. "CB350.") have no variants and are skipped; specs other than displacement are not read; offers not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Variant
from ._2w_common import Site, inr, meta, norm, trans_2w
from ._geo import geo

BASE = "https://www.honda2wheelersindia.com"


def _body(name: str, category: str) -> str:
    n = name.upper()
    if category == "Electric Vehicle":
        return "Electric Scooter"
    if category == "Scooter" or "DIO" in n or "ACTIVA" in n:
        return "Scooter"
    if "ADV" in n:
        return "Scooter"
    if any(k in n for k in ("NX", "XL750", "TRANSALP", "XR300")):
        return "Adventure"
    if "CBR" in n:
        return "Sports"
    if any(k in n for k in ("REBEL", "GOLD WING", "CB350", "H'NESS")):
        return "Cruiser"
    if any(k in n for k in ("HORNET", "SP160", "CB500", "CB750", "CB1000")):
        return "Street"
    return "Commuter"


def _num(v) -> float | None:
    m = re.search(r"-?\d+\.\d+", v or "")
    return float(m.group(0)) if m else None


def _image(page: str, url: str) -> str | None:
    """Largest model-specific picture the model page offers (og:image 1200x630 when it is a model shot)."""
    og = meta(page, "og:image") or ""
    if "/meta/" in og:
        return og
    key = norm(url.rstrip("/").rsplit("/", 1)[-1].replace("ev-", ""))
    cands = re.findall(r'(https://edge\.sitecorecloud\.io/[^"\ ?]+\.(?:png|jpe?g|webp)|/content/dam/e2w/[^"\ ?]+\.(?:png|jpe?g|webp))', page)
    mine = [c for c in dict.fromkeys(cands) if key and key in norm(c) and not re.search(r"(?i)nav|menu|logo|icon|emi", c)]
    if not mine:
        return None
    def width(c):
        w = re.search(r"(\d{3,4})\s*(?:w)?x\d{3,4}", c)
        return int(w.group(1)) if w else 0
    best = max(mine, key=lambda c: (("/image/" in c), width(c)))
    return best if best.startswith("http") else BASE + best.replace(" ", "%20")


class HondaTwoWheelersAdapter(BrandAdapter):
    brand = "Honda 2Wheelers"
    slug = "honda_2wheelers"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._models = None

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _api(self, path, referer, **params):
        return self.s.json(path, params=params, headers={"Referer": referer, "Accept": "application/json"})

    def models(self) -> list[dict]:
        if self._models is not None:
            return self._models
        sm = self.s.text("/sitemap.xml")
        paths = re.findall(r"<loc>https://www\.honda2wheelersindia\.com(/(?:scooter|motorcycle|ev)/[^<]+)</loc>", sm)
        by_key = {}
        for p in paths:
            last = p.rsplit("/", 1)[-1]
            if last in ("price",) or "/price" in p:
                continue
            by_key.setdefault(norm(last.replace("ev-", "")), p)
        rows = self._api("/api/form/model", BASE + "/")["data"]
        out = []
        for r in rows:
            name = (r.get("model_name") or "").strip()
            if not name or name.endswith(".") or not r.get("mtoc"):
                continue
            k = norm(name)
            path = by_key.get(k) or next((p for kk, p in by_key.items() if kk.startswith(k) or k.startswith(kk) and len(kk) > 3), None)
            out.append({"name": name, "category": r.get("category"), "model_code": r.get("model_code", "").strip(),
                        "body_type": _body(name, r.get("category") or ""), "url": BASE + path if path else None,
                        "image_url": None, "engine_cc": None, "battery_kwh": None})
        for m in out:          # model pages: image + displacement
            if not m["url"]:
                continue
            try:
                page = self.s.text(m["url"])
            except Exception:
                continue
            m["image_url"] = _image(page, m["url"])
            d = re.search(r'Displacement.{0,900}?SpecificationValue\\"(?:,\\"jsonValue\\")?:\{\\"value\\":\\"([\d.]+)\s*cc', page)
            if d:
                m["engine_cc"] = int(round(float(d.group(1))))
            b = re.search(r'Battery[^"\\]{0,40}\\":\{\\"value\\":\\"([\d.]+)\s*kWh', page) \
                or re.search(r'([\d.]+)\s*kWh', page) if m["body_type"] == "Electric Scooter" else None
            if b:
                m["battery_kwh"] = float(b.group(1))
        self._models = out
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown")
        state = g[0]
        out, seen = [], set()
        for m in self.models():
            ref = m["url"] or BASE + "/"
            states = self._api("/api/form/priceMasterState", ref, model_code=m["model_code"]).get("data") or []
            if not any(s.get("state_name", "").lower() == state.lower() for s in states):
                continue
            variants = self._api("/api/form/variant_v2", ref, model_name=m["name"]).get("data") or []
            for v in variants:
                vname = (v.get("variant_name") or "").replace("\xa0", " ").strip()
                code = (v.get("model_code") or m["model_code"]).replace("\xa0", " ").strip()
                if not vname:
                    continue
                p = self._api("/api/form/productPrice", ref, model_code=code, state=state, variant=vname).get("data") or []
                price = inr(p[0].get("ex_show_room_price")) if p else None
                if not price or (m["name"], vname) in seen:
                    continue
                seen.add((m["name"], vname))
                fuel = "Electric" if m["body_type"] == "Electric Scooter" else "Petrol"
                url = f"{BASE}/api/form/productPrice?model_code={code}&state={state}&variant={vname}"
                out.append(Variant(model=m["name"], variant=vname, fuel=fuel, transmission=trans_2w(m["body_type"], fuel, vname),
                                   ex_showroom_inr=price, city=city, source_url=url, body_type=m["body_type"],
                                   engine_cc=m["engine_cc"], battery_kwh=m["battery_kwh"], model_url=m["url"],
                                   image_url=m["image_url"]))
        if not out:
            raise NotSupported(f"Honda publishes no prices for {state}")
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown")
        ref = BASE + "/dealer-locator"
        rows = self._api("/api/dealer-locator/r", ref, state=g[0], city=city).get("data") or []
        out = []
        for d in rows:
            if (d.get("dealer_type") or "").strip() != "Sales":
                continue
            net = (d.get("network_type") or "").strip()
            name = (d.get("dealer_trade_name") or d.get("dealer_firm_name") or "").strip()
            addr = (d.get("address") or "").strip()
            pin = (d.get("pin_code") or "").strip() or None
            out.append(Dealer(name=f"{name} ({net})" if net else name, address=addr, city=city, state=g[0], pincode=pin,
                              phone=(d.get("mobile") or "").strip() or None, email=(d.get("email") or "").strip() or None,
                              lat=_num(d.get("latitude")), lng=_num(d.get("longitude")),
                              kind="sales", source_url=f"{BASE}/dealer-locator"))
        return out

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = HondaTwoWheelersAdapter()
