"""
Triumph Motorcycles India - https://www.triumphmotorcycles.in  (robots.txt: Allow /, Disallow /sitecore, /configure?*)

Endpoints used:
  GET /sitemap.xml                                  family pages /motorcycles/<range>/<family>/models
  GET /motorcycles/<range>/<family>/models          product cards: title, "Price From Rs x", detail link, CGI image on
                                                    Triumph's media host (media.triumphmotorcycles.co.uk, Cloudinary;
                                                    the 1920-px CGI is requested at w_1200 instead of the card's w_243)
  GET /motorcycles/<range>/<family>/specification   spec table (th/td: Capacity, Power, Torque, Seat Height, ...)
Price: the cards' "Price From" figure = lowest-priced colour; the site states "All prices indicated are ex-showroom
Delhi, NCT. Prices may vary slightly depending on colour" -> stored as one variant per model, city="India (national)".
Verified 2026-10-23: Speed 400 "Price From Rs 2,35,327.00"; Speed Triple 1200 RX Limited Edition Rs 23,06,900.
Gaps: colour / state prices are not published; a family spec table with several model columns is read from its
first column only; dealer pages exist per dealer (/dealers/india/<name>) but no city search
endpoint was read; offers not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import NATIONAL, Site, clean, inr, spec_rows, table_rows
from ._geo import coords_ok, pin_state

BASE = "https://www.triumphmotorcycles.in"


def _body(path: str, name: str) -> str:
    s = (path + " " + name).lower()
    if "tiger" in s or "/adventure/" in s:
        return "Adventure"
    if any(k in s for k in ("bobber", "speedmaster", "rocket")):
        return "Cruiser"
    if "daytona" in s:
        return "Sports"
    return "Street"


class TriumphAdapter(BrandAdapter):
    brand = "Triumph Motorcycles"
    slug = "triumph"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._cards = None

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _load(self):
        if self._cards is not None:
            return self._cards
        sm = self.s.text("/sitemap.xml")
        fams = list(dict.fromkeys(re.findall(r"<loc>https://www\.triumphmotorcycles\.in(/motorcycles/[a-z0-9\-/]+)/models</loc>", sm)))
        out, seen = [], set()
        for fam in fams:
            r = self.s.get(fam + "/models", ok=(200, 404))
            if r.status_code != 200:
                continue
            for card in r.text.split('class="product-card block')[1:]:
                card = card[:5000]
                title = re.search(r'class="product-card__title">(.*?)</p>', card, re.S)
                price = re.search(r"Price From\s*₹\s*([\d,]+)", card)
                img = re.search(r'src="(https://media\.triumphmotorcycles\.co\.uk/image/upload/[^"]+)"', card)
                link = re.search(r'href="(https://www\.triumphmotorcycles\.in/motorcycles/[^"]+)"', card)
                if not (title and price):
                    continue
                name = clean(title.group(1)).title().replace("Rs", "RS").replace("Rx", "RX").replace("Xc", "XC")
                if name in seen:
                    continue
                seen.add(name)
                image = None
                if img:
                    image = re.sub(r"w_\d+,c_scale", "w_1200,c_scale", img.group(1).replace("&amp;", "&"))
                    image = re.sub(r"[?&]mw=\d+", "", image)
                out.append({"name": name, "price": inr(price.group(1)), "image": image, "family": fam,
                            "url": link.group(1) if link else BASE + fam + "/models", "body": _body(fam, name)})
        self._cards = out
        return out

    def models(self) -> list[dict]:
        return [{"name": c["name"], "url": c["url"], "body_type": c["body"], "image_url": c["image"]} for c in self._load()]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = [Variant(model=c["name"], variant=c["name"], fuel="Petrol", transmission="Manual", ex_showroom_inr=c["price"],
                       city=NATIONAL, source_url=BASE + c["family"] + "/models", body_type=c["body"], model_url=c["url"],
                       image_url=c["image"]) for c in self._load() if c["price"]]
        if not out:
            raise NotSupported("Triumph model cards show no price")
        return out

    def specs(self):
        specs, feats, done = [], [], {}
        for c in self._load():
            fam = c["family"]
            if fam not in done:
                r = self.s.get(fam + "/specification", ok=(200, 404))
                done[fam] = table_rows(r.text) if r.status_code == 200 else []
            s, f = spec_rows(c["name"], c["name"], done[fam], BASE + fam + "/specification", "Petrol", "Manual")
            specs += s
            feats += f
        return specs, feats

    def dealers(self, city: str = "Hyderabad"):
        c = city.lower()
        alias = {"bengaluru": "bangalore", "gurugram": "gurgaon", "mysuru": "mysore", "vadodara": "baroda"}.get(c, c)
        return [d for d in self.all_dealers() if d.city.lower() in (c, alias)]

    def all_dealers(self):
        """triumphmotorcycles.in lists every Indian dealer in its sitemap (/dealers/india/<name>); each page has the
        name, the address block (lines, city, state, PIN), phone and a Google Maps directions link with lat,lng."""
        if getattr(self, "_dealer_cache", None) is not None:
            return self._dealer_cache
        from bs4 import BeautifulSoup
        from ..base import Dealer
        urls = sorted(set(re.findall(r"<loc>(https://www\.triumphmotorcycles\.in/dealers/india/[^<]+)</loc>", self.s.text("/sitemap.xml"))))
        out = []
        for u in urls:
            try:
                soup = BeautifulSoup(self.s.text(u), "html.parser")
            except Exception:
                continue
            title = soup.select_one(".dealer-header__title")
            loc = soup.select_one(".dealer-location")
            if not title or not loc:
                continue
            lines = [clean(x) for x in loc.get_text("\n", strip=True).split("\n") if clean(x)]
            pin_i = next((i for i, x in enumerate(lines) if re.fullmatch(r"\d{6}", x)), None)
            if pin_i is None or pin_i < 3:
                continue
            name = clean(title.get_text())
            start = next((i + 1 for i, x in enumerate(lines[:pin_i]) if x.upper() == name.upper()), 0)
            street = ", ".join(lines[start:pin_i - 2])
            tel = soup.select_one('a[href^="tel:"]')
            m = re.search(r"destination=(-?\d+\.\d+),(-?\d+\.\d+)", str(soup))
            pin = lines[pin_i]
            state = pin_state(pin) or lines[pin_i - 1]
            # the block ends "... city, [state,] PIN" but the state line is sometimes missing
            city = lines[pin_i - 2] if lines[pin_i - 1].lower() == state.lower() else lines[pin_i - 1]
            street = ", ".join(x for x in lines[start:pin_i] if x not in (city, lines[pin_i - 1]) or x == street)
            lat, lng = (float(m.group(1)), float(m.group(2))) if m else (None, None)
            if not coords_ok(pin, lat, lng):
                lat = lng = None                       # pin dropped in the wrong state on the brand's page
            out.append(Dealer(name=name.title(), address=street, city=city, state=state, pincode=pin,
                              phone=tel["href"][4:] if tel else None, email=None, lat=lat, lng=lng,
                              kind="sales+service", source_url=u))
        self._dealer_cache = out
        return out

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = TriumphAdapter()
