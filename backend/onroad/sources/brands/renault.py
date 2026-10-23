"""
Renault India - https://www.renault.co.in

Endpoints used (all on renault.co.in; robots.txt only blocks ?conf= / ?dealerId= / ?modelURI= / ?vin= query URLs):
  GET  /                         window.APP_STATE (JSON) -> vehicles mega-menu: modelAdminId, model name,
                                 modelHomepageURL, packshot image, minPrice
  GET  /cars/<model>.html        window.APP_STATE.page.data.modelParams.data.grades[].versions[] -> every version
                                 (label, engineName, gearboxTypeCode, energyCategory, startingPrice) - the same data the
                                 site's "versions & prices" / configurator renders
  POST /wired/commerce/v2/dealers/locator {brand:"renault", location:{lat,lon,country:"IN"}, count:25, language:"en"}
                                 -> the API behind /find-a-dealer.html (name, address, phone, lat/lon, domains)
  GET  /car-offers.html -> /car-offers/<model>-offers.html  (server-rendered; no offers JSON/XHR exists)
                                 Headline bullets (between "range starts at" and "request this offer") are joined to the
                                 "terms & conditions" paragraph: cash/exchange split per variant group ("INR 1,00,000 on
                                 Iconic & Techno+ & INR 50,000 for Evolution & Adventure", Duster-to-Duster exchange),
                                 loyalty/corporate/rural amounts from T&C, RELIVE scrappage, referral, finance (4.99% ROI
                                 alternative to cash). "Benefits upto X include cash upto A and exchange upto B" is split
                                 into components; a bare total only becomes kind "other". valid_from/until from
                                 "Benefits applicable for bookings between 1st Oct'26- 31st Oct'26".
                                 Region rule "(All India except Kerala, ..., Telangana, ...)" is honoured via _geo state,
                                 and blocks whose booking window has ended are dropped.
Offers verified 2026-10-22 against the live pages: Kiger cash INR 25,000 for Evolution+, Techno & Emotion; Duster
exchange INR 100,000 on Iconic & Techno+; all Oct 1-31 2026. Kwid's only block excludes Telangana (and is still dated
1-30 Sep 2026), so Hyderabad gets no Kwid offer. Gaps: referral benefit has no published amount; loyalty "+ AMC" value
unstated; regional exclusion needs the city in _geo.CITY_GEO.

City: version prices are one national ex-showroom list (no city selector on the model page; the separate
"<model>-price.html" iframe app loads files from an S3 bucket using credentials embedded in its JS - NOT used), so
prices() returns city="India (national)".
Verified 2026-10-20: Kiger AUTHENTIC 5,81,000 == JSON-LD "price":"581000" and the "₹5,81,000" on the Kiger page;
Duster authentic TCe 100 MT 10,49,000 == "range starts at ₹ 10.49 lakh" on the Duster offers page.
Known gaps: dual-tone / colour surcharges not included (base version price only); engine cc and seats not in the
version data; Renault does not publish body type in a structured field (body_type None); dealer emails are not
published by the locator.
"""

from __future__ import annotations

import datetime as dt
import html as _html
import json
import re
import time

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from . import _offers as _o
from ._geo import geo

BASE = "https://www.renault.co.in"
DELAY = 0.7
NATIONAL = "India (national)"
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _state(page: str) -> dict:
    m = re.search(r'window\.APP_STATE=JSON\.parse\((".*?")\);?\s*</script>', page, re.S)
    if not m:
        raise NotSupported("renault.co.in page no longer exposes window.APP_STATE")
    return json.loads(json.loads(m.group(1)))


def _text(page: str) -> str:
    page = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)
    s = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " | ", page)))
    return re.sub(r"(\| )+", "| ", s)


def _trans(v: dict) -> str:
    g, e = (v.get("gearboxTypeCode") or "").upper(), (v.get("engineName") or "").upper()
    if "CVT" in g or "CVT" in e:
        return "CVT"
    if "DCT" in e or "EDC" in g:
        return "DCT"
    if "AMT" in e or g.startswith("BVR"):
        return "AMT"
    if "E-TECH" in e or "HYBRID" in e:
        return "Automatic"
    return "Manual"


def _fuel(v: dict) -> str:
    cat, f = (v.get("energyCategory") or "").lower(), (v.get("mainFuelTypeCode") or "").upper()
    if cat in ("hev",):
        return "Strong Hybrid"
    if cat in ("bev", "ev"):
        return "Electric"
    if "CNG" in f or "GNV" in f or cat == "cng":
        return "CNG"
    if f in ("GAZ", "DIE", "DSL"):
        return "Diesel"
    return "Petrol"


