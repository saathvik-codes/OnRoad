"""
Isuzu Motors India - https://www.isuzu.in  (personal-use models: MU-X, V-Cross, Hi-Lander)

Endpoints used (robots.txt checked 2026-10-20: only /new_ambulance.html and /cgi-bin/ are disallowed):
  GET  /getprice                 "Get the price details" page: model cards (name, image) for models()
  GET  /Javscript/getprice.js    the data behind that page's State -> Model -> "Get Price" widget: a JS object
                                 modelsByState = {"<State>": [{name, price: "Starts From ₹ 21,50,080.00 in <State>"}]}
  GET  /vcross, /hilander, /mux  spec tables ("Displacement ... 1898 cm3", "Seating Capacity (Incl. Driver) 5")
  GET  /Javscript/style.js       the data behind /finddealers: State -> city options (selectstate) and one
                                 hard-coded block per city (displayResult) with Showroom/Service name, address,
                                 phone, e-mail

City: prices are published per STATE, so prices() returns city="<State>" (Hyderabad -> "Telangana").
Verified 2026-10-20 in getprice.js under "Telangana": Hi-Lander 2WD MT Standard 21,50,080; V-Cross 4WD AT Z Prestige
Premium 30,78,000; Mu-X 4WD AT Premium 37,98,580 (13 variants: Hi-Lander 4, V-Cross 6, MU-X 3).
Hyderabad dealers: Mahavir Isuzu L. B. Nagar (sales), Mahavir ISUZU Kukatpally (sales+service), JHABAKH AUTO
Vanasthalipuram (service).
Known gaps / caveats: the widget labels its price "Starts From ... in <state>" and never says ex-showroom vs on-road;
the Telangana entries are textually identical to Tamil Nadu's and even read "in Tamilnadu" (site copy-paste), they are
emitted as the site's Telangana price. D-Max / S-CAB / S-CAB Z are commercial pickups and are not emitted. Dealer
lat/lng not published (map links are booking widgets). No offers page exists (offers() -> NotSupported).
"""

from __future__ import annotations

import re
import time
from urllib.parse import quote

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import clean, inr, norm
from ._geo import geo

BASE = "https://www.isuzu.in"
PRICE_JS = f"{BASE}/Javscript/getprice.js"
DEALER_JS = f"{BASE}/Javscript/style.js"
DELAY = 1.0

# price-name prefix -> (model, page, body type)
MODELS = {
    "mux": ("MU-X", f"{BASE}/mux", "SUV"),
    "vcross": ("V-Cross", f"{BASE}/vcross", "Pickup"),
    "hilander": ("Hi-Lander", f"{BASE}/hilander", "Pickup"),
}


def _model_key(name: str) -> str | None:
    n = norm(name)
    return next((k for k in MODELS if n.startswith(k) or n.startswith("isuzu" + k)), None)


