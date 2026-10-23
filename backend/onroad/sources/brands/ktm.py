"""
KTM India (Bajaj Auto) - https://www.ktmindia.com  (robots.txt: Allow /*, Disallow /pulsarfont/*, /app_data/*)

Endpoints used (the XHRs of the site's own /on-road-price page, scripts/KTM/ORP/orp.js):
  GET /api/getOrpModelList/PB                      {"<category>": [{ModelName, ModelCode, DefaultColorCode, ItemId}]}
  GET /api/getOrpDetails/PB/<ModelCode>            states the model is priced in (StateCode, e.g. Telangana = TG)
  GET /api/getOrpByModelCode?modelCode=<ModelCode><DefaultColorCode>&StateCode=<code>
                                                   price breakup; "ESRP" (DisplayName "Ex Price") = ex-showroom
  GET /sitemap.xml -> /ktm-bikes/<category>/<model> pages: JSON-LD Product images on cdn.bajajauto.com (the
      "/orp/" side-view cut-out, ~750 px, else the first product render), and /<model>/specifications tables
      (Engine Displacement, Power, Torque, Fuel Tank, Kerb Weight, Rider Aids, ...) for specs().
City: prices are per state (Hyderabad -> TG); one price per model at its default colour.
Verified 2026-10-23 (Telangana): KTM 250 Adventure ESRP Rs 2,52,788 (ORP 3,45,318).
Gaps: colour-specific prices are not requested (default colour only); competition models (SX/EXC) are listed by the
API only if KTM prices them; dealers (/api/dealer/nearest-dealers needs a lead token) and offers not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import Site, cc_of, clean, inr, norm, spec_rows, table_rows, trans_2w
from ._geo import geo

BASE = "https://www.ktmindia.com"
STATE_CODE = {"Telangana": "TG", "Karnataka": "KA", "Maharashtra": "MH", "Tamil Nadu": "TN", "Delhi": "DL",
              "Andhra Pradesh": "AP", "West Bengal": "WB", "Gujarat": "GJ", "Rajasthan": "RJ", "Uttar Pradesh": "UP",
              "Kerala": "KL", "Haryana": "HR", "Madhya Pradesh": "MP", "Chandigarh": "CH", "Punjab": "PB"}


def _body(name: str, cat: str) -> str:
    n, c = name.lower(), (cat or "").lower()
    if "adventure" in n or "enduro" in n or c in ("travel", "dual sport", "enduro"):
        return "Adventure"
    if n.startswith("ktm rc") or " rc " in n or c == "supersport":
        return "Sports"
    return "Street"


class KTMAdapter(BrandAdapter):
    brand = "KTM India"
    slug = "ktm"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._list = None
        self._pages = None
        self._page_cache = {}

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE, headers={"Referer": BASE + "/on-road-price"})
        return self._s

    def _models(self):
        if self._list is None:
            data = self.s.json("/api/getOrpModelList/PB")
            self._list = [dict(x, _cat=cat) for cat, xs in data.items() if isinstance(xs, list) for x in xs
                          if (x.get("ModelName") or "").upper().startswith("KTM")]
            if not self._list:
                raise NotSupported("KTM ORP model list is empty")
        return self._list

    def _page_paths(self) -> dict:
        if self._pages is None:
            sm = self.s.text("/sitemap.xml")
            paths = re.findall(r"<loc>https://www\.ktmindia\.com(/ktm-bikes/[a-z\-]+/ktm-[a-z0-9\-]+)</loc>", sm)
            self._pages = {norm(p.rsplit("/", 1)[-1]): p for p in paths}
        return self._pages

    def _page_for(self, name: str):
        return self._page_paths().get(norm(name))

    def _image(self, path: str | None) -> str | None:
        if not path:
            return None
        if path not in self._page_cache:
            img = None
            try:
                page = self.s.text(path)
                for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
                    if '"Product"' in block:
                        ims = re.findall(r'"(https://cdn\.bajajauto\.com/[^"]+\.(?:webp|png|jpe?g))"', block)
                        img = next((i for i in ims if "/orp/" in i), ims[0] if ims else None)
                        break
            except Exception:
                pass
            self._page_cache[path] = img
        return self._page_cache[path]

    def models(self) -> list[dict]:
        out, used = [], set()
        for m in self._models():
            path = self._page_for(m["ModelName"])
            img = self._image(path)
            if img in used:
                img = None
            used.add(img)
            out.append({"name": m["ModelName"], "url": BASE + path if path else None,
                        "body_type": _body(m["ModelName"], m["_cat"]), "image_url": img})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        code = STATE_CODE.get(g[0]) if g else None
        if not code:
            raise NotSupported(f"KTM state code for {city!r} unknown")
        out = []
        for m in self._models():
            det = self.s.json(f"/api/getOrpDetails/PB/{m['ModelCode']}")
            if not any(s.get("StateCode") == code for s in det.get("States") or []):
                continue
            mc = (det.get("ModelCode") or m["ModelCode"]) + (det.get("DefaultColorCode") or m.get("DefaultColorCode") or "")
            res = self.s.json("/api/getOrpByModelCode", params={"modelCode": mc, "StateCode": code})
            resp = (((res.get("Data") or {}).get("Output") or {}).get("Response") or {})
            price = inr((resp.get("ESRP") or {}).get("Value"))
            if not price:
                continue
            body = _body(m["ModelName"], m["_cat"])
            path = self._page_for(m["ModelName"])
            out.append(Variant(model=m["ModelName"], variant=m["ModelName"], fuel="Petrol", transmission=trans_2w(body, "Petrol"),
                               ex_showroom_inr=price, city=city,
                               source_url=f"{BASE}/api/getOrpByModelCode?modelCode={mc}&StateCode={code}",
                               body_type=body, model_url=BASE + path if path else None, image_url=self._image(path)))
        if not out:
            raise NotSupported(f"KTM publishes no ex-showroom price for {g[0]}")
        return out

    def specs(self):
        specs, feats = [], []
        for m in self._models():
            path = self._page_for(m["ModelName"])
            if not path:
                continue
            try:
                page = self.s.text(path + "/specifications")
            except Exception:
                continue
            rows = table_rows(page[page.find("Parameter"):] if "Parameter" in page else page)
            s, f = spec_rows(m["ModelName"], m["ModelName"], rows, BASE + path + "/specifications", "Petrol",
                             trans_2w(_body(m["ModelName"], m["_cat"]), "Petrol"))
            specs += s
            feats += f
        return specs, feats

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("KTM nearest-dealers API is called with the lead form's verification token; not read")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = KTMAdapter()
