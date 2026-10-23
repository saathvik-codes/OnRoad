"""
Land Rover India adapter (JLR India: Range Rover, Defender, Discovery). Plain httpx; robots.txt of landrover.in,
rangerover.com and findmeasuv.in allow these paths.

Endpoints used:
  - https://www.landrover.in/index.html           -> link "VIEW PRICES" to the official price-list PDF (discovered live)
  - https://www.findmeasuv.in/pricing_pdf/land-rover-vehicles-price-in-india.pdf
        JLR India's own "Vehicles price list" PDF (linked from landrover.in / rangerover.com/en-in as VIEW PRICES;
        findmeasuv.in is JLR India's online-booking site). Read with pypdf (layout mode).
  - https://www.rangerover.com/en-in/index.html   -> model cards (name, image, "Price from")
  - https://www.landrover.in/defender/index.html, /discovery/index.html -> og:image for Defender / Discovery
  - https://retailerlocator.jaguarlandrover.com/dealers?...&brand=Land%20Rover&requestMarketLocale=en_in&country=in
        the JSON API behind landrover.in/national-dealer-locator.html (retailerlocatorv2 component, data-url attr).
        Without lat/lng it returns every Indian outlet; we filter on address.town.
Verified 2026-10-19/20: PDF "Prices are effective from 1st July 2026", 3 pages, 7 models / 41 variant rows (Range Rover 3,
Range Rover Sport 7, Velar 5, Evoque 2, Defender 16, Discovery Sport 2, Discovery 6), all checked row-by-row against
pypdf's text of the PDF on 2026-10-20. Spot checks: Range Rover 4.4 l Petrol LWB SV
= 350.00 lakh, Defender 2.0 Si4 (110) X-Dynamic HSE = 107.00 lakh (= "Price from ₹ 10 700 000" on the Defender page),
Range Rover Evoque 64.86 lakh (= "Price from ₹ 6 486 000" on rangerover.com/en-in), Discovery Sport 63.37 lakh
(= "Price from ₹ 6 337 000" on the Discovery page). Hyderabad: Pride Motors (sales x2 incl. one sales+service, 1 service).
Price semantics: one national ex-showroom list in ₹ lakh (we convert to rupees: lakh * 100000); city="India".
The PDF says prices exclude 1% TCS. Model labels in the PDF are vertically centred against their variant rows, so the
parser assigns rows to labels by the closest-centre contiguous split (checked against page order).
Gaps: no retail offers page (offers-and-finance/retail-offers redirects to the home page) -> NotSupported;
engine_cc not given (only "3.0 l"), all automatic.
"""

from __future__ import annotations

import io
import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, city_match, clean

HOME = "https://www.landrover.in/index.html"
PDF_FALLBACK = "https://www.findmeasuv.in/pricing_pdf/land-rover-vehicles-price-in-india.pdf"
RR_URL = "https://www.rangerover.com/en-in/index.html"
PAGES = {"Defender": "https://www.landrover.in/defender/index.html",
         "Discovery": "https://www.landrover.in/discovery/index.html"}
LOCATOR = "https://retailerlocator.jaguarlandrover.com/dealers"
OFFERS_URL = "https://www.landrover.in/offers-and-finance/retail-offers.html"

_PRICE = re.compile(r"(\d{1,3}\.\d{2})\s*$")
_LABEL = re.compile(r"^(?P<model>[A-Z][A-Za-z ]+?)\s*(?P<local>\*\*)?\s*\((?P<my>[\d.]+MY)\)")


def _group(rows: list[int], labels: list[int]) -> list[int]:
    """Assign each row (by line index) to a label so that groups are contiguous and each label sits closest to the
    centre of its group (labels are vertically centred in the PDF). Returns label index per row."""
    R, L = len(rows), len(labels)
    INF = float("inf")
    dp = [[INF] * (R + 1) for _ in range(L + 1)]
    back = [[0] * (R + 1) for _ in range(L + 1)]
    dp[0][0] = 0.0
    for i in range(1, L + 1):
        for j in range(i, R + 1):
            for k in range(i - 1, j):
                if dp[i - 1][k] == INF:
                    continue
                centre = sum(rows[k:j]) / (j - k)
                c = dp[i - 1][k] + abs(centre - labels[i - 1])
                if c < dp[i][j]:
                    dp[i][j], back[i][j] = c, k
    if dp[L][R] == INF:
        raise RuntimeError("Land Rover PDF: could not match variant rows to model labels")
    out, j = [0] * R, R
    for i in range(L, 0, -1):
        k = back[i][j]
        for r in range(k, j):
            out[r] = i - 1
        j = k
    return out


def _fuel(v: str) -> str:
    if re.search(r"diesel|\d\.\dD\b", v, re.I):
        return "Diesel"
    if re.search(r"electric|\bEV\b", v, re.I):
        return "Electric"
    if re.search(r"PHEV|plug-in", v, re.I):
        return "Hybrid"
    return "Petrol"                        # "Petrol", "V8", "Si4", "P400"...


