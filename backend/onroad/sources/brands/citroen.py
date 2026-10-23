"""
Citroën India - https://www.citroen.in

Endpoints used (the same unauthenticated calls the official pages make; citroen.in's "Check Price", "Find a Dealer" and
variant-comparison widgets are iframes of embed.citroenindia.com, which reads https://api.citroenindia.com):
  GET  api.citroenindia.com/api/vehicles/models?page=1&limit=500
                                 -> models on sale: id, modelName, displayName, bodyType, modelImage, startingPrice, status
  GET  api.citroenindia.com/api/vehicles/vehicle-configs/price-list?modelId=<id>
                                 -> [{variantName, price}] - exactly the table the "Check Price" page
                                 (citroen.in/tools/check-price.html -> embed.citroenindia.com/Pricing) renders as
                                 "Prices (Ex-showroom)"
  GET  api.citroenindia.com/api/dealers/nearby?lat=&lng=&radius=&limit=   (Find a Dealer widget; typeCodes VN = sales)
  GET  www.citroen.in/models/<model>.html   spec block text ("Transmission | 6-Speed Automatic", "Electric Motor
                                 Power", "Diesel") -> fuel / automatic-only models
  GET  www.citroen.in/buy/offers.html       "Additional benefits of up to ₹x Lakh*" per model + "valid till" line
                                 (server-rendered; the embed app's API constants have no offers/schemes endpoint -
                                 checked /api/vehicles/*, /api/content/*; model pages, /corporate-enquiry.html,
                                 /gem.html, /tools/request-an-offer.html publish no amounts). Citroën gives only one
                                 total per model -> kind "other", title "Total benefits up to ...".

robots.txt: citroen.in disallows */api/* on www.citroen.in (not used); api.citroenindia.com and embed.citroenindia.com
publish no robots.txt. The embed bundle also contains an admin login / Bearer-token flow - NOT used (only the calls the
public widgets make without credentials).
City: the price list is one national ex-showroom list (no city/state selector) -> city="India (national)".
Verified 2026-10-20: C3X Live 4,99,000 == models.startingPrice 499000 (the "from" price); C3X Turbo Shine AT 9,68,000;
BasaltX Turbo AT Max 13,89,500; C5 Aircross Shine 37,32,400 - as listed on the Check Price page. 36 variants, 5 models.
Known gaps: C3X CNG (PureTech 82 MT CNG) is listed in the variant comparison but has no row in the price list, so it is
not returned; ë-C3X models.startingPrice (11,99,000) is below its cheapest listed variant (12,09,000) - the variant list
is used; engine cc / battery kWh are not published as numbers (only "1.2L" / "2.0L"); dealer lat/lng and phones come
from the locator; offers are model-level "up to" totals only (no cash/exchange/corporate split, no variant, no
start date published; verified 2026-10-22: C3X up to ₹1.18 lakh, BasaltX/AircrossX ₹1.55 lakh, ë-C3X ₹1.25 lakh,
"valid till 31st October 2026"; C5 Aircross has no offer card).
"""

from __future__ import annotations

import datetime as dt
import html
import re
import unicodedata

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import Polite, make_client
from . import _offers as _o
from ._geo import geo

BASE = "https://www.citroen.in"
API = "https://api.citroenindia.com"
EMBED = "https://embed.citroenindia.com"
NATIONAL = "India (national)"
HDRS = {"Origin": EMBED, "Referer": EMBED + "/", "Accept": "application/json"}
# vehicleCode -> citroen.in model page (URLs only; every number comes from the API)
PAGES = {"C3": "c3", "BST": "basalt", "C3A": "aircross", "EC3": "new-e-c3", "C5A": "c5-aircross"}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def _text(page: str) -> str:
    """Visible text with ' | ' between elements (spec tables become 'Transmission | 6-Speed Automatic | ...')."""
    page = re.sub(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<noscript\b.*?</noscript>", " ", page, flags=re.S | re.I)
    s = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " | ", page)))
    return re.sub(r"(\|\s*)+", "| ", s)


