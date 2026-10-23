"""
Volkswagen India - https://www.volkswagen.co.in (a division of Skoda Auto Volkswagen India Pvt Ltd)

Endpoints used:
  GET  /en/models.html   <script type="x-feature-hub/serialized-states"> -> "models_featureappsection" ->
                         modelOverviewResult.modelOverview.models[] (carlines -> trims -> engines[] with bodyTypes,
                         engineTypes, gearTypes and prices.price1.value). This is the server-side state of VW's own
                         model-overview feature app (its BFF URL is signed per deploy, so the page is read instead).
  POST https://www.volkswagenlabs.co.in/onehub-api/api/findbinddealers
       form {CityName:"<City>,<State>", SrcLat, SrcLong, NetworkTypeId:1 (showroom)}
       -> the API called by https://www.volkswagen.co.in/app/site/find-a-dealer/ (dealer-locator.js)
  GET  /en/purchase-and-financing/offers/current-offers.html (links one layer per model line) and each
       .../current-offers.html/__layer/layers/offers_and_products/current-offers/<model>/master.layer
       The layer's AEM richtext (JSON embedded in the HTML) is read: heading (model line), offer bullets (EMI, assured
       buyback) and the disclaimer, which states the other benefits (total benefits, scrappage, free labour,
       loyalty / exchange / corporate). The /en/models/<model>.html pages repeat the same layer text (checked
       2026-10-22: Tayron, Tiguan R-Line and Golf GTI pages carry no offer); en.sitemap.xml has no other offer page
       (service-offers.html is after-sales, not a purchase offer).

City: the model overview shows one national "From Rs X" ex-showroom per trim (no city selector), so prices() returns
city="India (national)". Each trim is one price line on the site (VW publishes no colour/variant split below trim).
Verified 2026-10-20: Taigun Comfortline 1.0 TSI MT 10,99,900 == "From Rs 10,99,900" on models.html; Hyderabad
dealer API returned VW Deccan / Mehdipatnam / SP Road / Hyderabad (Banjara Hills) etc. with phone, email, lat/lng.
Known gaps: engine cc is given as "1.0L TSI" text only (engine_cc left None rather than guessed); seats not published
in the overview; Golf GTI has no gear/engine fields.
Offers (verified 2026-10-22): Virtus layer -> EMI Rs 15,836, up to 70% assured buyback, total benefits up to
Rs 1,30,000, free labour on 1,000/7,500/15,000 km services, scrappage up to Rs 20,000 (emitted for both Virtus Sport
and Virtus Chrome, the overview's names for the Virtus line). Taigun layer -> EMI Rs 15,836 (Comfortline, Rs 10 lakh
loan for 7 years, Bajaj), up to 75% buyback, free labour, scrappage up to Rs 20,000, and exchange / loyalty / corporate
benefits named without amounts ("Corporate and loyalty benefits cannot be clubbed").
Offer gaps: VW states NO validity dates and no city split (national offers -> valid_* None, city None); EMI is a
monthly instalment, not a benefit, so its amount_inr is None (figure in title); no offers for Tayron, Tiguan R-Line,
Golf GTI; the Virtus total is not broken down into cash/exchange/etc. on the site.
"""

from __future__ import annotations

import html as _html
import json
import re
import time
import urllib.parse

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import make_client

BASE = "https://www.volkswagen.co.in"
DEALER_API = "https://www.volkswagenlabs.co.in/onehub-api/api/findbinddealers"
DELAY = 0.7
NATIONAL = "India (national)"

# city -> (state, lat, lng) used only to call the locator the way its Google-Places search box does
CITY_GEO = {"hyderabad": ("Telangana", 17.385044, 78.486671), "bengaluru": ("Karnataka", 12.971599, 77.594566),
            "mumbai": ("Maharashtra", 19.076090, 72.877426), "chennai": ("Tamil Nadu", 13.082680, 80.270721),
            "new delhi": ("Delhi", 28.613939, 77.209023), "delhi": ("Delhi", 28.613939, 77.209023),
            "pune": ("Maharashtra", 18.520430, 73.856743), "kolkata": ("West Bengal", 22.572645, 88.363892),
            "ahmedabad": ("Gujarat", 23.022505, 72.571365)}