class LandRoverAdapter(BrandAdapter):
    brand = "Land Rover"
    slug = "land_rover"
    website = "https://www.landrover.in"

    def _pdf_url(self, p: Polite) -> str:
        home = p.text(HOME)
        m = re.search(r'href="(https://[^"]+pricing_pdf/[^"?]+\.pdf)', home)
        return m.group(1) if m else PDF_FALLBACK

    def _rows(self) -> tuple[str, str, list[dict]]:
        from pypdf import PdfReader
        with Polite() as p:
            url = self._pdf_url(p)
            data = p.get(url).content
        reader = PdfReader(io.BytesIO(data))
        eff = ""
        rows_out = []
        for page in reader.pages:
            text = page.extract_text(extraction_mode="layout")
            m = re.search(r"effective from\s+([^\n]+?)\s+and", text)
            eff = eff or (clean(m.group(1)) if m else "")
            rows, labels = [], []
            for idx, line in enumerate(text.splitlines()):
                s = line.strip()
                if not s or s.startswith(("*", "Model", "Visit", "Prices", "Ex-Showroom", "The on-road")):
                    continue
                chunks = re.split(r"\s{2,}", s)
                lab = _LABEL.match(chunks[0])
                if lab:
                    labels.append((idx, lab))
                pm = _PRICE.search(s)
                if pm:
                    body = s[:pm.start()].rstrip()
                    parts = re.split(r"\s{2,}", body)
                    var = parts[-1] if parts else ""
                    if lab and len(parts) == 1:          # label and variant glued: "Range Rover (26MY) 4.4 l ..."
                        var = body[lab.end():].strip()
                    var = clean(var)
                    if var and not _LABEL.match(var):
                        rows.append((idx, var, float(pm.group(1))))
            if not rows:
                continue
            which = _group([r[0] for r in rows], [lb[0] for lb in labels])
            for (idx, var, lakh), li in zip(rows, which):
                lab = labels[li][1]
                rows_out.append({"model": clean(lab.group("model")), "my": lab.group("my"),
                                 "local": bool(lab.group("local")), "variant": var,
                                 "inr": int(round(lakh * 100000))})
        if not rows_out:
            raise RuntimeError("Land Rover price PDF parsed to zero rows")
        return url, eff, rows_out

    def _cards(self) -> dict[str, dict]:
        """model name (upper) -> {url, image} from the brand's own pages."""
        out = {}
        with Polite() as p:
            rr = p.text(RR_URL)
            for block in re.split(r'class="cmp-ContentCard display-block"', rr)[1:]:
                h = re.search(r'cmp-ContentCard__heading[^>]*>(.*?)</h2>', block, re.S)
                img = re.search(r'<img[^>]+src="(https://jlr\.scene7\.com[^"]+)"', block)
                href = re.search(r'data-href="([^"]+)"', block)
                if h:
                    out[clean(h.group(1)).upper()] = {"image": img.group(1) if img else None,
                                                      "url": "https://www.rangerover.com" + href.group(1) if href else RR_URL}
            for name, url in PAGES.items():
                page = p.text(url)
                og = re.search(r'<meta property="og:image" content="([^"]+)"', page)
                out[name.upper()] = {"image": og.group(1) if og else None, "url": url}
        return out

    def models(self) -> list[dict]:
        _, _, rows = self._rows()
        cards = self._cards()
        seen, out = set(), []
        for r in rows:
            if r["model"] in seen:
                continue
            seen.add(r["model"])
            c = cards.get(r["model"].upper()) or cards.get(r["model"].split()[0].upper()) or {}
            out.append({"name": r["model"], "url": c.get("url"), "body_type": "SUV", "image_url": c.get("image")})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        url, eff, rows = self._rows()
        out = []
        for r in rows:
            out.append(Variant(model=r["model"], variant=f'{r["variant"]} ({r["my"]}{", locally manufactured" if r["local"] else ""})',
                               fuel=_fuel(r["variant"]), transmission="Automatic", ex_showroom_inr=r["inr"],
                               city="India", source_url=url, body_type="SUV"))
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        params = {"requestMarketLocale": "en_in", "brand": "Land Rover", "filter": "All", "radius": "100",
                  "unitOfMeasure": "Kilometres", "country": "in", "fetchOpeningTimes": "false"}
        with Polite(extra_headers={"Accept": "application/json"}) as p:
            data = p.json(LOCATOR, params=params)
        out = []
        for d in data.get("dealers", []):
            a = d.get("address") or {}
            if not city_match(city, a.get("town"), a.get("line2"), a.get("line3")):
                continue
            sales, service = bool(d.get("dealer")), bool(d.get("authorisedRepairer"))
            kind = "sales+service" if sales and service else ("sales" if sales else "service")
            svc = {s.get("type"): s for s in d.get("services") or []}
            first = svc.get("sales") or svc.get("repair") or {}
            out.append(Dealer(name=clean(d.get("name")).title(),
                              address=", ".join(x for x in (a.get("line1"), a.get("line2"), a.get("line3"), a.get("town"), a.get("postCode")) if x),
                              city=a.get("town") or city, state=a.get("county") or "", pincode=a.get("postCode"),
                              phone=first.get("phone") or None, email=first.get("email") or None,
                              lat=d.get("latitude"), lng=d.get("longitude"), kind=kind,
                              source_url="https://www.landrover.in/national-dealer-locator.html", website=d.get("homePage")))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        with Polite() as p:
            r = p.c.get(OFFERS_URL)
        if r.status_code != 200 or str(r.url).rstrip("/").endswith(("index.html", "landrover.in")):
            raise NotSupported("Land Rover India publishes no retail offers: /offers-and-finance/retail-offers.html "
                               f"redirects to {r.url} (status {r.status_code})")
        raise NotSupported(f"Land Rover offers page now exists at {r.url}; parser not implemented - re-verify")


ADAPTER = LandRoverAdapter()