def _ascii(s: str) -> str:
    """'Citroën ë-C3X' -> 'e-C3X' (keeps the slug distinct from 'C3X')."""
    s = re.sub(r"^Citro[eë]n\s+", "", (s or "").strip())
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


class CitroenAdapter(BrandAdapter):
    brand = "Citroën"
    slug = "citroen"
    website = BASE

    def __init__(self):
        self._h = None

    def _http(self) -> Polite:
        if self._h is None:
            self._h = Polite(make_client(), delay=1.0)
        return self._h

    def _api(self, path, **params):
        return self._http().get(API + path, params=params, headers=HDRS).json()

    def models(self) -> list[dict]:
        out = []
        for m in self._api("/api/vehicles/models", page=1, limit=500).get("data") or []:
            if not m.get("status"):
                continue
            page = PAGES.get(m.get("vehicleCode") or "") or PAGES.get((m.get("vehicleCode") or "").upper()[:3])
            if not page:      # vehicleCode for C5 Aircross etc. - fall back on the model name
                page = {"c5aircross": "c5-aircross", "c3aircross": "aircross", "basalt": "basalt", "ec3": "new-e-c3",
                        "c3": "c3"}.get(re.sub(r"[^a-z0-9]", "", (m.get("modelName") or "").lower()))
            out.append({"name": _ascii(m.get("displayName") or m.get("modelName")), "id": m["id"],
                        "url": f"{BASE}/models/{page}.html" if page else None, "body_type": m.get("bodyType"),
                        "image_url": m.get("modelImage"), "min_price": int(m["startingPrice"]) if m.get("startingPrice") else None})
        if not out:
            raise NotSupported("api.citroenindia.com returned no active models")
        return out

    def _page_facts(self, url: str | None) -> tuple[str, bool]:
        """(fuel, automatic_only) from the model page's spec block."""
        if not url:
            return "", False
        t = _text(self._http().get(url).text)
        trans = re.findall(r"Transmission \| ([^|]+?) \|", t)
        auto_only = bool(trans) and all("automatic" in x.lower() for x in trans)
        if "Electric Motor Power" in t:
            fuel = "Electric"
        elif re.search(r"\bDiesel\b", t):
            fuel = "Diesel"
        elif "PureTech" in t:
            fuel = "Petrol"
        else:
            fuel = ""
        return fuel, auto_only

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = []
        for m in self.models():
            rows = self._api("/api/vehicles/vehicle-configs/price-list", modelId=m["id"]).get("data") or []
            if not rows:
                continue
            fuel, auto_only = self._page_facts(m["url"])
            for r in rows:
                name, price = (r.get("variantName") or "").strip(), r.get("price")
                if not name or not price:
                    continue
                seats = re.search(r"\b([57])\s*s\b", name, re.I)
                trans = "Automatic" if auto_only or re.search(r"\bAT\b", name) else "Manual"
                out.append(Variant(model=m["name"], variant=name, fuel=fuel, transmission=trans,
                                   ex_showroom_inr=int(price), city=NATIONAL, source_url=f"{BASE}/tools/check-price.html",
                                   body_type=m.get("body_type"), seats=int(seats.group(1)) if seats else None,
                                   model_url=m["url"], image_url=m.get("image_url")))
        if not out:
            raise NotSupported("Citroën price list returned no variants")
        return out

    def specs(self):
        """The variant-comparison page (embed.citroenindia.com/variant-comparison/<model>, a citroen.in iframe) reads
        GET api.citroenindia.com/api/vehicles/variant-comparisons?modelName=<API modelName>&limit=2000 -> one row per
        (grade, category, item) with value "Yes" / "-" / text. Grades are named without engine or gearbox ("SHINE",
        "FEEL(O)"), so a priced name gets a grade's rows only when it is that grade plus Turbo / NA / AT / MT / seat
        words. Only equipment is published there (no technical data)."""
        from ._spec_kit import SpecSink
        priced = self.prices("Hyderabad")
        api_names = {m["id"]: m.get("modelName") for m in self._api("/api/vehicles/models", page=1, limit=500).get("data") or []}
        feats = []
        for m in self.models():
            mn = api_names.get(m["id"])
            if not mn:
                continue
            src = f"{EMBED}/variant-comparison/{mn}"
            rows = self._api("/api/vehicles/variant-comparisons", modelName=mn, limit=2000).get("data") or []
            by_grade: dict[str, list[dict]] = {}
            for r in rows:
                if r.get("status") is not False:
                    by_grade.setdefault(_citroen_grade(r.get("variantName") or ""), []).append(r)
            for v in (x for x in priced if x.model == m["name"]):
                grade = _citroen_grade(re.sub(r"\b(TURBO|NA|AT|MT)\b|-\s*[57]S\b", " ", v.variant.upper()))
                if grade not in by_grade:
                    continue
                sink = SpecSink(v.model, v.variant, v.fuel, v.transmission)
                for r in by_grade[grade]:
                    val = (r.get("value") or "").strip()
                    if r.get("category", "").upper() == "VARIANTS" or "optional" in (r.get("category") or "").lower():
                        continue
                    if re.match(r"(optional|with |only )", val, re.I):
                        continue
                    sink.feature(r.get("subCategory") or "", "✓" if val.lower() == "yes" else val, src)
                feats += sink.out()[1]
        if not feats:
            raise NotSupported("api.citroenindia.com variant-comparisons returned no rows for the priced grades")
        return [], feats

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        if not g:
            raise NotSupported(f"no coordinates configured for {city!r} (add to _geo.CITY_GEO)")
        state, lat, lng = g
        data = self._api("/api/dealers/nearby", lat=lat, lng=lng, radius=40, limit=200).get("data") or []
        out = []
        for x in data:
            codes = x.get("typeCodes") or []
            if "VN" not in codes or x.get("isActive") is False:
                continue
            addr = ", ".join(p for p in (x.get("line1"), x.get("line2"), x.get("line3")) if p)
            out.append(Dealer(name=x.get("name") or "", address=addr, city=x.get("city") or city,
                              state=x.get("state") or state, pincode=x.get("zipCode"),
                              phone=x.get("phoneVN") or x.get("phoneNumber"), email=x.get("emailSales") or x.get("email"),
                              lat=x.get("latitude"), lng=x.get("longitude"),
                              kind="sales+service" if "APV" in codes else "sales",
                              source_url=f"{BASE}/tools/find-a-dealer.html", website=x.get("publicUrl")))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        url = f"{BASE}/buy/offers.html"
        t = _text(self._http().get(url).text)
        valid = None
        vm = re.search(r"valid till (\d{1,2})\s*(?:\|\s*)?(?:st|nd|rd|th)?\s*(?:\|\s*)?([A-Za-z]+),?\s+(\d{4})", t)
        if vm and vm.group(2).lower() in MONTHS:
            valid = dt.date(int(vm.group(3)), MONTHS[vm.group(2).lower()], int(vm.group(1))).isoformat()
        cm = re.search(r"\*(Offer valid on limited stock.*?Benefits may vary basis model & variants\.)", t)
        cond = re.sub(r"\s*\|\s*", " ", re.sub(r"(\d)\s*\|\s*(st|nd|rd|th)", r"\1\2", cm.group(1))) if cm else None
        out = []
        for m in re.finditer(r"Citro[eë]n ([^|]{2,30}?) \| (Additional benefits of up to ₹\s*([\d.,]+)\s*(Lakh)?\*?)", t):
            n = float(m.group(3).replace(",", ""))
            amt = int(round(n * 100000)) if m.group(4) else int(n)
            out.append(Offer(model=_ascii(m.group(1)), title=f"Total benefits up to {_o.inr(amt)}", amount_inr=amt,
                             details=m.group(2) + (" " + cond if cond else ""), valid_until=valid, city=None,
                             source_url=url, kind="other", conditions=cond))
        if not out:
            raise NotSupported("citroen.in/buy/offers.html shows no 'Additional benefits of up to' cards")
        return out



def _citroen_grade(name: str) -> str:
    """'Live (O)' / 'LIVE(O)' -> 'LIVE(O)'."""
    return re.sub(r"\s+", " ", re.sub(r"\s*\(\s*", "(", name.upper())).strip(" -")

ADAPTER = CitroenAdapter()
