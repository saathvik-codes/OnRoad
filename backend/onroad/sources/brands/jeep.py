"""
Jeep India - https://www.jeep-india.com

Endpoints used (all on www.jeep-india.com; robots.txt is "Allow: /"):
  GET  /shopping_tools/jeep-prices.html   MainNavigation data-props (JSON) -> vehicles.navCard[]: model name, model page,
                                          nav image, "Ex-Showroom Price Starting at"
  GET  /<model page>.html                 ModelWalk data-props (JSON) -> the trim walk on each model page: tab labels
                                          (trim names), per-trim pricing.price ("21.30 Lakh*", "Ex-Showroom Price") and
                                          emiData.EMIFormulaValues.msrp, feature bullets, trim images; page text gives the
                                          engine ("2.0L Multijet II Diesel Engine")
  GET  /content/dam/cross-regional/apac/jeep/en_in/ebook/jeep-dealers.js
                                          JSON behind /find-dealer.html (FADApp dataSource): sales[] / services[] with
                                          name, address, city, pincode, phone, lat/lng, email, website
  GET  /jeep-india-offers.html            ImageDescription data-props: monthly consumer / corporate / special offers

Not used: the Build & Price API (/apacconfig/v1/pricing/...) answers HTTP 500 "UNDERGOING MAINTENANCE" (Akamai page).
City: Jeep publishes one national ex-showroom price per trim (no city selector) -> city="India (national)".
Prices: the trim walk's displayed lakh figure is authoritative; the exact msrp is used only when it agrees with it
(Meridian Trail Edition msrp is mistyped as 303900 for "30.39 Lakh*").
Verified 2026-10-20: Compass Sport 17,99,000 == "Ex-Showroom Price Starting at 17.99 Lakh*" on jeep-prices.html;
Meridian Longitude 23,33,000 == 23.33 Lakh*; Wrangler Unlimited 67,70,000 == 67.70 Lakh*; Grand Cherokee Limited (O)
63,00,000 == 63.00 Lakh*. 19 trims, 4 models.
Known gaps: prices are per trim, not per powertrain (Compass/Meridian MT vs AT/4x4 split is not published on the site);
transmission is set only when the trim's own bullets say "Automatic" gearbox, fuel only when the model page states the
engine (Compass/Meridian diesel) - Wrangler / Grand Cherokee pages publish neither, so those fields are ""; engine cc
not published as a number; Hyderabad showrooms are filed under city "Gachibowli" in the locator, so dealers are
matched by distance (<= 40 km) from the city centre; offers are "up to" amounts at model level.
"""

from __future__ import annotations

import html
import json
import math
import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import Polite, make_client
from ._geo import geo

BASE = "https://www.jeep-india.com"
NATIONAL = "India (national)"
DEALERS_JS = "/content/dam/cross-regional/apac/jeep/en_in/ebook/jeep-dealers.js"
RADIUS_KM = 40
MODELS = ("Compass", "Meridian", "Wrangler", "Grand Cherokee")


def _props(page: str, component: str) -> list[dict]:
    out = []
    for m in re.finditer(rf'data-component="{component}"[^>]*?data-props="([^"]*)"', page):
        try:
            out.append(json.loads(html.unescape(m.group(1))))
        except ValueError:
            pass
    return out


