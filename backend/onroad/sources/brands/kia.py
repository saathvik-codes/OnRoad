"""
Kia India adapter (www.kia.com/in).

Endpoints (public; called by the site's own configurator and dealer-locator clientlibs under
/etc.clientlibs/kia2/components/in/content/buy/...):
  cities  : POST https://www.kia.com/api/kia2_in/findAdealer.getStateCity.do   form: dealerType=S
            -> {data:{stateAndCity:[{val1:{key:'TS',value:'Telangana'}, val2:[{key:'S50',value:'Hyderabad'},..]}]}}
  models  : header navigation of https://www.kia.com/in/home.html (model list + page URLs)
            POST https://www.kia.com/api/kia2_in/configure.getModelList.do     form: stateCode, cityCode
            (model codes, image, "starting MSRP" used by /in/buy/configure/select-a-vehicle.html)
  prices  : GET  https://www.kia.com/api/kia2_in/configure.getVrntList.do      params: modelCode, stateCode, cityCode
            -> every variant with price per paint group {M: {...}, N: {...}}; the configurator shows
               price[group].interExsrPrice as "Ex-showroom", so that is the value used here.
            Models that are not in the configurator (EV9 at time of writing): the model page FAQ sentence
            "starts at price of Rs X (Ex-showroom price all India)" is read live and returned as one row.
  dealers : POST https://www.kia.com/api/kia2_in/findAdealer.getDealerList.do  form: state, city, dealerType=S
  offers  : /in/utility/special-benefits-t-c.html and /in/utility/post-gst-benefits.html carry only T&C text;
            the benefit amounts are in banner images -> NotSupported. Re-checked 2026-10-22: home page, Sonet
            showroom page, /in/buy/book-online.html (redirects to sign-up), /in/buy/exchange-your-car.html, the
            configurator getVrntList.do JSON (no offer fields) and /in/sitemap.xml (only a 2025 pre-GST blog) have
            no offer amount, validity or JSON feed.

Verified 2026-10-19 (run from backend/):
  Seltos (MDBT0020) for TS/S50 (Hyderabad): HTE 6MT = Rs 11,24,900 and X Line (O) 7DCT = Rs 21,56,900, matching the
  FAQ on https://www.kia.com/in/our-vehicles/seltos/showroom.html ("base model HTE starts at Rs 11,24,900* and top
  model X Line (O) starts at Rs 21,56,900*"). The same Seltos call for Delhi (DL/N10) returned identical prices:
  Kia India prices are PAN-India ex-showroom (the post-GST page says "Ex-showroom price ... (PAN India)"), but the
  API is still called with the requested city so any future regional difference is picked up.
Known gaps:
  * Paint group 'N' (a few trims carry a second, ~Rs 20,000 higher price) is not named by the API; such rows are
    returned with the suffix "[paint group N]". Paint group 'M' is the standard price.
  * engine_cc: Kia publishes engines as "Smartstream G1.5" / "D1.5 CRDi" (litres), so engine_cc stays None.
  * Body type is not tagged in any Kia feed; BODY below follows Kia's own page wording (e.g. "sub-compact SUV",
    "7 seater", "Carnival Limousine") and is not price data.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import Polite, clean, inr, transmission, visible_text

SITE = "https://www.kia.com"
API = SITE + "/api/kia2_in"
HOME = SITE + "/in/home.html"

BODY = {
    "sonet": "SUV", "syros": "SUV", "seltos": "SUV", "sorento": "SUV", "syros-ev": "SUV", "ev9": "SUV",
    "ev6": "Crossover", "carens": "MUV", "carens-clavis": "MUV", "carens-clavis-ev": "MUV", "carnival": "MUV",
}
CITY_ALIASES = {"bengaluru": "bangalore", "gurugram": "gurgaon", "new delhi": "delhi", "mysuru": "mysore"}
KIA_FALLBACK_IMAGES = {
    "carnival": "https://www.kia.com/content/dam/kia2/in/en/images/360vr/carnival/8tb72hc5jgg000/exterior/gwp/08-m.png",
    "ev9": "https://www.kia.com/content/dam/kia2/in/en/images/360vr/ev9/dow7ybz7zhh325/exterior/obg/09-d.png",
}
NAV = re.compile(r'<a href="(/in/our-vehicles/([a-z0-9-]+)\.html)" class="d2-a[^"]*">\s*<span class="text">([^<]+)</span>')
TM = re.compile(r"\b(\d?(?:MT|AT|DCT|IVT|iMT|AMT))\b", re.I)


def _slug_from_code_name(name: str) -> str:
    # configurator model names: SONET, NEW_SELTOS, SYROS_EV, CLAVIS, CLAVIS_EV ...
    n = re.sub(r"^NEW_", "", name.upper()).replace("_", "-").lower()
    return {"clavis": "carens-clavis", "clavis-ev": "carens-clavis-ev"}.get(n, n)


def _disp(name: str) -> str:
    """'CARENS CLAVIS EV' -> 'Carens Clavis EV' (keeps EV/EV6/EV9 upper-case)."""
    if not name.isupper():
        return name
    return " ".join(w if w.startswith("EV") else w.title() for w in name.split())


class KiaAdapter(BrandAdapter):
    brand = "Kia"
    slug = "kia"
    website = SITE + "/in"

    def _city(self, h: Polite, city: str) -> tuple[str, str, str, str]:
        data = h.post(API + "/findAdealer.getStateCity.do", data={"dealerType": "S"}).json()["data"]["stateAndCity"]
        want = CITY_ALIASES.get(city.strip().lower(), city.strip().lower())
        for st in data:
            for c in st["val2"]:
                if c["value"].strip().lower() == want:
                    return st["val1"]["key"], c["key"], st["val1"]["value"], c["value"]
        raise NotSupported(f"Kia India lists no sales city named '{city}'")

    def _nav(self, h: Polite) -> list[tuple[str, str, str]]:
        page = h.get(HOME).text
        seen, out = set(), []
        for href, slug, name in NAV.findall(page):
            name = clean(name)
            if name and slug not in seen and "test" not in slug:
                seen.add(slug)
                out.append((slug, name, SITE + href))
        return out

    def _model_list(self, h: Polite, state: str, city: str) -> list[dict]:
        return h.post(API + "/configure.getModelList.do", data={"stateCode": state, "cityCode": city}).json()["data"]

    def models(self) -> list[dict]:
        with Polite(self.client()) as h:
            nav = self._nav(h)
            st, ct, _, _ = self._city(h, "Hyderabad")
            cfg = {_slug_from_code_name(m["modelName"]): m for m in self._model_list(h, st, ct)}
        out = []
        for slug, name, url in nav:
            m = cfg.get(slug, {})
            img = SITE + m["imgListD"] if m.get("imgListD") else KIA_FALLBACK_IMAGES.get(slug)
            out.append({"name": _disp(name), "url": url, "body_type": BODY.get(slug),
                        "image_url": img,
                        "fuel": "Electric" if slug.endswith("-ev") or slug in ("ev6", "ev9") else None,
                        "model_code": m.get("modelCode"), "source_url": HOME})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out: list[Variant] = []
        with Polite(self.client()) as h:
            st, ct, _, city_name = self._city(h, city)
            nav = self._nav(h)
            cfg = {_slug_from_code_name(m["modelName"]): m for m in self._model_list(h, st, ct)}
            for slug, name, url in nav:
                disp = _disp(name)
                m = cfg.get(slug)
                if not m:
                    out.extend(self._faq_price(h, slug, disp, url, city))
                    continue
                img = SITE + m["imgListD"] if m.get("imgListD") else None
                src = f"{API}/configure.getVrntList.do?modelCode={m['modelCode']}&stateCode={st}&cityCode={ct}"
                data = h.json(API + "/configure.getVrntList.do",
                              params={"modelCode": m["modelCode"], "stateCode": st, "cityCode": ct})["data"]
                is_ev = slug.endswith("-ev") or slug in ("ev6", "ev9")
                for v in data.get("variants", []):
                    vname = clean(v.get("variantName"))
                    short = re.sub(r"^KIA\s+(NEW\s+)?", "", vname, flags=re.I)
                    for prefix in (name, name.replace(" EV", ""), m["modelName"].replace("_", " ").replace("NEW ", "")):
                        if prefix and short.upper().startswith(prefix.upper() + " "):
                            short = short[len(prefix) + 1:]
                            break
                    vname = short.strip() or vname
                    upper = vname.upper()
                    if is_ev:
                        fuel = "Electric"
                    elif "HEV" in upper or "HYBRID" in upper:
                        fuel = "Hybrid"
                    elif "CRDI" in upper or re.search(r"\bD1\.\d", upper):
                        fuel = "Diesel"
                    else:
                        fuel = "Petrol"
                    tm = TM.search(vname)
                    trans = transmission(re.sub(r"^\d", "", tm.group(1))) if tm else ("Automatic" if is_ev else "")
                    kwh = re.search(r"(\d+(?:\.\d+)?)\s*KWH", upper)
                    for group, p in sorted((v.get("price") or {}).items()):
                        price = inr(p.get("interExsrPrice") or p.get("intraExsrPrice"))
                        if not price:
                            continue
                        out.append(Variant(
                            model=disp, variant=vname + ("" if group == "M" else f" [paint group {group}]"),
                            fuel=fuel, transmission=trans, ex_showroom_inr=price, city=city, source_url=src,
                            body_type=BODY.get(slug), battery_kwh=float(kwh.group(1)) if kwh else None,
                            model_url=url, image_url=img))
        if not out:
            raise NotSupported(f"Kia configurator returned no prices for '{city}'")
        return out

    def _faq_price(self, h: Polite, slug: str, name: str, url: str, city: str) -> list[Variant]:
        """Model not in the configurator: read the 'starts at price of Rs X (Ex-showroom price all India)' FAQ."""
        # visible FAQ only: on 2026-10-19 the EV9 JSON-LD said Rs 1,29,90,000 while the visible FAQ said
        # Rs 1,29,91,312; the visible text is what a buyer reads.
        page = visible_text(h.get(SITE + f"/in/our-vehicles/{slug}/showroom.html").text)
        m = re.search(r"starts at (?:a )?price of\s*₹\s*([\d ,]+)\*?\s*\(Ex-showroom price all India\)", page, re.I)
        if not m:
            return []
        return [Variant(model=name, variant="Starting price (only figure published; model not in configurator)",
                        fuel="Electric" if slug in ("ev6", "ev9") or slug.endswith("-ev") else "",
                        transmission="Automatic" if slug in ("ev6", "ev9") or slug.endswith("-ev") else "",
                        ex_showroom_inr=inr(m.group(1)), city=city, body_type=BODY.get(slug),
                        source_url=SITE + f"/in/our-vehicles/{slug}/showroom.html", model_url=url)]

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite(self.client()) as h:
            st, ct, state_name, _ = self._city(h, city)
            rows = h.post(API + "/findAdealer.getDealerList.do",
                          data={"state": st, "city": ct, "dealerType": "S"}).json()["data"]
        src = f"{SITE}/in/buy/find-a-dealer/result.html?state={st}&city={ct}  (API {API}/findAdealer.getDealerList.do)"
        out = []
        for r in rows:
            addr = clean(", ".join(x for x in (r.get("address1"), r.get("address2"), r.get("address3")) if x))
            addr = re.sub(r",\s*,", ",", addr)
            pin = re.findall(r"\b(\d{3}\s?\d{3})\b", addr)
            phones = list(dict.fromkeys(p for p in (r.get("phone1"), r.get("phone2")) if p))
            out.append(Dealer(
                name=clean(r.get("dealerName")), address=addr, city=r.get("cityName") or city,
                state=r.get("stateName") or state_name, pincode=pin[-1].replace(" ", "") if pin else None,
                phone=", ".join(phones) or None, email=r.get("email") or None,
                lat=float(r["lat"]) if r.get("lat") else None, lng=float(r["lng"]) if r.get("lng") else None,
                kind="sales" if (r.get("dealerType") or "").lower().startswith("sales") else (r.get("dealerType") or "sales").lower(),
                source_url=src, website=r.get("website") or None))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported(
            "Kia India publishes no offer amounts as text/JSON (checked 2026-10-22): /in/utility/special-benefits-t-c.html "
            "('Monsoon benefits / South Offers T&C': benefits = extended warranty, exchange bonus, special, corporate "
            "and accessories benefit; applicable in AP, Telangana, Karnataka, Kerala, Tamil Nadu, Pondicherry) and "
            "/in/utility/post-gst-benefits.html are terms text only, with no amounts or dates; home page, model "
            "showroom pages, /in/buy/* pages, the configurator API (configure.getVrntList.do) and /in/sitemap.xml "
            "carry no offer figures.")

    # ---------------------------------------------------------------- specs
    def specs(self):
        """Per-trim specs + standard equipment from /in/our-vehicles/<model>/specs.html (see module docstring)."""
        from ..base import Feature, Spec
        from ._spec_common import feature_keys, with_unit

        priced: dict[tuple[str, str], list[Variant]] = {}
        for v in self.prices("Hyderabad"):
            priced.setdefault((v.model, re.sub(r" \[paint group \w+\]$", "", v.variant)), []).append(v)
        specs, feats = [], []
        with Polite(self.client()) as h:
            st, ct, _, _ = self._city(h, "Hyderabad")
            nav = self._nav(h)
            cfg = {_slug_from_code_name(m["modelName"]): m for m in self._model_list(h, st, ct)}
            for slug, name, url in nav:
                m = cfg.get(slug)
                if not m:
                    continue                      # not in the configurator -> no priced variants to attach to
                disp = _disp(name)
                data = h.json(API + "/configure.getVrntList.do",
                              params={"modelCode": m["modelCode"], "stateCode": st, "cityCode": ct})["data"]
                surl = f"{SITE}/in/our-vehicles/{slug}/specs.html"
                model_rows, trim_rows, trim_feats = _kia_spec_page(h.get(surl).text)
                trims = {_kia_trim_key(t): t for t in set(trim_rows) | set(trim_feats)}
                for raw in data.get("variants", []):
                    targets = priced.get((disp, _kia_vname(raw, name, m)), [])
                    trim = trims.get(_kia_trim_key(raw.get("variantGroup") or ""))
                    if not targets or not trim:
                        continue
                    rows = dict(model_rows)
                    rows.update(dict(trim_rows.get(trim, [])))
                    for t in targets:
                        for cap, val in rows.items():
                            spec = _kia_spec_key(cap)
                            if spec:
                                group, key, unit = spec
                                specs.append(Spec(t.model, t.variant, t.fuel, t.transmission, group, key, cap,
                                                  with_unit(val, unit), surl))
                        for label in trim_feats.get(trim, []):
                            for key in feature_keys(label):
                                feats.append(Feature(t.model, t.variant, t.fuel, t.transmission, key, label, surl))
        if not specs and not feats:
            raise NotSupported("Kia India specs pages returned no per-trim data")
        return specs, feats


# specs.html sections that are not equipment lists
_KIA_NON_FEATURE = {"highlights", "color", "colour", "dimensions", "powertrain", "variants", "technical specs"}
# (regex on the site's own row caption, group, key, unit taken from the caption)
_KIA_SPECS = [(re.compile(p, re.I), g, k, u) for p, g, k, u in [
    (r"^overall length", "Dimensions", "length", "mm"), (r"^overall width", "Dimensions", "width", "mm"),
    (r"^overall height", "Dimensions", "height", "mm"), (r"^wheelbase", "Dimensions", "wheelbase", "mm"),
    (r"^ground clearance", "Dimensions", "ground_clearance", "mm"), (r"^boot space", "Capacity", "boot_space", None),
    (r"^fuel tank", "Capacity", "fuel_tank", "l"), (r"^seating capacity", "Capacity", "seating_capacity", None),
    (r"^displacement", "Engine", "displacement", None), (r"^max\.? power \(ps\)$", "Performance", "max_power", "Ps"),
    (r"^max\.? torque \(nm\)$", "Performance", "max_torque", "Nm"), (r"^battery capacity", "Battery", "battery_capacity", None),
    (r"^dc fast charge.*350\s*kw", "Battery", "charging_time_dc", None),
    (r"^dc fast charge.*50\s*kw", "Battery", "charging_time_dc_50kw", None),
    (r"^range in km", "Efficiency", "range", "km"), (r"^0-100 kmph \(sec\)", "Performance", "acceleration_0_100", "s"),
    (r"^max tyre|^tyre size", "Chassis", "tyre_size", None), (r"^brakes( – |\s*-\s*)front", "Chassis", "front_brakes", None),
    (r"^brakes( – |\s*-\s*)rear", "Chassis", "rear_brakes", None), (r"^brakes$", "Chassis", "brakes", None),
    (r"^drive$", "Chassis", "drivetrain", None), (r"^suspension( – |\s*-\s*)front", "Chassis", "front_suspension", None),
    (r"^suspension( – |\s*-\s*)rear", "Chassis", "rear_suspension", None), (r"^suspension$", "Chassis", "suspension", None),
]]


def _kia_spec_key(cap: str):
    for rx, g, k, u in _KIA_SPECS:
        if rx.search(cap.strip()):
            return g, k, u
    return None


def _kia_vname(v: dict, name: str, m: dict) -> str:
    """Same variant label prices() derives from one getVrntList.do row (before any paint-group suffix)."""
    vname = clean(v.get("variantName"))
    short = re.sub(r"^KIA\s+(NEW\s+)?", "", vname, flags=re.I)
    for prefix in (name, name.replace(" EV", ""), m["modelName"].replace("_", " ").replace("NEW ", "")):
        if prefix and short.upper().startswith(prefix.upper() + " "):
            short = short[len(prefix) + 1:]
            break
    return short.strip() or vname


def _kia_trim_key(t: str) -> str:
    """'X LINE (O)' / 'X-Line(O)' -> 'xlineo'; 'HTK Plus' -> 'htk+'; seat-count tokens (6/7) dropped."""
    t = re.sub(r"\bplus\b", "+", t, flags=re.I)
    t = re.sub(r"(?<![\w.])[67](?![\w.])", " ", t)
    return re.sub(r"[\s\-()]", "", t.lower())


def _kia_spec_page(page: str):
    """-> (model-level [(caption, value)], {trim: [(caption, value)]}, {trim: [equipment line]})."""
    page = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    model_rows, trim_rows, trim_feats = [], {}, {}
    for sec in re.split(r'<h2 class="accordion-title specs-heading">', page)[1:]:
        sec = sec[:sec.find("</section>")]
        title = clean(sec[:sec.find("</h2>")]).lower()
        if title in ("dimensions", "technical specs"):
            model_rows += [(clean(a), clean(b)) for a, b in re.findall(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", sec, re.S)]
        for trim, body in re.findall(r'<ul data-spec="([^"]*)" class="specs-list">(.*?)</ul>', sec, re.S):
            for li in re.findall(r'<li class="specs-item">(.*?)</li>', body, re.S):
                cm = re.search(r'<span class="cap[^"]*">(.*?)</span>\s*<span class="measure">(.*?)</span>', li, re.S)
                if title in ("dimensions", "technical specs"):
                    if cm:
                        trim_rows.setdefault(trim, []).append((clean(cm.group(1)), clean(cm.group(2))))
                elif title not in _KIA_NON_FEATURE and not title.startswith(("what ", "how ", "which ")):
                    text = clean(li)
                    # lines tied to one engine/gearbox ("(Automatic Only)", "(G1.5 MT only)") are not standard on
                    # every variant of the trim, so they are left out rather than guessed
                    if text and not re.search(r"\bonly\b", text, re.I):
                        trim_feats.setdefault(trim, []).append(text)
    return model_rows, trim_rows, trim_feats


ADAPTER = KiaAdapter()
