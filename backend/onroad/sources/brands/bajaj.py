"""
Bajaj Auto - https://www.bajajauto.com  (robots.txt disallows /api/*, /handlers/* and a few asset paths; not used)

Endpoints used:
  GET /bikes/pulsar/pulsar-150   any model page embeds the site's ex-showroom price table as
        `arrShowRoomPriceJsonNew = {"<State>": {"<City>": {"<model code>": {"model_name": ..., "price": ...}}}}`
        (the data behind the page's state/city price selector). Read once; every city's list is in it.
        The same page's model cards (div.listingBoxSec) give each model's page link, displacement and
        navigation image on cdn.bajajauto.com.

City: prices are per city (Hyderabad = data["Telangana"]["Hyderabad"]).
Verified 2026-10-22 (Hyderabad): "pulsar 150 sd ug" Rs 1,15,616 and "dominar d 400 ug2" Rs 2,32,656 (34 Hyderabad
rows). The model page itself shows the Delhi figure (Pulsar 150 Rs 1,28,650) for a different model code.
Gaps: variant names are Bajaj's internal price-list names (e.g. "pulsar n160 td"); colours are not priced
separately; Chetak electric scooters are sold via chetak.com (not read); Freedom 125 is a CNG/petrol bike (fuel
"CNG"); the dealer locator's search script (fnSearchDealers) is not present in the page -> dealers NotSupported;
offers not read; specs not read.
"""

from __future__ import annotations

import json
import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import Site, inr, norm, trans_2w
from ._geo import geo

BASE = "https://www.bajajauto.com"
PRICE_PAGE = "/bikes/pulsar/pulsar-150"

_RULES = [  # internal price-list name -> model
    (r"^pulsar\s*ns\s*400", "Pulsar NS400Z"), (r"^pulsar\s*ns\s*(\d{3})", r"Pulsar NS\1"),
    (r"^pulsar\s*n\s*(\d{3})", r"Pulsar N\1"), (r"^pulsar\s*rs\s*200", "Pulsar RS200"),
    (r"^pulsar\s*220", "Pulsar 220F"), (r"^pulsar\s*(\d{3})", r"Pulsar \1"),
    (r"^avenger\s*(\d{3})\s*(street|cruise)", lambda m: f"Avenger {m.group(2).title()} {m.group(1)}"),
    (r"^dominar\s*d?\s*(\d{3})", r"Dominar \1"), (r"^freedom\s*125", "Freedom 125"),
    (r"^platina\s*(?:99|100)", "Platina 100"), (r"^platina\s*110", "Platina 110"), (r"^ct\s*110\s*x", "CT 110X"),
    (r"^ct\s*(\d{3})", r"CT \1"),
]


def _model(name: str) -> str | None:
    n = name.lower().strip()
    for pat, rep in _RULES:
        m = re.search(pat, n)
        if m:
            return rep(m) if callable(rep) else m.expand(rep)
    return None


def _body(model: str) -> str:
    m = model.lower()
    if "avenger" in m:
        return "Cruiser"
    if "rs200" in m or "220f" in m:
        return "Sports"
    if "dominar" in m:
        return "Street"           # Bajaj calls the Dominar a sports tourer; listed with the street bikes
    if re.search(r"pulsar (n|ns)\d", m) or "pulsar 150" in m or "pulsar 180" in m:
        return "Street"
    return "Commuter"


def _card_key(model: str) -> str:
    """Order-insensitive key so the card 'Avenger 220 Cruise' matches the model 'Avenger Cruise 220'."""
    n = re.sub(r"\b(bajaj|ng04|drum|led|disc)\b", " ", model.lower()).replace("ns400z", "ns400").replace("220f", "220")
    n = re.sub(r"\b(pulsar)\s+(ns|n|rs)\s*(\d)", r"\1 \2\3", n)
    return "".join(sorted(re.findall(r"[a-z]+\d*|\d+", n)))


class BajajAdapter(BrandAdapter):
    brand = "Bajaj Auto"
    slug = "bajaj"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._page = None

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _get_page(self) -> str:
        if self._page is None:
            self._page = self.s.text(PRICE_PAGE)
        return self._page

    def _cards(self) -> dict:
        out = {}
        for b in self._get_page().split('class="listingBoxSec"')[1:]:
            b = b[:6000]
            n = re.search(r'data-model-name="([^"]+)"', b)
            if not n:
                continue
            h = re.search(r'href="(/bikes/[^"]+)" target="" class="explore', b)
            ims = [i for i in re.findall(r'src="(https://cdn\.bajajauto\.com/[^"]+\.(?:webp|png|jpe?g))"', b) if "logo" not in i.lower()]
            nav = [i for i in ims if "navigat" in i] or ims
            cc = re.search(r"(\d{2,3}(?:\.\d+)?)\s*cc", b)
            k = _card_key(n.group(1))
            out.setdefault(k, {"url": BASE + h.group(1) if h else None, "image_url": nav[0] if nav else None,
                               "engine_cc": int(round(float(cc.group(1)))) if cc else None})
        return out

    def _table(self) -> dict:
        page = self._get_page()
        i = page.find("arrShowRoomPriceJsonNew = ")
        if i < 0:
            raise NotSupported("Bajaj price table (arrShowRoomPriceJsonNew) not found on the model page")
        data, _ = json.JSONDecoder().raw_decode(page[i + len("arrShowRoomPriceJsonNew = "):])
        return data

    def models(self) -> list[dict]:
        cards = self._cards()
        names = {}
        for state in self._table().values():
            for rows in state.values():
                for r in rows.values():
                    m = _model(r.get("model_name", ""))
                    if m:
                        names[m] = True
        out = []
        for m in names:
            c = cards.get(_card_key(m), {})
            out.append({"name": m, "url": c.get("url"), "body_type": _body(m), "image_url": c.get("image_url")})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        table = self._table()
        state = next((s for s in table if g and s.lower() == g[0].lower()), None)
        rows = None
        if state:
            rows = next((v for c, v in table[state].items() if c.lower() == city.lower()), None)
        if not rows:
            raise NotSupported(f"Bajaj publishes no ex-showroom list for {city!r}")
        cards = self._cards()
        out = []
        for code, r in rows.items():
            name = (r.get("model_name") or "").strip()
            model = _model(name)
            price = inr(r.get("price"))
            if not model or not price:
                continue
            c = cards.get(_card_key(model), {})
            body = _body(model)
            fuel = "CNG" if model.startswith("Freedom") else "Petrol"
            out.append(Variant(model=model, variant=name.title(), fuel=fuel, transmission=trans_2w(body, fuel),
                               ex_showroom_inr=price, city=city, source_url=BASE + PRICE_PAGE, body_type=body,
                               engine_cc=c.get("engine_cc"), model_url=c.get("url"), image_url=c.get("image_url")))
        return out

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("Bajaj /customer-service/locate-a-dealer calls fnSearchDealers(), which is not shipped in the page; no dealer data readable")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter (state campaign pages such as /offer-maharashtra)")


ADAPTER = BajajAdapter()