def _text(fragment: str) -> str:
    fragment = re.sub(r"<script.*?</script>|<style.*?</style>", " ", fragment, flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " | ", fragment)))



_HERO = re.compile(r"banner|homepage-image|hero|model-db|alpha", re.I)
_FEATURE = re.compile(r"seat|sunroof|wheel|boot|light|airbag|charg|dsg|climat|massage|adas|hill|infotain|feature|iq-|illum|interior|safety|performance|section|gallery|intro|app", re.I)
_SKIP = re.compile(r"mobile|logo|brochure|technical|book|dealer|icon|-mb-|900x1600", re.I)


def _hero_image(page_url: str) -> str | None:
    key = page_url.rstrip("/").split("/")[-1].replace(".html", "").split("-")[-1].lower()   # taigun / tayron / line / sport / chrome / gti
    """Largest official hero image on the model page (assets.volkswagen.com URLs are signed per size, so we pick the widest
    one the page itself offers instead of building a URL)."""
    import base64, html as _html
    try:
        h = _html.unescape(make_client().get(page_url, timeout=30).text)
    except Exception:
        return None
    best, best_w, cut, cut_w = None, 0, None, 0
    for name, q in re.findall(r"https://assets\.volkswagen\.com/is/image/volkswagenag/([A-Za-z0-9_\-]+)\?([A-Za-z0-9=_\-]+)", h):
        if _SKIP.search(name) or _FEATURE.search(name):
            continue
        try:
            d = base64.b64decode(q + "==")
            w = int((re.search(rb"wid=(\d+)", d) or [0, b"0"])[1])
        except Exception:
            d, w = b"", 0
        u = f"https://assets.volkswagen.com/is/image/volkswagenag/{name}?{q}"
        w += 10000 if key in name.lower() else 0            # images named after this model first
        if b"alpha" in d and w > cut_w:                 # transparent side-profile cutout of a trim: best for cards
            cut, cut_w = u, w
        elif _HERO.search(name) and w > best_w:
            best, best_w = u, w
    return cut if cut_w % 10000 >= 800 else (best if best_w % 10000 >= 800 else None)