RENAULT_LOCAL_IMAGES = {
    "duster": "/models/renault/duster.png",
    "kiger": "/models/renault/kiger.png",
    "kwid": "/models/renault/kwid.png",
    "triber": "/models/renault/triber.png",
}


class RenaultAdapter(BrandAdapter):
    brand = "Renault"
    slug = "renault"
    website = BASE

    def __init__(self):
        self._c = None

    def _client(self):
        if self._c is None:
            self._c = self.client()
        return self._c

    def _get(self, url, **kw):
        time.sleep(DELAY)
        r = self._client().get(url if url.startswith("http") else BASE + url, **kw)
        r.raise_for_status()
        return r

    def models(self) -> list[dict]:
        st = _state(self._get("/").text)
        out, seen = [], set()

        def walk(o):
            if isinstance(o, dict):
                if "modelAdmin" in o and "modelData" in o:
                    a, d = o["modelAdmin"], o["modelData"] or {}
                    if a.get("modelAdminId") not in seen and a.get("modelHomepageURL"):
                        seen.add(a["modelAdminId"])
                        m_name = a.get("shortModelName") or a.get("modelName") or ""
                        img = a.get("imageURI")
                        for k, v in RENAULT_LOCAL_IMAGES.items():
                            if k.lower() in m_name.lower():
                                img = v
                                break
                        out.append({"name": m_name, "id": a["modelAdminId"],
                                    "url": BASE + a["modelHomepageURL"], "body_type": None,
                                    "image_url": img, "min_price": d.get("minPrice")})
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(st)
        if not out:
            raise NotSupported("Renault model menu not found in APP_STATE")
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out, seen = [], set()
        for m in self.models():
            st = _state(self._get(m["url"]).text)
            data = (((st.get("page") or {}).get("data") or {}).get("modelParams") or {}).get("data") or {}
            name = data.get("label") or m["name"]
            for g in data.get("grades") or []:
                for v in g.get("versions") or []:
                    price = v.get("startingPrice") or v.get("minPrice")
                    key = (data.get("modelSpecCode") or name, v.get("code"), v.get("label"))
                    if not price or key in seen:       # Duster E-Tech versions appear on two model pages
                        continue
                    seen.add(key)
                    out.append(Variant(model=name, variant=v.get("label", "").strip(), fuel=_fuel(v),
                                       transmission=_trans(v), ex_showroom_inr=int(price), city=NATIONAL,
                                       source_url=m["url"], model_url=m["url"], image_url=m.get("image_url")))
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        if not g:
            raise NotSupported(f"no coordinates configured for {city!r} (add to _geo.CITY_GEO)")
        state, lat, lng = g
        time.sleep(DELAY)
        r = self._client().post(f"{BASE}/wired/commerce/v2/dealers/locator",
                                json={"brand": "renault", "location": {"lat": lat, "lon": lng, "country": "IN"},
                                      "count": 100, "milesUnit": False, "language": "en"},
                                headers={"Referer": f"{BASE}/find-a-dealer.html", "Origin": BASE})
        r.raise_for_status()
        out = []
        for x in r.json() or []:
            rn = x.get("renault") or {}
            dom = rn.get("domains") or {}
            if not dom.get("newVehicles") or (x.get("locality") or "").strip().lower() != city.lower():
                continue
            a, gl = x.get("address") or {}, x.get("geolocalization") or {}
            out.append(Dealer(name=x.get("commonName") or x.get("name"), address=a.get("streetAddress") or "",
                              city=city, state=state, pincode=a.get("postalCode"),
                              phone=(x.get("telephone") or {}).get("value"), email=None, lat=gl.get("lat"), lng=gl.get("lon"),
                              kind="sales+service" if any("workshop" in (a.get("description") or "").lower() for a in x.get("dealerActivities") or []) else "sales",
                              source_url=f"{BASE}/find-a-dealer.html"))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        links = sorted(set(re.findall(r'href="(/car-offers/[a-z0-9\-]+-offers\.html)"', self._get("/car-offers.html").text)))
        if not links:
            raise NotSupported("renault.co.in/car-offers.html lists no /car-offers/<model>-offers.html pages")
        names = {}
        try:
            names = {re.sub(r"[^a-z0-9]", "", m["name"].lower()): m["name"] for m in self.models()}
        except NotSupported:
            pass
        g = geo(city)
        state = g[0] if g else None
        out = []
        for path in links:
            slug = path.split("/")[-1].replace("-offers.html", "")
            out += _renault_page(_text(self._get(path).text), names.get(slug.replace("-", ""), slug.title()),
                                 BASE + path, city, state)
        return out

    def specs(self):
        """Each model page's window.APP_STATE.page.data.modelParams.data.engines[] carries the engine sheet Renault shows
        per powertrain (label "1L turbo CVT": maximumPower, torque, engineSize, gearboxType, fuelType - each a
        {label, value} pair); a version's engineName names its engine. The per-grade equipment list there is only
        option codes, and the /specifications.html tables are filled client-side from the configurator, so no
        features."""
        from ._spec_kit import SpecSink
        fields = (("maximumPower", "Engine", "max_power"), ("torque", "Engine", "max_torque"),
                  ("engineSize", "Engine", "displacement"), ("gearboxType", "Performance", "gearbox"))
        priced = {(v.model, v.variant): v for v in self.prices("Hyderabad")}
        specs, done = [], set()
        for m in self.models():
            st = _state(self._get(m["url"]).text)
            data = (((st.get("page") or {}).get("data") or {}).get("modelParams") or {}).get("data") or {}
            name = data.get("label") or m["name"]
            engines = {e.get("label"): e for e in data.get("engines") or []}
            for g in data.get("grades") or []:
                for ver in g.get("versions") or []:
                    v = priced.get((name, (ver.get("label") or "").strip()))
                    e = engines.get(ver.get("engineName"))
                    if not v or not e or (v.model, v.variant) in done:
                        continue
                    done.add((v.model, v.variant))
                    sink = SpecSink(v.model, v.variant, v.fuel, v.transmission)
                    for f, grp, key in fields:
                        x = e.get(f) or {}
                        val = str(x.get("value") or "").strip()
                        if val and val != "NC" and x.get("label") and x.get("label") != "NC":
                            sink.spec(grp, key, x["label"], val, m["url"], check=False)
                    specs += sink.out()[0]
        if not specs:
            raise NotSupported("renault.co.in model pages carried no engine sheets")
        return specs, []