class IsuzuAdapter(BrandAdapter):
    brand = "Isuzu"
    slug = "isuzu"
    website = BASE

    def __init__(self):
        self._c = None
        self._last = 0.0

    def _get(self, url: str) -> str:
        if self._c is None:
            self._c = self.client()
        gap = time.monotonic() - self._last
        if self._last and gap < DELAY:
            time.sleep(DELAY - gap)
        self._last = time.monotonic()
        r = self._c.get(url)
        r.raise_for_status()
        return r.text

    def models(self) -> list[dict]:
        page = self._get(f"{BASE}/getprice")
        out = []
        for m in re.finditer(r'<img class="lozad" (?:data-)?src="([^"]+)"[^>]*>\s*<div class="car-d-text">\s*<h6>(.*?)</h6>',
                             page, re.S):
            key = _model_key(clean(m.group(2)))
            if key:
                name, url, body = MODELS[key]
                out.append({"name": name, "url": url, "body_type": body,
                            "image_url": f"{BASE}/{quote(m.group(1).lstrip('/'))}"})
        return out

    def _specs(self, url: str) -> tuple[int | None, int | None]:
        try:
            t = clean(re.sub(r"(?s)<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", self._get(url)))
        except Exception:
            return None, None
        cc = re.search(r"Displacement[^0-9]{0,15}(\d{4})\s*cm", t)
        seats = re.search(r"Seating Capacity \(Incl\. Driver\)\s*(\d)", t) or re.search(r"Seating\s*(\d)\s*persons", t)
        return (int(cc.group(1)) if cc else None), (int(seats.group(1)) if seats else None)

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown (add to _geo.CITY_GEO); Isuzu prices are per state")
        state = g[0]
        js = self._get(PRICE_JS)
        start = re.search(r'(?:^|[\s{,])"?%s"?\s*:\s*\[' % re.escape(state), js)
        if not start:
            raise NotSupported(f"Isuzu getprice.js has no price list for {state}")
        block = js[start.end():js.find("]", start.end())]
        images = {_model_key(m["name"]): m["image_url"] for m in self.models()}
        specs: dict[str, tuple] = {}
        out = []
        for name, price in re.findall(r'name:\s*"([^"]+)"\s*,\s*price:\s*"([^"]+)"', block):
            name = clean(name)
            key = _model_key(name)
            amount = inr(re.search(r"[\d,]{6,}", price).group(0)) if re.search(r"[\d,]{6,}", price) else None
            if not key or not amount:
                continue
            model, url, body = MODELS[key]
            if key not in specs:
                specs[key] = self._specs(url)
            cc, seats = specs[key]
            variant = re.sub(r"(?i)^(mu-?x|v-?cross|hi-?lander)\s*", "", name).strip()
            out.append(Variant(model=model, variant=variant, fuel="Diesel",
                               transmission="Automatic" if re.search(r"\bAT\b", name) else "Manual",
                               ex_showroom_inr=amount, city=state, source_url=PRICE_JS, body_type=body,
                               engine_cc=cc, seats=seats, model_url=url, image_url=images.get(key)))
        if not out:
            raise NotSupported(f"Isuzu getprice.js {state} list has no MU-X / V-Cross / Hi-Lander rows")
        return out

    def specs(self):
        """/vcross, /hilander, /mux: spec and feature <table>s whose header row is 'Model | <full variant name> ...'
        (tables without a header row continue the previous one). A column applies to a priced variant only when its
        name, without the model prefix, is the variant's name less the price list's Standard / Premium suffix."""
        from bs4 import BeautifulSoup
        from ._spec_kit import SpecSink, html_tables, is_tick, spec_key
        priced = self.prices("Hyderabad")
        specs, feats = [], []

        def bare(n):
            return re.sub(r"\s+", " ", re.sub(r"(?i)^(mu-?x|v-?cross|hi-?lander)\s*", "", n or "")).strip().lower()
        for url in dict.fromkeys(v.model_url for v in priced if v.model_url):
            tables = html_tables(BeautifulSoup(self._get(url), "html.parser").find_all("table"), url)
            for v in (x for x in priced if x.model_url == url):
                sink = SpecSink(v.model, v.variant, v.fuel, v.transmission)
                # the price list splits each spec-table trim into "... Standard" / "... Premium" (paint) lines
                trim = re.sub(r"\s+(standard|premium)$", "", bare(v.variant))
                done = set()
                for t in tables:
                    # a column applies when it names this trim; an unheaded single-column table is the whole model's
                    idx = [i for i, h in enumerate(t.cols) if bare(h) == trim or (not h and len(t.cols) == 1)]
                    for sec, lab, vals in t.rows:
                        vs = {vals[i] for i in idx if i < len(vals)}
                        if len(vs) != 1:
                            continue
                        val = vs.pop()
                        k = spec_key(sec, lab)
                        if re.search(r"(?i)\bdeck\b", lab):
                            continue          # "Deck Inner (LxWxH)" is the load bed, not the vehicle's length/width/height
                        if is_tick(val):
                            sink.feature(lab, val, url)
                        elif k and k[1] in done:
                            continue          # first published value of a spec key wins
                        else:
                            if k:
                                done.add(k[1])
                            sink.row(sec, lab, val, url)
                s_, f_ = sink.out()
                specs += s_
                feats += f_
        if not specs and not feats:
            raise NotSupported("isuzu.in model pages had no spec column matching a priced variant")
        return specs, feats

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown (add to _geo.CITY_GEO)")
        state = g[0]
        js = self._get(DEALER_JS)
        # city options the locator offers for this state
        sm = re.search(r'selectedVal === "%s"\s*\)\s*\{(.*?)\}' % re.escape(state), js, re.S)
        options = re.findall(r"<option value='([^']+)'>", sm.group(1)) if sm else []
        found: dict[str, Dealer] = {}
        for opt in options:
            bm = re.search(r'selectedValthree === "%s"\s*\)\s*\{' % re.escape(opt), js)
            if not bm:
                continue
            nxt = js.find("selectedValthree ===", bm.end())
            block = js[bm.end(): nxt if nxt > 0 else len(js)]
            section, cur = "sales", None
            for text in re.findall(r'textContent\s*=\s*"([^"]*)"', block):
                text = re.sub(r"\s+", " ", text).strip()
                if text in ("Showroom", "Service"):
                    section, cur = ("sales" if text == "Showroom" else "service"), None
                elif not text or text in ("For Booking", "Get direction") or text.startswith("Dealer Service Manager"):
                    continue
                elif text.startswith("Address"):
                    if cur is not None:
                        cur["address"] = re.sub(r"^Address\s*:\s*", "", text)
                elif text.startswith("Phone"):
                    if cur is not None and not cur.get("phone"):
                        cur["phone"] = re.sub(r"^Phone\s*:\s*", "", text).strip()
                elif text.startswith("Email"):
                    if cur is not None and not cur.get("email"):
                        cur["email"] = re.sub(r"^Email id\s*:\s*", "", text).strip()
                else:
                    cur = {"name": text, "kind": section}
                    cur_list = found.setdefault("_raw", [])
                    cur_list.append(cur)
        out: dict[str, Dealer] = {}
        for d in found.get("_raw", []):
            addr = re.sub(r"\s*,\s*", ", ", d.get("address", "")).strip(" ,")
            pin = re.search(r"(\d{6})\s*$", addr)
            in_city = city.lower() in addr.lower() or (
                city.lower() == "hyderabad" and pin is not None and pin.group(1).startswith("500"))
            if not addr or not in_city:
                continue
            key = norm(addr)[:40]
            if key in out:
                if out[key].kind != d["kind"]:
                    out[key].kind = "sales+service"
                continue
            out[key] = Dealer(name=d["name"], address=addr, city=city, state=state,
                              pincode=pin.group(1) if pin else None, phone=d.get("phone"), email=d.get("email"),
                              lat=None, lng=None, kind=d["kind"], source_url=f"{BASE}/finddealers")
        if not out:
            raise NotSupported(f"no Isuzu outlet for {city!r} in the official locator data")
        return list(out.values())

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("isuzu.in publishes no offers page")


ADAPTER = IsuzuAdapter()
