"""
Lexus India adapter (Toyota Kirloskar Motor's Lexus India site, WordPress, server-rendered HTML).

Endpoints used (all on https://www.lexusindia.co.in, robots.txt allows everything):
  - /price-and-model-tools/price-list/   models (tabs SUV/SEDAN/MPV), every published variant with "From INR x", images
  - /contact-us/find-a-dealer/           all dealer cards (data-location=<city slug>) with address, phone, e-mail, map link
Verified 2026-10-19/20 by running the adapter and comparing with the pages:
  - price list: 7 models / 14 variants incl. the footnoted RX 350h Exquisite (Mark Levinson) at INR 93,87,000; NX 350h Exquisite
    INR 67,93,000 and LM 350h 7-Seater VIP INR 2,27,38,000 match the "From INR" figures on the model pages / home page.
  - Hyderabad: "Lexus Hyderabad" (Jubilee Hills, guest experience centre) + "Lexus Service Point Hyderabad" (Kothaguda).
Price semantics: Lexus publishes ONE national list, "From INR ..." per variant, without naming a city and without the
words "ex-showroom" (the page's state selector only feeds the enquiry form). We return it with city="India" - treat
it as the national ex-showroom starting price. Hyderabad-specific ex-showroom prices are not published.
Gaps: no offers page on the site (offers() -> NotSupported); body type from the price-list tab (MPV -> MUV);
transmission is not stated per variant (all Lexus India cars are automatic; we put "Automatic").
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, city_match, clean, inr

BASE = "https://www.lexusindia.co.in"
PRICE_URL = BASE + "/price-and-model-tools/price-list/"
DEALER_URL = BASE + "/contact-us/find-a-dealer/"
BODY = {"SUV": "SUV", "SEDAN": "Sedan", "MPV": "MUV", "HATCHBACK": "Hatchback", "COUPE": "Coupe"}


def _fuel(name: str, tag: str) -> str:
    s = f"{name} {tag}".lower()
    if "diesel" in s:
        return "Diesel"
    if "hybrid" in s or re.search(r"\b\d{3}h\b", s):
        return "Strong Hybrid"
    if "electric" in s or re.search(r"\b\d{3}e\b", s):
        return "Electric"
    return "Petrol"


class LexusAdapter(BrandAdapter):
    brand = "Lexus"
    slug = "lexus"
    website = BASE

    def _price_page(self) -> list[dict]:
        with Polite() as p:
            page = p.text(PRICE_URL)
        sec = page[page.find("sec__price_list "):]
        tabs = [clean(t).upper() for t in re.findall(r'class="mdc-tab__text-label">(.*?)</span>', sec)]
        panels = re.split(r'<div class="tab__panel_main', sec)[1:]
        out = []
        for i, panel in enumerate(panels):
            body = BODY.get(tabs[i] if i < len(tabs) else "", None)
            for block in re.split(r'<div class="price_list_img">', panel)[1:]:
                img = re.search(r'data-src="([^"]+)"\s+alt="([^"]+)"', block)
                url = re.search(r'<a href="(https://www\.lexusindia\.co\.in/models/[^"]+)"', block)
                model = clean(img.group(2)) if img else clean(re.search(r"<h3>(.*?)</h3>", block).group(1))
                rows = []
                for li in re.findall(r'<div class="price_list_model_class">(.*?)</div>\s*<div class="price_list_pricing">(.*?)</div>',
                                     block, re.S):
                    name_html, price_html = li
                    name_html = re.sub(r"<!--.*?-->", "", name_html, flags=re.S)
                    em = re.search(r"<em>(.*?)</em>", name_html, re.S)
                    tag = clean(em.group(1)) if em else ""
                    name = clean(re.sub(r"<em>.*?</em>", "", name_html, flags=re.S))
                    if tag and not re.search(r"hybrid|electric|diesel|petrol|performance", tag, re.I):
                        name = f"{name} {tag}"          # ES rows put the trim in <em>
                    rows.append((name, tag, inr(clean(price_html))))
                # footnotes such as "RX350h Exquisite (with Mark Levinson audio) is priced at INR 93,87,000"
                for fn in re.findall(r"<small>(.*?)</small>", block, re.S):
                    for m in re.finditer(r"([A-Z]{2}\s?\d{3}[a-z]?\s+[A-Za-z ]+?)\s*\((with [^)]+)\)\s*is priced at INR\s*([\d,]+)", clean(fn)):
                        base_name = re.sub(r"^([A-Z]{2})\s?(\d)", r"\1 \2", m.group(1).strip())
                        rows.append((f"{base_name} ({m.group(2)})", "", inr(m.group(3))))
                out.append({"model": model, "body": body, "image": img.group(1) if img else None,
                            "url": url.group(1) if url else PRICE_URL, "rows": rows})
        if not out:
            raise RuntimeError("Lexus price list layout changed: no models parsed")
        return out

    def models(self) -> list[dict]:
        return [{"name": m["model"], "url": m["url"], "body_type": m["body"], "image_url": m["image"]}
                for m in self._price_page()]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = []
        for m in self._price_page():
            for name, tag, price in m["rows"]:
                if not price:
                    continue
                out.append(Variant(model=m["model"], variant=name, fuel=_fuel(name, tag), transmission="Automatic",
                                   ex_showroom_inr=price, city="India", source_url=PRICE_URL, body_type=m["body"],
                                   model_url=m["url"], image_url=m["image"]))
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite() as p:
            page = p.text(DEALER_URL)
        page = re.sub(r"<svg.*?</svg>|<!--.*?-->", "", page, flags=re.S)
        out = []
        for loc, card in re.findall(r'<div\s+class="dealer_card"\s+data-location="([^"]*)">(.*?)(?=<div\s+class="dealer_card"\s+data-location=|</section>)',
                                    page, re.S):
            label = clean((re.search(r'dealer_card--label">(.*?)</div>', card, re.S) or [None, ""])[1])
            name = clean((re.search(r"<h4>(.*?)</h4>", card, re.S) or [None, ""])[1])
            addr = clean((re.search(r'dealer_card_info_each--text">\s*<p>(.*?)</p>', card, re.S) or [None, ""])[1])
            if not city_match(city, loc.replace("-", " "), name.replace("Lexus", ""), addr):
                continue
            tel = re.search(r'href="tel:([^"]+)"', card)
            mail = re.search(r'href="mailto:([^"]+)"', card)
            geo = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", card) or re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", card)
            pin = re.search(r"\b(\d{6})\b", addr)
            state = re.search(r",\s*([A-Za-z ]+?)\s*-?\s*\d{6}", addr)
            kind = "service" if "SERVICE" in label.upper() or "service" in name.lower() else "sales"
            out.append(Dealer(name=name, address=addr, city=city, state=state.group(1).strip() if state else "",
                              pincode=pin.group(1) if pin else None, phone=tel.group(1) if tel and "@" not in tel.group(1) else None,
                              email=mail.group(1).strip() if mail else None,
                              lat=float(geo.group(1)) if geo else None, lng=float(geo.group(2)) if geo else None,
                              kind=kind, source_url=DEALER_URL, website=f"{BASE}/dealers/{loc}"))
        # each card appears once per layout; de-duplicate on name+address
        seen, uniq = set(), []
        for d in out:
            k = (d.name, d.address)
            if k not in seen:
                seen.add(k)
                uniq.append(d)
        return uniq

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Lexus India publishes no offers/finance-scheme page (only a payment estimator and "
                           "lexusfinance.co.in leasing info without amounts)")


ADAPTER = LexusAdapter()