def _clauses(tc: list[str], rx: str) -> list[str]:
    return [c for c in tc if re.search(rx, c, re.I)]


def _renault_page(s: str, model: str, url: str, city: str, state: str | None) -> list[Offer]:
    """One /car-offers/<model>-offers.html page: headline bullets (between 'range starts at' and 'request this offer')
    joined to the 'terms & conditions' paragraph that explains each bullet."""
    hm = re.search(r"range starts at[^|]*\|(.*?)\|\s*(?:request this offer|Explore More|test drive)", s, re.I)
    tm = re.search(r"terms & conditions(.*?)Benefits applicable for bookings between\s*\|?\s*([^|]*?)\|?\s*only", s, re.I | re.S)
    if not hm:
        return []
    head = [x.strip() for x in hm.group(1).split("|") if x.strip() and x.strip() not in ("^", "#", "##", "*")]
    tc = [x.strip(" *#^") for x in (tm.group(1) if tm else "").split("|") if len(x.strip(" *#^:")) > 3]
    tc_text = " ".join(tc)
    # region rule, e.g. "KWID 2026 (All India except Kerala, ..., Telangana, ...)"
    ex = re.search(r"All India except ([^)]*)\)", s)
    if ex and state and state.lower() in ex.group(1).lower():
        return []
    vf = vu = None
    if tm:
        vm = re.search(r"(\d+)\w*\s+([A-Za-z]+)'?(\d{2})?\s*-\s*(\d+)\w*\s+([A-Za-z]+)'?(\d{2})", tm.group(2))
        if vm:
            end = _o.day_month_year(vm.group(4), vm.group(5), vm.group(6))
            start = _o.day_month_year(vm.group(1), vm.group(2), vm.group(3) or vm.group(6))
            vu, vf = (end.isoformat() if end else None), (start.isoformat() if start else None)
    if _o.expired(vu):
        return []
    edition = next((h for h in head if not re.search(r"benefit|offer|discount|loyalty|exchange|cash|referral|scrappage", h, re.I)), None)
    head = [h for h in head if h != edition and not h.startswith("(")]
    region = f" ({ex.group(0).rstrip(')')})" if ex else ""
    base_details = f"{edition + ': ' if edition else ''}"
    out: list[Offer] = []

    def add(kind, title, amt, cond, variant=None, details=None):
        out.append(Offer(model=model, title=title, amount_inr=amt, details=(details or title) + region, valid_until=vu,
                         city=city if ex else None, source_url=url, kind=kind, conditions=cond, valid_from=vf,
                         variant=variant))

    def per_variant(kind, label, clauses, headline_amt, headline):
        """'Cash offer of INR 25,000 for Evolution+, Techno & Emotion' -> one offer per amount/variant group."""
        done = False
        for c in clauses:
            qual = ""
            for part in re.split(r"(?<=[a-z+])(?=For [A-Z])|\.\s+", c):
                if re.match(r"For ", part):
                    qual = re.sub(r"\s+offer.*", "", part[4:], flags=re.I)
                for piece in re.split(r"&\s*(?=INR)", part):
                    pm = re.search(r"INR\s*([\d,]+)(.*?)\s+(?:for|on)\s+(.+?)(?:\s+[Vv]ariants?)?\s*\.?\s*$", piece)
                    if not pm or re.search(r"\ball (?:variants|versions)\b", pm.group(3), re.I):
                        continue
                    amt = int(pm.group(1).replace(",", ""))
                    extra = pm.group(2).strip()
                    t = f"{label}{' (' + qual + ')' if qual else ''} {_o.inr(amt)}{' ' + extra if extra else ''}"
                    if headline_amt and amt == headline_amt and re.search(r"up ?to", headline, re.I):
                        t = t.replace(_o.inr(amt), "up to " + _o.inr(amt), 1)
                    add(kind, t, amt, c, variant=pm.group(3).strip(), details=base_details + headline + " | " + c)
                    done = True
        if not done:
            add(kind, f"{label} up to {_o.inr(headline_amt)}" if headline_amt else label, headline_amt,
                " ".join(clauses) or None, details=base_details + headline)

    total = None
    for h in head:
        k = "cash" if re.match(r"cash", h, re.I) else _o.kind_of(h)
        amt = _o.amount(h)
        if re.match(r"benefits? up ?to", h, re.I):
            total = (h, amt)
            continue
        if re.search(r"referral", h, re.I):
            cl = _clauses(tc, r"referral")
            add("other", "Referral benefit", None, " ".join(cl) or None, details=base_details + h)
        elif k == "scrappage":
            cl = _clauses(tc, r"RELIVE|scrappage")
            add("scrappage", f"RELIVE scrappage exchange benefit up to {_o.inr(amt)}", amt, " ".join(cl) or None,
                details=base_details + h)
        elif k == "loyalty":
            cl = _clauses(tc, r"loyalty")
            la = _o.amount(" ".join(cl))
            add("loyalty", f"Loyalty benefit up to {_o.inr(la)}" if la else "Loyalty benefit", la, " ".join(cl) or None,
                details=base_details + h + (" | " + " ".join(cl) if cl else ""))
        elif k == "corporate":
            cl = _clauses(tc, r"corporate|rural|institutional")
            for c in cl:
                cm = re.search(r"Corporate dis\w* of upto INR\s*([\d,]+)", c, re.I)
                if cm:
                    a = int(cm.group(1).replace(",", ""))
                    add("corporate", f"Corporate discount up to {_o.inr(a)}", a, c, details=base_details + h + " | " + c)
                rm = re.search(r"Rural offer of INR\s*([\d,]+)", c, re.I)
                if rm:
                    a = int(rm.group(1).replace(",", ""))
                    add("other", f"Rural offer {_o.inr(a)}", a, c, details=base_details + "Rural offer | " + c)
            if not any(o.kind == "corporate" for o in out):
                add("corporate", "Corporate discount", None, " ".join(cl) or None, details=base_details + h)
        elif k in ("cash", "exchange", "finance"):
            if k == "finance" or re.search(r"rate of interest", h, re.I):
                rm = re.search(r"([\d.]+%)\s*Rate of Interest", h, re.I)
                if rm:
                    add("finance", f"{rm.group(1)} rate of interest (instead of cash offer)", None,
                        " ".join(_clauses(tc, r"ROI|rate of interest|Renault Finance")) or None, details=base_details + h)
            if k != "finance":
                label = "Cash offer" if k == "cash" else "Exchange benefit"
                cl = _clauses(tc, r"^cash" if k == "cash" else r"^exchange benefit|duster to duster")
                per_variant(k, label, cl, amt, h)
        else:
            add(k, h, amt, None, details=base_details + h)

    if total:
        h, amt = total
        inc = next((c for c in tc if re.search(r"Benefits upto [\d,]+ include", c, re.I)), "")
        comps = re.findall(r"(cash|exchange) benefit(?: upto INR\s*([\d,]+K?))?", inc, re.I)
        have = {o.kind for o in out}
        if comps:
            for kind, a in comps:
                kind = kind.lower()
                if kind in have:
                    continue
                val = _o.amount("INR " + a) if a else (amt if len(comps) == 1 else None)
                label = "Cash benefit" if kind == "cash" else "Exchange benefit"
                add(kind, f"{label} up to {_o.inr(val)}" if val else label, val, inc,
                    variant="select variants" if "select variants" in inc.lower() else None,
                    details=base_details + h + " | " + inc)
        elif not have & {"cash", "exchange"}:
            add("other", f"Total benefits up to {_o.inr(amt)}", amt, inc or None, details=base_details + h)
    return out


ADAPTER = RenaultAdapter()
