"""
BYD India - https://bydautoindia.com

The site is a React SPA (~6.5 KB shell); all content comes from the CMS API hard-wired in the bundle
(/static/js/main.*.js: {"H":"https://api.bydautoindia.com/", "s":"https://byd-assets.s3.us-east-2.amazonaws.com/production/"}).
robots.txt on bydautoindia.com is "Allow: /"; api.bydautoindia.com/robots.txt has no Disallow.

Endpoints used:
  GET  https://api.bydautoindia.com/menu          HEADER_CENTER_MENU -> "Models" children (label + page sku, e.g. bydsealion7)
  GET  https://api.bydautoindia.com/page/<sku>   model page: `body` is a JSON list of HTML blocks. The pricing block holds
                                                 one card per variant: <h2>VARIANT</h2> <strong>₹ 41 90 000*</strong>
                                                 "(Ex-showroom price)" + spec lines ("6 Seater", "71.8kWh* Battery Capacity");
                                                 the spec table header (Dimensions | Dynamic | Premium | ...) gives
                                                 "Battery capacity (kWh)" / "Seating capacity" per variant (colspans expanded).
                                                 `vehicle_schema` / `product_schema` JSON-LD give bodyType, seatingCapacity, image.
  GET  https://api.bydautoindia.com/dealers      the official dealer locator's data (/find-dealer); filtered to ACTIVE + city.

City: the price cards say only "(Ex-showroom price)" with no city or state (older, now commented-out blocks said
"Ex-showroom price All India"), so prices() returns city="India (national)".
HTML comments in the CMS blocks contain stale price cards and are stripped before parsing.

Verified 2026-10-20: 4 models / 14 variants. Sealion 7 Dynamic ₹41,90,000 and eMAX 7 Comfort 6 Seater ₹27,90,000,
Atto 3 Dynamic ₹24,99,000, Seal Dynamic ₹41,50,000 (cards on /page/<sku>). 3 Hyderabad dealers (Mody BYD Banjara Hills,
Mody BYD Begampet, KUN BYD Gachibowli).
Known gaps: JSON-LD "price" values are stale/labelled "On-Road Price" and are NOT used; dealer lat/lng are blank or "0"
in the API (-> None); the API has no sales/service flag (kind="sales"); no offers are published (offers() raises
NotSupported); engine_cc not applicable.
"""

from __future__ import annotations

import json
import re
import time

import httpx

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import clean, inr, make_client, norm
from ._geo import geo

SITE = "https://bydautoindia.com"
API = "https://api.bydautoindia.com/"
DELAY = 1.0
NATIONAL = "India (national)"
BODY = {"suv": "SUV", "sedan": "Sedan", "mpv": "MUV", "muv": "MUV", "hatchback": "Hatchback"}

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_CARD = re.compile(r"<h2[^>]*>((?:(?!<h2).)*?)</h2>\s*<p[^>]*>\s*<strong>\s*(?:₹|&#8377;|INR)\s*([\d\s,]+)\*?\s*</strong>\s*</p>(.*?)</div>",
                   re.S)


def _title(s: str) -> str:
    return re.sub(r"\b[A-Z]{2,}\b", lambda m: m.group(0).title(), s)


def _cells(tr: str) -> list[str]:
    out = []
    for attrs, body in re.findall(r"<t[dh]([^>]*)>(.*?)</t[dh]>", tr, re.S):
        span = re.search(r'colspan="?(\d+)', attrs)
        out += [clean(body)] * (int(span.group(1)) if span else 1)
    return out