class VolkswagenAdapter(BrandAdapter):
    brand = "Volkswagen"
    slug = "volkswagen"
    website = BASE

    def __init__(self):
        self._c = None

    def _client(self):
        if self._c is None:
            self._c = self.client()
        return self._c

    def _get(self, url, **kw):
        time.sleep(DELAY)
        r = self._client().get(url, **kw)
        r.raise_for_status()
        return r

    def _overview(self) -> list[dict]:
        page = self._get(f"{BASE}/en/models.html").text
        m = re.search(r'<script type="x-feature-hub/serialized-states"[^>]*>(.*?)</script>', page, re.S)
        if not m:
            raise NotSupported("VW models.html no longer embeds the model-overview state")
        states = json.loads(urllib.parse.unquote(m.group(1)))
        for v in states.values():
            if isinstance(v, str) and "modelOverviewResult" in v:
                return json.loads(v)["modelOverviewResult"]["modelOverview"]["models"]
        raise NotSupported("VW model-overview state not found")

    @staticmethod
    def _img(node: dict) -> str | None:
        name = (node.get("data") or {}).get("name") or (node.get("data") or {}).get("carlineName") or ""
        u = ((node.get("data") or {}).get("media") or {}).get("defaultSideView", {}).get("url")
        return BASE + u if u and u.startswith("/") else u

    def models(self) -> list[dict]:
        out = []
        for m in self._overview():
            d = m["data"]
            engines = d.get("engines") or [e for c in m.get("children", []) for e in c["data"].get("engines", [])]
            body = next((b for e in engines for b in e.get("bodyTypes", [])), None)
            url = f"{BASE}/en/models{m['nodeId']}.html"
            out.append({"name": d["name"], "url": url, "body_type": body, "image_url": _hero_image(url) or self._img(m)})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = []
        for m in self._overview():
            trims = m.get("children") or [m]          # Tiguan R-Line / Golf GTI are single-trim nodes
            for t in trims:
                for e in t["data"].get("engines", []):
                    price = ((e.get("prices") or {}).get("price1") or {}).get("value")
                    if not price:
                        continue
                    gear = " ".join(e.get("gearTypes") or [])
                    name = t["data"]["name"].strip()
                    trans = "DSG" if "DSG" in name else ("Manual" if "Manual" in gear else
                                                         ("Automatic" if gear else ("Manual" if " MT" in name else "Automatic")))
                    out.append(Variant(
                        model=m["data"]["name"], variant=name, fuel="Electric" if m["data"].get("isElectric") else "Petrol",
                        transmission=trans, ex_showroom_inr=int(price), city=NATIONAL, source_url=f"{BASE}/en/models.html",
                        body_type=(e.get("bodyTypes") or [None])[0], model_url=f"{BASE}/en/models{m['nodeId']}.html",
                        image_url=self._img(t) or self._img(m)))
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        geo = CITY_GEO.get(city.lower())
        if not geo:
            raise NotSupported(f"no coordinates configured for {city!r}; add it to CITY_GEO")
        state, lat, lng = geo
        time.sleep(DELAY)
        r = self._client().post(DEALER_API, data={"CityName": f"{city},{state}", "SrcLat": str(lat), "SrcLong": str(lng),
                                                  "NetworkTypeId": "1"},
                                headers={"Origin": BASE, "Referer": f"{BASE}/app/site/find-a-dealer/"})
        d = r.json()
        if not d.get("isValid"):
            raise NotSupported(f"VW dealer API returned no data for {city}")
        out = []
        for x in d.get("Dealers") or []:
            if (x.get("DealerCity") or "").lower() != city.lower():
                continue
            out.append(Dealer(name=x["DealerName"], address=x.get("DealerAddress") or "", city=x["DealerCity"],
                              state=x.get("DealerState") or state, pincode=x.get("DealerPincode"),
                              phone=x.get("DealerContact"), email=x.get("DealerEmail"),
                              lat=float(x["Latitude"]) if x.get("Latitude") else None,
                              lng=float(x["Longitude"]) if x.get("Longitude") else None, kind="sales",
                              source_url=f"{BASE}/app/site/find-a-dealer/", website=x.get("Website")))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        """National offers from the per-model layers of /en/purchase-and-financing/offers/current-offers.html.

        Each layer's AEM richtext (embedded as JSON in the layer HTML) holds a bullet list (EMI / assured buyback) and a
        disclaimer paragraph that states the remaining benefits (total benefits, scrappage, free labour, loyalty /
        exchange / corporate). VW states no validity dates and no city split, so valid_* and city stay None."""
        page = self._get(f"{BASE}/en/purchase-and-financing/offers/current-offers.html").text
        layers = list(dict.fromkeys(re.findall(
            r'href="(/en/purchase-and-financing/offers/current-offers\.html/__layer/[^"]+?/master\.layer)"', page)))
        names = [m["data"]["name"] for m in self._overview()]
        out: list[Offer] = []
        for path in layers:
            src = BASE + path
            blocks = _richtext_blocks(self._get(src).text)
            heading = next((t.strip() for k, t in blocks if k in ("heading", "overline") and t.strip()), "")
            heading = heading or path.split("/current-offers/")[-1].split("/")[0].replace("-", " ").title()
            # the layer heading is the model line ("Virtus", "Taigun"); join to every overview model of that line
            models = [n for n in names if _norm(heading) in _norm(n)] or [heading]
            bullets, disclaimer = [], ""
            for _, text in blocks:
                if "representation purpose" in text:
                    disclaimer = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
                    continue
                for line in text.replace("\xa0", " ").split("\n"):
                    line = line.strip(" -")
                    if re.search(r"EMI of|Assured Buyback|benefit|discount|bonus", line, re.I) and len(line) < 120 \
                            and not line.lower().startswith("avail benefits"):
                        bullets.append(line)
            sentences = [s.strip(" *^") for s in re.split(r"(?<=\.)\s+(?=[*^A-Z0-9])", disclaimer) if s.strip(" *^")]
            general = [s for s in sentences if re.search(r"extended by authorised|cess extra|sole discretion|finance partner|"
                                                         r"Subject to applicable|cannot be clubbed", s, re.I)]
            loan = next((s for s in sentences if s.lower().startswith("loan amount")), None)
            variant_note = re.search(r"prices mentioned are for the (\w+) variant", disclaimer)
            items = []        # (kind, title, amount, details, conditions, variant)
            for b in bullets:
                if b.upper().startswith("EMI OF"):
                    # a monthly instalment, not a benefit -> amount_inr stays None (figure kept in title/details)
                    emi = _inr(b)
                    items.append(("finance", f"EMI of ₹{_lakh(emi)}*" if emi else b, None, b,
                                  " ".join(x for x in [loan] + general if x) or None,
                                  variant_note.group(1) if variant_note else None))
                elif "buyback" in b.lower():
                    items.append(("other", b, None, b, " ".join(general) or None, None))
                else:
                    items.append(("other", b, _inr(b), b, " ".join(general) or None, None))
            for s in sentences:
                low = s.lower()
                if low.startswith("benefits up to"):
                    amt = _inr(s)
                    items.append(("other", f"Total benefits up to ₹{_lakh(amt)}" if amt else s, amt, s, " ".join(general) or None, None))
                elif "scrappage" in low:
                    amt = _inr(s)
                    items.append(("scrappage", f"Additional scrappage benefits up to ₹{_lakh(amt)}" if amt else s, amt, s,
                                  " ".join(general) or None, None))
                elif low.startswith("labour charges free"):
                    items.append(("other", "Free labour charges on 1,000 / 7,500 / 15,000 km services", None, s,
                                  " ".join(general) or None, None))
            # benefits the disclaimer names without an amount ("details on loyalty and exchange benefits",
            # "Corporate and loyalty benefits cannot be clubbed")
            for kind in ("exchange", "loyalty", "corporate"):
                hit = [s for s in sentences if re.search(rf"\b{kind}\b", s, re.I) and "benefit" in s.lower()]
                if hit:
                    items.append((kind, f"{kind.title()} benefit (amount not stated; ask dealer)", None, " ".join(hit),
                                  " ".join(general) or None, None))
            for model in models:
                for kind, title, amt, details, cond, variant in items:
                    out.append(Offer(model=model, title=title, amount_inr=amt, details=details, valid_until=None,
                                     city=None, source_url=src, kind=kind, conditions=cond, variant=variant))
        if not out:
            raise NotSupported("VW current-offers page lists no model offer layers")
        return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _lakh(n: int) -> str:
    """1300000 -> '13,00,000' (Indian digit grouping, as VW prints amounts)."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    return ",".join(re.findall(r"\d{1,2}(?=(?:\d{2})*$)", head)) + "," + tail


def _inr(text: str) -> int | None:
    """'EMI of INR 15 836*' / 'up to ₹ 20 000' -> 15836 / 20000 (VW writes thousands with spaces)."""
    m = re.search(r"(?:INR|₹|Rs\.?)\s*(\d[\d ,]*\d|\d)", text)
    return int(re.sub(r"\D", "", m.group(1))) if m else None


def _richtext_blocks(page: str) -> list[tuple[str, str]]:
    """(component name, plain text) for every AEM richtext item of an offers layer (JSON embedded in the HTML)."""
    dec = json.JSONDecoder()

    def walk(n):
        if isinstance(n, list):
            return "".join(walk(x) for x in n)
        if n.get("kind") == "textNode":
            return n.get("value", "")
        return ("\n" if n.get("tagName") in ("p", "li", "br") else "") + walk(n.get("children", []))

    out, seen = [], set()
    for m in re.finditer(r'\{"richtext":', page):
        try:
            rt, end = dec.raw_decode(page, m.end())
        except ValueError:
            continue
        p = re.search(r'"originalCqPath":"([^"]+)"', page[end:end + 800])
        if not p or "/layers/offers_and_products/" not in p.group(1) or p.group(1) in seen:
            continue
        seen.add(p.group(1))
        out.append((p.group(1).rsplit("/", 1)[-1], walk(rt)))
    return out


ADAPTER = VolkswagenAdapter()
