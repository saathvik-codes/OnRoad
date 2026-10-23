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
        raise NotSupported("Triumph dealer search not read by this adapter")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = TriumphAdapter()
