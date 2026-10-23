"""
Nissan Motor India - https://www.nissan.in

Endpoints used (robots.txt on www.nissan.in only blocks ?location= URLs; dealers.nissan.in allows all):
  GET  /prices-list.html          static "Ex-Showroom Price (INR)" tables per model (h2 model heading ->
                                  accordion per transmission -> rows "variant | price")
  GET  /                          vehicle nav (/vehicles/new/<model>.html) for models()
  GET  https://dealers.nissan.in/home/<state>/car-showroom-in-<city>   official dealer locator, "Sales" filter
                                  (URL pattern built by the locator's own home.js search button)
  GET  /Offers.html -> each "View Offer" page (/vehicles/new/nissan-magnite/offer.html, /tekton-offer.html, ...)
                                  Server-rendered (no offers XHR). Each page carries one HTML <table> per market
                                  (Variant x Cash/Accessories | Navratri Special [cash] | Exchange Bonus Nissan/Datsun/
                                  Renault car | Exchange Bonus other make | POI) followed by "Note: Applicable till <d>
                                  Applicable Market: ..." -> one Offer per non-zero cell (variant = row label). The
                                  market note decides the city ("Only Kerala, Hyderabad, ...", "All India Excluding ...",
                                  "Tamil Nadu & Telangana only"); a block with no own date takes the page T&C's "invoiced
                                  on or before 31st October 2026". Range-wide items (gold coin, test-drive gift,
                                  October scratch & win) come from the state's T&C paragraph ("All India:" / "Tamil
                                  Nadu:"), model=None. Linked .../offers-tnc.html is the exchange/POI documentation.
                                  /upcoming-offers.html currently says "New offers coming up soon".

City: /prices-list.html is one national list and names no city (the offer T&C says "All prices ex-showroom Delhi"),
so prices() returns city="India (national)".
Verified 2026-10-20: Magnite MT VISIA 5,69,400 and Gravite Visia MT 5,73,400 in the table; Gravite matches the
"modelPrice":"573400" in the page's own price JSON. 7 Hyderabad showrooms on the locator page.
Offers verified 2026-10-22 (pages titled "Offers - OCTOBER 2026"): Hyderabad gets the Tekton table for "Only Kerala,
Hyderabad, Chennai, Kolkata & Delhi/NCR" (T160 MT TEKNA cash/accessories INR 27,000; exchange INR 70,000 for a
Nissan/Datsun/Renault car) valid to 2026-10-31. The Gravite (Telangana table) and Magnite (amounts only inside images)
blocks say "Applicable till 15th Oct'26", so they are dropped as expired; Nissan has published no newer month/festive
page yet.
Known gaps: the CNG pack is an add-on table (not a variant) and is not emitted; X-Trail is listed on the site but has
no price in the list (price placeholder "1"); Magnite offer amounts are images only (emitted with amount None when in
date); dealer lat/lng and e-mail are not on the locator cards; engine cc/seats not in the price list.
"""

from __future__ import annotations

import datetime as dt
import html as _html
import re
import time

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from . import _offers as _o
from ._geo import geo

