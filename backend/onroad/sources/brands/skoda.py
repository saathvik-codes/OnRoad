"""
Skoda Auto India - https://www.skoda-auto.co.in

Endpoints used:
  GET  https://www.skoda-auto.co.in/models/range          model list (name, URL, image, categoryKeys) in the page's
                                                         embedded JSON; category labels (Family->"SUV", City->"Sedan")
                                                         are the site's own translations, read from the same page.
  The site's "Get Ex-Showroom Price" tool (https://www.skoda-auto.co.in/aid/checkprice) is an iframe served by Skoda
  India's own skodapeaceofmind.co.in app; its JS (js/dev-checkprice.js) calls two ASP.NET page methods:
  POST https://skodapeaceofmind.co.in/Skoda_TCD/checkprice/CheckPrice.aspx/GetModels   {}  -> model codes
  POST https://skodapeaceofmind.co.in/Skoda_TCD/checkprice/CheckPrice.aspx/GetPrice
       {selectedModel, fuelType, transmissionType} -> [{Variant, ExshowroomPrice, FestivePrice}]
  GET  https://dealers.skoda-auto.co.in/location/telangana/hyderabad[?page=N]  official dealer locator (Singleinterface)

City: the check-price tool takes NO city - it is one national ex-showroom list, and the page states no city, so
prices() returns city="India (national)" whatever city is asked for.
Verified 2026-10-19: Kylaq Classic 1.0 TSI MT 7,59,000 (tool) == "starting at Rs 7.59 lakh" on the Kylaq model page.
When a FestivePrice is published it is used as the price (the tool strikes out the regular price) and the regular
price is not kept.
Known gaps: Superb is listed on /models/range but not in the check-price tool -> no variant prices; the separate
/models/kylaq/kylaq/pricelist-table page shows some different figures (e.g. Signature 9,09,900 vs 9,49,000 in the
tool) - not used, unverified which is newer; engine cc / seats not published in the price data; dealer emails are
not on the locator cards.
Offers (re-checked 2026-10-22; sitemap-web.xml has no offers page, /promotions-old/monthly-offer/detail is an empty
template, check-price FestivePrice is blank for every variant):
  GET  /                         HomeBannerModule slide "Join the Celebration: Assured gifts await at Fan Fest" and the
                                 HometilesModule "Fan Fest offers" (tiles Kushaq, Kylaq, Kodiaq -> test-drive forms).
                                 The tiles are images only; no amount is in the page text/JSON -> one amount-less
                                 offer per model tile, conditions = site-wide offer T&C footer.
  GET  /shopping/corporate-sales "Find your Corporate Eligibility": corporate houses, government employees,
                                 professionals, CSD (defence), MSME special offers ("combination of cash / exchange")
                                 -> brand-wide kind=corporate offers without amounts.
  Gaps: Skoda publishes no rupee amounts, no validity dates and no city split for any offer (checked home, every
  model page, /shopping/exchange, /shopping/buy, test-drive pages); /shopping/exchange only mentions "Exclusive
  Upgrade Benefits" (not emitted: no offer terms).
"""

from __future__ import annotations

import html as _html
import json
import re
import time

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from . import _si_locator
from ._ga_common import visible_text

BASE = "https://www.skoda-auto.co.in"
TCD = "https://skodapeaceofmind.co.in/Skoda_TCD/checkprice"
DEALERS = "https://dealers.skoda-auto.co.in"
DELAY = 0.7
NATIONAL = "India (national)"