class BYDAdapter(BrandAdapter):
    brand = "BYD"
    slug = "byd"
    website = SITE

    def __init__(self):
        self._c = None
        self._pages: dict[str, dict] = {}

    def _get(self, path: str):
        if self._c is None:
            self._c = make_client()
        else:
            time.sleep(DELAY)
        try:
            r = self._c.get(API + path)
        except httpx.TransportError:        # the API occasionally drops idle keep-alive sockets; retry once
            time.sleep(DELAY * 3)
            r = self._c.get(API + path)
        r.raise_for_status()
        return r.json()

    def _model_skus(self) -> list[tuple[str, str]]:
        menu = self._get("menu")["data"]
        center = next((m for m in menu if m.get("sku") == "HEADER_CENTER_MENU"), None)
        if not center:
            raise NotSupported("BYD menu API no longer has HEADER_CENTER_MENU")
        items = json.loads(center["body"])
        models = next((i for i in items if i.get("label", "").lower() == "models"), None)
        if not models:
            raise NotSupported("BYD menu API has no 'Models' entry")
        return [(c["label"], c["url"].strip("/")) for c in models.get("child", []) if c.get("url")]

    def _page(self, sku: str) -> dict:
        if sku not in self._pages:
            d = self._get(f"page/{sku}")["data"]
            schema = {}
            for key in ("vehicle_schema", "product_schema"):
                try:
                    schema[key] = json.loads(d.get(key) or "{}")
                except ValueError:
                    schema[key] = {}
            blocks = [_COMMENT.sub(" ", b.get("content") or "") for b in json.loads(d.get("body") or "[]")]
            self._pages[sku] = {"blocks": blocks, **schema}
        return self._pages[sku]

    def _model_info(self, label: str, sku: str) -> dict:
        p = self._page(sku)
        vs, ps = p["vehicle_schema"], p["product_schema"]
        name = vs.get("model") or re.sub(r"(?i)^byd\s+", "", label)
        img = ps.get("image") if isinstance(ps.get("image"), str) else None
        body = BODY.get(str(vs.get("bodyType", "")).lower())
        return {"name": name, "url": f"{SITE}/{sku}", "body_type": body,
                "image_url": img if img and "path-to-image" not in img else None,
                "seats": vs.get("seatingCapacity") if isinstance(vs.get("seatingCapacity"), int) else None}

    def models(self) -> list[dict]:
        out = []
        for label, sku in self._model_skus():
            info = self._model_info(label, sku)
            out.append({k: info[k] for k in ("name", "url", "body_type", "image_url")})
        return out

    @staticmethod
    def _spec_table(blocks: list[str]) -> dict[str, dict[str, str]]:
        """{norm(variant header): {'battery': '71.8', 'seats': '5'}} from the spec table."""
        for b in blocks:
            if "battery capacity (kwh)" not in b.lower():
                continue
            header, out = None, {}
            for tr in re.findall(r"<tr.*?</tr>", b, re.S):
                cells = _cells(tr)
                if not cells:
                    continue
                if header is None and cells[0].lower() == "dimensions":
                    header = [norm(c) for c in cells[1:]]
                    out = {h: {} for h in header}
                    continue
                if header is None:
                    continue
                label = cells[0].lower()
                key = "battery" if label.startswith("battery capacity (kwh)") else "seats" if label.startswith("seating capacity") else None
                if key:
                    for h, v in zip(header, cells[1:]):
                        out[h].setdefault(key, v)
            if header:
                return out
        return {}

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = []
        for label, sku in self._model_skus():
            info = self._model_info(label, sku)
            blocks = self._page(sku)["blocks"]
            spec = self._spec_table(blocks)
            for b in blocks:
                if "Ex-showroom price" not in b:
                    continue
                for h2, price, tail in _CARD.findall(b):
                    lines = [clean(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", tail, re.S)]
                    if not any("ex-showroom" in x.lower() for x in lines):
                        continue
                    name = _title(clean(h2))
                    key = norm(name.split("(")[0])
                    col = spec.get(key) or next((v for k, v in spec.items() if k and key.startswith(k)), {})
                    seats = next((int(m.group(1)) for x in lines if (m := re.search(r"(\d+)\s*Seater", x, re.I))), None)
                    kwh = next((float(m.group(1)) for x in lines if (m := re.search(r"([\d.]+)\s*kWh", x, re.I))), None)
                    if kwh is None and re.fullmatch(r"[\d.]+", col.get("battery", "")):
                        kwh = float(col["battery"])
                    if seats is None and re.fullmatch(r"\d+", col.get("seats", "")):
                        seats = int(col["seats"])
                    if seats is None:
                        seats = info["seats"]
                    variant = name
                    if re.search(r"Seater", " ".join(lines), re.I) and seats:
                        variant = f"{name} {seats} Seater"
                    out.append(Variant(model=info["name"], variant=variant, fuel="Electric", transmission="Automatic",
                                       ex_showroom_inr=inr(price), city=NATIONAL, source_url=f"{API}page/{sku}",
                                       body_type=info["body_type"], battery_kwh=kwh, seats=seats,
                                       model_url=info["url"], image_url=info["image_url"]))
        if not out:
            raise NotSupported("BYD model pages no longer contain '(Ex-showroom price)' variant cards")
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        data = self._get("dealers")["data"]
        out = []
        for d in data:
            if d.get("status") != "ACTIVE" or (d.get("city") or "").strip().lower() != city.lower():
                continue
            addr = clean(d.get("address"))
            pin = re.findall(r"\b(\d{6})\b", addr)

            def coord(v):
                try:
                    f = float(v)
                    return f if f else None
                except (TypeError, ValueError):
                    return None
            out.append(Dealer(name=clean(d.get("name")), address=addr, city=city,
                              state=d.get("state") or (g[0] if g else ""), pincode=pin[-1] if pin else None,
                              phone=clean(d.get("phone_no")) or None, email=clean(d.get("email")) or None,
                              lat=coord(d.get("latitude")), lng=coord(d.get("longitude")), kind="sales",
                              source_url=f"{API}dealers"))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("bydautoindia.com publishes no offers/discounts (no offers page or CMS section)")


ADAPTER = BYDAdapter()