def _plain(s: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _lakh(s: str | None) -> int | None:
    m = re.search(r"([\d.]+)\s*Lakh", s or "", re.I)
    return int(round(float(m.group(1)) * 100000)) if m else None


def _trim(s: str) -> str:
    """'85th ANNIVERSARY EDITION' / '85TH ANNIVERSARY EDITION' -> '85th Anniversary Edition'; 'Limited (O)' unchanged."""
    s = re.sub(r"[A-Z]{3,}", lambda m: m.group(0).capitalize(), s.strip())
    return re.sub(r"(?<=\d)(ST|ND|RD|TH)\b", lambda m: m.group(0).lower(), s)


def _img(media) -> str | None:
    try:
        src = (media.get("lg") or media.get("md") or media.get("xs"))[0].split(" ")[0]
    except (AttributeError, IndexError, TypeError):
        return None
    return src if src.startswith("http") else BASE + src


def _model_name(title: str) -> str:
    t = _plain(title).replace("®", "").replace("JEEP", "").strip()
    for n in MODELS:
        if n.lower() in t.lower():
            return n
    return t.title()


def _coord(v) -> float | None:
    m = re.search(r"-?\d+\.\d+", str(v or ""))
    return float(m.group(0)) if m else None


def _km(a, b, c, d) -> float:
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


class JeepAdapter(BrandAdapter):
    brand = "Jeep"
    slug = "jeep"
    website = BASE

    def __init__(self):
        self._h = None

    def _get(self, path: str):
        if self._h is None:
            self._h = Polite(make_client(), delay=1.0)
        return self._h.get(path if path.startswith("http") else BASE + path)

    def models(self) -> list[dict]:
        page = self._get("/shopping_tools/jeep-prices.html").text
        out, seen = [], set()
        for nav in _props(page, "MainNavigation"):
            nav = nav.get("header") or nav
            for c in ((nav.get("vehicles") or {}).get("navCard") or []):
                url = c.get("destination") or ""
                if not url.endswith(".html") or url in seen:
                    continue
                seen.add(url)
                out.append({"name": _model_name(c.get("title")), "url": BASE + url, "body_type": "SUV",
                            "image_url": _img(((c.get("media") or {}).get("mediaAsset") or {}).get("image") or {}),
                            "min_price": _lakh((c.get("price") or {}).get("price"))})
        if not out:
            raise NotSupported("jeep-india.com navigation no longer lists vehicles in MainNavigation props")
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = []
        for m in self.models():
            page = self._get(m["url"]).text
            text = _plain(page)
            fuel = "Diesel" if re.search(r"Multijet[^.<]{0,20}Diesel Engine", text) else ""
            for walk in _props(page, "ModelWalk"):
                tabs = (walk.get("tabGroup") or {})
                labels, images = tabs.get("label") or [], tabs.get("image") or []
                for i, h in enumerate(walk.get("vehicleHighlights") or []):
                    trim = _plain(labels[i]["label"]) if i < len(labels) else _plain(h.get("vehicleName")).split("change")[-1]
                    bullets = " | ".join(_plain(b.get("text")) for b in ((h.get("feature") or {}).get("bullets") or []))
                    trans = "Automatic" if re.search(r"Speed Automatic|Automatic (Gearbox|Transmission)", bullets, re.I) else ""
                    seats = re.search(r"(\d)-Seater (?:Trim|Cabin)", bullets, re.I)
                    for mo in (h.get("models") or {}).values():
                        if not mo.get("displayPricing", True):
                            continue
                        shown = _lakh((mo.get("pricing") or {}).get("price"))
                        msrp = ((mo.get("emiData") or {}).get("EMIFormulaValues") or {}).get("msrp")
                        price = int(msrp) if shown and str(msrp or "").isdigit() and abs(int(msrp) - shown) < 1000 else shown
                        if not price:
                            continue
                        out.append(Variant(model=m["name"], variant=_trim(trim), fuel=fuel,
                                           transmission=trans, ex_showroom_inr=price, city=NATIONAL, source_url=m["url"],
                                           body_type="SUV", seats=int(seats.group(1)) if seats else None,
                                           model_url=m["url"],
                                           image_url=_img(images[i]) if i < len(images) else m.get("image_url")))
                        break       # one price per trim (the walk repeats the same model code across options)
        if not out:
            raise NotSupported("no ModelWalk trim prices found on jeep-india.com model pages")
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        data = self._get(DEALERS_JS).json()
        services = data.get("services") or []
        out = []
        for x in data.get("sales") or []:
            if x.get("inactiveDealer"):
                continue
            lat, lng = _coord(x.get("dealerShowroomLatitude")), _coord(x.get("dealerShowroomLongitude"))
            named = city.lower() in ((x.get("dealerCity") or "") + " " + (x.get("dealerAddress1") or "")).lower()
            near = bool(g and lat and lng and _km(g[1], g[2], lat, lng) <= RADIUS_KM)
            if not (named or near):
                continue
            pin = (x.get("dealerZipCode") or "").strip() or None
            svc = any((s.get("dealerZipCode") or "").strip() == pin and s.get("dealerName", "").split(" - ")[0] ==
                      x.get("dealerName", "").split(" - ")[0] for s in services)
            web = (x.get("website") or "").strip() or None
            out.append(Dealer(name=x.get("dealerName") or "", address=_plain(x.get("dealerAddress1")).rstrip(" &"),
                              city=city, state=x.get("dealerState") or (g[0] if g else ""), pincode=pin,
                              phone=(x.get("phoneNumber") or "").strip() or None, email=(x.get("demail") or "").strip() or None,
                              lat=lat, lng=lng, kind="sales+service" if svc else "sales",
                              source_url=f"{BASE}/find-dealer.html",
                              website=web if not web or web.startswith("http") else "https://" + web))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        url = f"{BASE}/jeep-india-offers.html"
        out = []
        for p in _props(self._get(url).text, "ImageDescription"):
            p = p.get("descriptionBlock") or p
            title = _plain(p.get("title"))
            body = " ".join(_plain((c.get("content") or {}).get("paragraphCopy")) for c in p.get("contentModules") or [])
            if not title or "₹" not in body:
                continue
            hits = list(re.finditer(r"(?:up to\s*)?₹\s*([\d.,]+)\s*(Lakh)?\*?(?:(?!₹).){0,40}?\bon (?:the )?(?:Jeep\s*®?\s*)?"
                                    r"(Compass|Meridian|Wrangler|Grand Cherokee)", body, re.I))
            if not hits:     # "OFFERS ON THE JEEP GRAND CHEROKEE ... benefits up to ₹4,00,000*"
                n = re.search(r"₹\s*([\d.,]+)\s*(Lakh)?", body, re.I)
                model = next((x for x in MODELS if x.lower() in title.lower()), None)
                hits = [(n, model)] if n and model else []
            else:
                hits = [(h, _model_name(h.group(3))) for h in hits]
            for n, model in hits:
                v = float(n.group(1).replace(",", ""))
                amt = int(round(v * 100000)) if n.group(2) else int(v)
                out.append(Offer(model=model, title=title.title(), amount_inr=amt, details=body[:400],
                                 valid_until=None, city=None, source_url=url))
        return out


ADAPTER = JeepAdapter()