class SkodaAdapter(BrandAdapter):
    brand = "Skoda"
    slug = "skoda"
    website = BASE

    def __init__(self):
        self._c = None

    def _client(self):
        if self._c is None:
            self._c = self.client()
        return self._c

    def _get(self, url, **kw):
        time.sleep(DELAY)
        r = self._client().get(url, **kw)
        r.raise_for_status()
        return r

    def _post(self, url, payload):
        time.sleep(DELAY)
        r = self._client().post(url, content=json.dumps(payload), headers={"Content-Type": "application/json; charset=utf-8"})
        r.raise_for_status()
        return r.json().get("d") or []

    # Fallback to official high-resolution transparent Azure FrontDoor images if range page URLs 404
    VERIFIED_IMAGES = {
        "slavia": "https://k2ngtoolsfrontdoorprodfde-gpgketbpfhacepaz.a03.azurefd.net/mdmstorage/images/CBVTOBMDSJ6BHXL2L2XAA63ZR4%3D%3D%3D%3D%3D%3D.png",
        "kushaq": "https://k2ngtoolsfrontdoorprodfde-gpgketbpfhacepaz.a03.azurefd.net/mdmstorage/images/2RU32VPFEAIFELIERKBNHTMYM4%3D%3D%3D%3D%3D%3D.png",
        "kylaq": "https://k2ngtoolsfrontdoorprodfde-gpgketbpfhacepaz.a03.azurefd.net/mdmstorage/images/64ZNUB3WZFUDHJ3PLDNZUIUL7U%3D%3D%3D%3D%3D%3D.png",
        "kodiaq": "https://k2ngtoolsfrontdoorprodfde-gpgketbpfhacepaz.a03.azurefd.net/mdmstorage/images/ZYJFAACOJPEFHQ6DLJDBPE5UWI%3D%3D%3D%3D%3D%3D.png",
        "superb": "https://k2ngtoolsfrontdoorprodfde-gpgketbpfhacepaz.a03.azurefd.net/mdmstorage/images/6GSB5WZSOJOFSEQZLM63BXRNRQ%3D%3D%3D%3D%3D%3D.png",
        "octavia-rs": "https://k2ngtoolsfrontdoorprodfde-gpgketbpfhacepaz.a03.azurefd.net/mdmstorage/images/XCMFUWBPA3ZDKANDOPSOB3RSGA%3D%3D%3D%3D%3D%3D.png",
    }

    # ------------------------------------------------------------ models
    def models(self) -> list[dict]:
        page = _html.unescape(self._get(f"{BASE}/models/range").text)
        cats = {k: v for k, v in re.findall(r'"MDM\.CarCategory\.Category_(\w+)":"([^"]+)"', page)}
        out, seen = [], set()
        for m in re.finditer(r'"categoryKeys":\[([^\]]*)\],"modelName":"([^"]+)".*?"url":"([^"]+)","image":\{"altText":[^,]*,"url":"([^"]+)"', page):
            keys, name, url, img = m.groups()
            if name in seen:
                continue
            seen.add(name)
            body = None
            for k in re.findall(r'"(\w+)"', keys):
                if cats.get(k) in ("SUV", "Sedan", "Hatchback", "MPV"):
                    body = cats[k]
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            valid_img = self.VERIFIED_IMAGES.get(slug) or img
            out.append({"name": name, "url": url, "body_type": body, "image_url": valid_img})
        if not out:
            raise NotSupported("Skoda /models/range layout changed")
        return out

    # ------------------------------------------------------------ prices
    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        js = self._get(f"{TCD}/js/dev-checkprice.js").text
        names = dict(re.findall(r"case\s*'(\w+)'\s*:\s*selectedModel\s*=\s*'([^']+)'", js))
        codes = [m["ModelName"] for m in self._post(f"{TCD}/CheckPrice.aspx/GetModels", {})]
        try:
            site = {re.sub(r"[^a-z]", "", m["name"].lower()): m for m in self.models()}
        except Exception:
            site = {}
        out, seen = [], set()
        for code in codes:
            model = names.get(code, code.title())
            k = re.sub(r"[^a-z]", "", model.lower())
            meta = (site.get(k) or site.get(code) or site.get(re.sub(r"^new", "", code))
                    or site.get(re.sub(r"rs$", "", re.sub(r"^new", "", code))) or {})
            for fuel in ("Petrol", "Diesel"):
                for trans in ("Manual", "Automatic"):
                    rows = self._post(f"{TCD}/CheckPrice.aspx/GetPrice",
                                      {"selectedModel": model, "fuelType": fuel, "transmissionType": trans})
                    for r in rows:
                        regular = int(re.sub(r"\D", "", r["ExshowroomPrice"]) or 0)
                        festive = int(re.sub(r"\D", "", r.get("FestivePrice") or "") or 0)
                        price = festive or regular
                        if not price:
                            continue
                        var = r["Variant"].strip()
                        if not re.search(r"\b(MT|AT|DSG|Manual|Automatic)\b", var):
                            var = f"{var} {'MT' if trans == 'Manual' else 'AT'}"
                        key = (r.get("ModelName") or model, var)
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append(Variant(
                            model=r.get("ModelName") or model, variant=var,
                            fuel=fuel, transmission="DSG" if "DSG" in var else trans, ex_showroom_inr=price, city=NATIONAL,
                            source_url=f"{BASE}/aid/checkprice", body_type=meta.get("body_type"),
                            model_url=meta.get("url"), image_url=meta.get("image_url")))
        return out

    # ------------------------------------------------------------ dealers
    def dealers(self, city: str = "Hyderabad", state: str | None = None) -> list[Dealer]:
        try:
            url, cards = _si_locator.fetch_city(self._client(), DEALERS, city, state, delay=DELAY)
        except LookupError as e:
            raise NotSupported(str(e))
        st = state or (_si_locator.CITY_STATE.get(city.lower()) or "").replace("-", " ").title()
        return _si_locator.to_dealers(cards, city, st, url)

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        """Skoda publishes no amounts: the home page's "Fan Fest offers" tiles (campaign: "Assured gifts await at Fan
        Fest") and the corporate-sales eligibility list ("Special offers are a combination of cash / exchange").
        Both are national and undated, so amount_inr / valid_* / city stay None."""
        out: list[Offer] = []
        home = _html.unescape(self._get(BASE + "/").text)
        terms = _footer_terms(home)
        known = {re.sub(r"[^a-z]", "", n.lower()) for n in ("Kylaq", "Kushaq", "Slavia", "Kodiaq", "Octavia RS", "Superb")}
        campaign = None
        for props in _module_props(home, "HomeBannerModule"):
            for s in (props.get("viewModel") or {}).get("slides") or []:
                if re.search(r"offer|fest|gift|benefit", f"{s.get('title')} {s.get('text')}", re.I):
                    campaign = f"{s.get('title')}: {s.get('text')}".strip(": ")
        for props in _module_props(home, "HometilesModule"):
            vm = props.get("viewModel") or {}
            head = (vm.get("headline") or "").strip()
            if not re.search(r"offer", head, re.I):
                continue
            for t in vm.get("tiles") or []:
                model = (t.get("headline") or "").strip()
                if re.sub(r"[^a-z]", "", model.lower()) not in known:
                    continue                            # e.g. the generic "Book a Test Drive" tile
                out.append(Offer(model=model, title=f"{head}: {campaign or head} (amount not stated)", amount_inr=None,
                                 details=f"{head} - {model}. {campaign or ''} Offer tile on skoda-auto.co.in links to "
                                         f"{t.get('url')}; no benefit amount is published on the site.".strip(),
                                 valid_until=None, city=None, source_url=BASE + "/", kind="other", conditions=terms))
        corp_url = f"{BASE}/shopping/corporate-sales"
        page = re.sub(r"<script.*?</script>|<style.*?</style>", " ", self._get(corp_url).text, flags=re.S | re.I)
        lines = [re.sub(r"\s+", " ", _html.unescape(x)).strip() for x in re.split(r"<[^>]+>", page)]
        lines = [x for x in lines if x and "{" not in x]          # drop inline emotion CSS
        start = next((k for k, x in enumerate(lines) if x == "Find your Corporate Eligibility"), None)
        end = next((k for k, x in enumerate(lines) if x == "Helpline" and start is not None and k > start), len(lines))
        parts = lines[start + 1:end] if start is not None else []
        i = 0
        while i < len(parts):
            head, body = parts[i], []
            i += 1
            while i < len(parts) and parts[i].endswith((".", ")")):
                body.append(parts[i]); i += 1
            text = " ".join(body)
            if body and re.search(r"special offer", text, re.I):
                out.append(Offer(model=None, title=f"Corporate / special offer - {head} (amount not stated)", amount_inr=None,
                                 details=text, valid_until=None, city=None, source_url=corp_url, kind="corporate",
                                 conditions=text))
        if not out:
            raise NotSupported("skoda-auto.co.in shows no Fan Fest / offer tiles and no corporate special offers")
        return out


def _module_props(page: str, container: str) -> list[dict]:
    """data-props JSON of every <div data-modulecontainer="<container>"> module on an (unescaped) Skoda page."""
    out, dec = [], json.JSONDecoder()
    for m in re.finditer(rf'data-modulecontainer="{container}"', page):
        j = page.find('data-props="', m.end())
        if j < 0:
            continue
        try:
            out.append(dec.raw_decode(page, j + len('data-props="'))[0])
        except ValueError:
            pass
    return out


def _footer_terms(page: str) -> str | None:
    """The site-wide offer disclaimer ("Škoda T&C Apply. *Special price under this offer ...")."""
    t = visible_text(page)
    m = re.search(r"(Škoda T&C Apply\..*?Check with your nearest dealership for more information\.)", t)
    return m.group(1) if m else None


ADAPTER = SkodaAdapter()