BASE = "https://www.nissan.in"
DEALERS = "https://dealers.nissan.in"
DELAY = 0.7
NATIONAL = "India (national)"
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _t(s: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _trans(group: str, name: str) -> str:
    s = f"{group} {name}".upper()
    if "CVT" in s:
        return "CVT"
    if "DCT" in s or "DUAL CLUTCH" in s:
        return "DCT"
    if "AMT" in s or "EZ SHIFT" in s or "EZ-SHIFT" in s or "AUTOMATED MANUAL" in s:
        return "AMT"
    return "Manual"


class NissanAdapter(BrandAdapter):
    brand = "Nissan"
    slug = "nissan"
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

    NISSAN_IMAGES = {
        "magnite": "https://www-asia.nissan-cdn.net/content/dam/Nissan/in/vehicles/new-magnite/TEKNA%2B_VLP_V1.png",
        "x-trail": "https://www-asia.nissan-cdn.net/content/dam/Nissan/in/vehicles/x-trail/overview/Nissan%20X-TRAIL%20Side%20Angle.png",
        "gravite": "https://www-asia.nissan-cdn.net/content/dam/Nissan/in/vehicles/new-magnite/ACENTA_VLP_V1.png",
        "tekton": "https://www-asia.nissan-cdn.net/content/dam/Nissan/in/vehicles/new-magnite/Images/TEKNA_VLP_V1_2.png",
        "kuro": "https://www-asia.nissan-cdn.net/content/dam/Nissan/in/vehicles/new-magnite/N_CONNECTA_Black_V1_2.png",
    }

    def models(self) -> list[dict]:
        page = self._get("/").text
        out, seen = [], set()
        for path in re.findall(r'href="(/vehicles/new/[a-z0-9\-]+\.html)"', page):
            if path in seen:
                continue
            seen.add(path)
            slug = path.rsplit("/", 1)[-1][:-5].replace("nissan-", "")
            img = next((v for k, v in self.NISSAN_IMAGES.items() if k in slug), None)
            out.append({"name": slug.replace("-", " ").title(), "url": BASE + path,
                        "body_type": "SUV", "image_url": img})
        tek = re.search(r'href="(https://www\.nissan\.in/cf/vehicles/new/tekton)"', page)
        if tek and not any("tekton" in m["url"] for m in out):
            out.append({"name": "Tekton", "url": tek.group(1), "body_type": "SUV", "image_url": self.NISSAN_IMAGES.get("tekton")})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        page = self._get("/prices-list.html").text
        start = page.find('class="c_154 accordion"')
        page = page[max(0, page.rfind("<h2", 0, start)):] if start > 0 else page
        tokens = re.finditer(r'<h2 class="heading">\s*<span>(.*?)</span>|<h2 class="accordion-title">\s*<span>(.*?)</span>'
                             r'|<tr>(.*?)</tr>', page, re.S)
        model, group, out = None, "", []
        for m in tokens:
            if m.group(1) is not None:
                if _t(m.group(1)):
                    model, group = _t(m.group(1)), ""
            elif m.group(2) is not None:
                group = _t(m.group(2))
            elif model:
                cells = [_t(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", m.group(3), re.S)]
                if len(cells) != 2 or not re.fullmatch(r"[\d,]{5,}", cells[1]) or "CNG" in group.upper():
                    continue
                name = cells[0]
                out.append(Variant(model=model, variant=name, fuel="Petrol", transmission=_trans(group, name),
                                   ex_showroom_inr=int(cells[1].replace(",", "")), city=NATIONAL,
                                   source_url=f"{BASE}/prices-list.html"))
        if not out:
            raise NotSupported("Nissan /prices-list.html table layout changed")
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown (add to _geo.CITY_GEO)")
        state = g[0]
        url = f"{DEALERS}/home/{state.lower().replace(' ', '-')}/car-showroom-in-{city.lower().replace(' ', '-')}"
        page = self._get(url).text
        out = []
        for card in page.split('class="itemdealer-inr"')[1:]:
            name = re.search(r'store-name">\s*<a href="([^"]+)">(.*?)</a>', card, re.S)
            addr = re.search(r'locationicon\.png"></span>(.*?)</div>', card, re.S)
            phone = re.search(r'href="tel:([^"]+)"', card)
            if not name:
                continue
            label = _t(name.group(2))
            a = _t(addr.group(1)) if addr else ""
            a = re.sub(r"\s*,\s*", ", ", a)
            pin = re.search(r"(\d{6})\s*$", a)
            out.append(Dealer(name=label, address=re.sub(r"\s*-\s*\d{6}\s*$", "", a), city=city, state=state,
                              pincode=pin.group(1) if pin else None, phone=phone.group(1) if phone else None, email=None,
                              lat=None, lng=None, kind="sales+service" if "Workshop" in label else "sales",
                              source_url=url, website=name.group(1)))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        g = geo(city)
        state = g[0] if g else None
        page = self._get("/Offers.html").text
        links = []
        for m in re.finditer(r"View Offer", page):
            hrefs = re.findall(r'href="([^"]+)"', page[max(0, m.start() - 600):m.start()])
            if hrefs and hrefs[-1] not in links:
                links.append(hrefs[-1])
        if not links:
            raise NotSupported("nissan.in/Offers.html links no 'View Offer' pages")
        out, seen_brand = [], set()
        for path in links:
            raw = self._get(path).text
            body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
            txt = _t(body)
            hm = re.search(r"New Nissan ([A-Za-z\- ]+?) Offer\s*[–-]\s*([A-Za-z]+ 20\d\d)", txt)
            model = hm.group(1).strip() if hm else path
            url = BASE + path
            tnc = _nissan_tnc(txt, state)
            tnc_until = None
            im = re.search(r"invoiced on or before (\d+\w*\s+[A-Za-z]+\s+20\d\d)", tnc or "")
            if im:
                tnc_until = _o.date_text(im.group(1))
            tl = re.search(r'href="([^"]*offers-tnc\.html)"', raw)
            tnc_url = (BASE + tl.group(1)) if tl and tl.group(1).startswith("/") else url
            tables = list(re.finditer(r"<table.*?</table>", body, re.S))
            if tables:
                for k, tm in enumerate(tables):
                    end = tables[k + 1].start() if k + 1 < len(tables) else len(body)
                    market, until = _nissan_note(_t(body[tm.end():end]))
                    if not _nissan_market_applies(market, city, state):
                        continue
                    until = until or tnc_until
                    if _o.expired(until):
                        continue
                    out += _nissan_table(tm.group(0), model, url, city, market, until, tnc_url)
            else:   # benefit amounts are drawn inside images: keep the applicable, unexpired block without an amount
                for nm in re.finditer(r"Note:(.*?)(?=Note:|Click here|$)", txt):
                    market, until = _nissan_note(nm.group(1))
                    until = until or tnc_until
                    if market and _nissan_market_applies(market, city, state) and not _o.expired(until):
                        out.append(Offer(model=model, title=f"{hm.group(0) if hm else 'Monthly offer'} (amounts shown as image)",
                                         amount_inr=None, details="Benefit amounts are published only as an image on the "
                                                                  f"offer page. Applicable market: {market}",
                                         valid_until=until, city=city, source_url=url, kind="other", conditions=tnc))
            for o in _nissan_brandwide(tnc, url, tnc_until):
                if o.title not in seen_brand:
                    seen_brand.add(o.title)
                    out.append(o)
        return out

    def specs(self):
        raise NotSupported('nissan.in publishes no spec or equipment table on its pages (checked 2026-10-23: model pages, sitemap, /specifications.html 404); specs exist only in brochure PDFs (/vehicles/brochures.html) not parsed')


def _nissan_note(note: str):
    mm = re.search(r"Applicable Market\s*:?\s*(.*?)(?=\s*(?:Variant |Note:|Click here|$))", note)
    dm = re.search(r"Applicable til+\s*(\d+)\s*\w*\s+([A-Za-z]+)\s*['’]?\s*(\d{2})", note)
    until = None
    if dm:
        d = _o.day_month_year(dm.group(1), dm.group(2), dm.group(3))
        until = d.isoformat() if d else None
    return (mm.group(1).strip() if mm else None), until


def _nissan_market_applies(market: str | None, city: str, state: str | None) -> bool:
    if not market:
        return False
    toks = [t.lower() for t in (city, state) if t]
    m = market.lower()
    if "exclud" in m:
        return not any(t in m.split("exclud", 1)[1] for t in toks)
    if re.search(r"all (?:india|markets)", m):
        return True
    return any(t in m for t in toks)


def _nissan_tnc(txt: str, state: str | None) -> str | None:
    """'*Terms & conditions apply | All India: ... | Tamil Nadu: ...' -> the paragraph for our state (else All India)."""
    secs = dict(re.findall(r"(?:^|\s)([A-Z][A-Za-z ]{2,20}):\s+(The scheme/benefits.*?)"
                           r"(?=\s+[A-Z][A-Za-z ]{2,20}:\s+The scheme|\s+Nissan India\s|$)", txt))
    if state and state in secs:
        return secs[state].strip()
    return (secs.get("All India") or "").strip() or None


def _nissan_table(tbl: str, model: str, url: str, city: str, market: str, until: str | None, tnc_url: str) -> list[Offer]:
    rows = re.findall(r"<tr.*?</tr>", tbl, re.S)
    head = [r for r in rows if "<th" in r]
    cols = []                                  # [label, complete?]
    if head:
        for c in re.finditer(r"<th([^>]*)>(.*?)</th>", head[0], re.S):
            sm = re.search(r'colspan="(\d+)"', c.group(1))
            full = 'rowspan="2"' in c.group(1) or len(head) == 1
            for _ in range(int(sm.group(1)) if sm else 1):
                cols.append([_t(c.group(2)), full])
        sub = iter([_t(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", head[1], re.S)] if len(head) > 1 else [])
        for c in cols:
            if not c[1]:
                c[0] = f"{c[0]} ({next(sub, '')})".replace(" ()", "")
    out = []
    for r in rows:
        cells = [_t(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if not cells:
            continue
        variant = cells[0]
        for label, val in zip([c[0] for c in cols[1:]], cells[1:]):
            amt = _o.amount(val if re.search(r"INR|Rs|₹", val) else "INR " + val)
            if not amt:
                continue
            low = label.lower()
            kind = ("exchange" if "exchange" in low else "corporate" if "poi" in low else
                    "cash" if re.search(r"cash|navratri|festive|special", low) else _o.kind_of(label))
            cond = f"Applicable market: {market}"
            ex = re.search(r"(?:If used car:\s*|\[)([^\]]*(?:car|make|cars))\]?", label, re.I)
            if kind == "exchange" and ex:
                cond = f"On exchange of used car: {ex.group(1).strip()}. " + cond
            if kind == "corporate":
                cond = "POI offer (selected corporates / employees, per Nissan offer T&C). " + cond
            if "with gst" in low:
                cond += ". Offer with GST"
            title = re.sub(r"\s*\((?:Offer With GST)[^)]*\)", "", label)
            out.append(Offer(model=model, title=f"{title} {_o.inr(amt)}", amount_inr=amt,
                             details=f"{model} {variant}: {label} = {val}. Applicable market: {market}. T&C: {tnc_url}",
                             valid_until=until, city=city, source_url=url, kind=kind, conditions=cond, variant=variant))
    return out


def _nissan_brandwide(tnc: str | None, url: str, until: str | None) -> list[Offer]:
    """Range-wide schemes stated in the page's T&C paragraph (no per-customer amount except a stated voucher)."""
    if not tnc:
        return []
    out = []
    for rx, title in [(r"1 gm\. gold coin offer[^.]*\.", "1 gm gold coin offer (part of total benefit)"),
                      (r"(?:Assured gift|Benefit voucher)[^.]*test drive[^.]*\.", "Test-drive gift"),
                      (r"For customers booking any Nissan car[^.]*\.(?:[^.]*Process of claiming[^.]*\.)?"
                       r"(?:[^.]*one-time participation[^.]*\.)?", "Book & take delivery in October: scratch-and-win / gift")]:
        m = re.search(rx, tnc)
        if m:
            a = _o.amount(m.group(0)) if "voucher" in m.group(0).lower() else None
            out.append(Offer(model=None, title=title + (f" worth up to {_o.inr(a)}" if a else ""), amount_inr=a,
                             details=m.group(0).strip(), valid_until=until, city=None, source_url=url, kind="other",
                             conditions=m.group(0).strip()))
    return out


ADAPTER = NissanAdapter()
