"""
Hero MotoCorp - https://www.heromotocorp.com  (robots.txt: everything allowed except a test path)

Endpoints used:
  GET /en-in/price-list.html
        header navigation (div.bike-item-container): model page link, model title, displacement and the model's
        Scene7 image (s7ap1.scene7.com/is/image/hmcl/<asset>, Hero's own DAM). Used by models().
  GET /en-in/<motorcycles|scooters>/[performance/]<model>-price-in-<city>-in-<state code>.html
        server-rendered "PRICE OF VARIANTS IN <CITY>" table (variant | Ex-showroom Price). These are the pages the
        site's own state/city selector opens; they are listed in /en-in/price-sitemap.xml. One page per model per city.
  dealers.heromotocorp.com/location/<state>/<city>  -> its XHR
  GET https://weblocationapi.dashloc.com/v1/branches-by-company/<company id>/?state=&city=&limit=&offset=
        the official dealer locator's own API (no robots.txt on that host; dealers.heromotocorp.com only disallows /api/).

City: prices are per city (Hyderabad = "-price-in-hyderabad-in-tlg.html").
Verified 2026-10-22 (Hyderabad): Splendor+ DRUM BRAKE OBD2B Rs 78,956 and SPLENDOR+ 125 MILLION EDITION Rs 81,966;
38 Hyderabad outlets in the locator (branchCount on the page = API total).
Gaps: Vida electric scooters are sold through vidaworld.com (not read); Mavrick / X440 T have no city price pages
(skipped when the page 404s); Scene7 nav images are the largest model shots the site offers (about 490-870 px);
offers not read; specs not read.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import Site, cc_of, clean, dashloc_dealers, inr, trans_2w
from ._geo import geo

BASE = "https://www.heromotocorp.com"
LOCATOR = "https://dealers.heromotocorp.com"
COMPANY_ID = "3ad8111e-c406-496b-bf95-a582f0a9fbf1"     # pinia.mainstore.currentCompanyId on the locator page
STATE_CODE = {"Telangana": "tlg", "Karnataka": "kar", "Maharashtra": "mah", "Tamil Nadu": "tn", "Delhi": "del",
              "Andhra Pradesh": "ap", "West Bengal": "wb", "Gujarat": "gj", "Rajasthan": "rj", "Uttar Pradesh": "up",
              "Kerala": "ker", "Haryana": "hr", "Madhya Pradesh": "mp", "Chandigarh": "cd", "Punjab": "pb"}


def _body(slug: str, path: str) -> str:
    s = slug.lower()
    if "/scooters/" in path:
        return "Scooter"
    if "xpulse" in s:
        return "Adventure"
    if "karizma" in s:
        return "Sports"
    if any(k in s for k in ("xtreme", "mavrick", "x440", "harley")):
        return "Street"
    return "Commuter"


class HeroAdapter(BrandAdapter):
    brand = "Hero MotoCorp"
    slug = "hero"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._models = None

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def models(self) -> list[dict]:
        if self._models is not None:
            return self._models
        page = self.s.text("/en-in/price-list.html")
        out, seen = [], set()
        for blk in page.split('class="bike-item-container')[1:]:
            blk = blk[:4000]
            href = re.search(r'<a href="(/en-in/(?:motorcycles|scooters)/[^"]+?\.html)"', blk)
            img = re.search(r'<img src="(https://s7ap1\.scene7\.com/is/image/hmcl/[^"?]+|/content/dam/[^"?]+)', blk)
            title = re.search(r'class="bike-title[^"]*">(.*?)</div>', blk, re.S)
            if not (href and title):
                continue
            path = href.group(1)
            slug = path.rsplit("/", 1)[-1][:-5].lower()
            if slug in seen:
                continue
            seen.add(slug)
            spec = re.search(r'class="bike-spec[^"]*">(.*?)</div>', blk, re.S)
            out.append({"name": clean(title.group(1)), "url": BASE + path, "body_type": _body(slug, path),
                        "image_url": (img.group(1) if img.group(1).startswith("http") else BASE + img.group(1)) if img else None, "engine_cc": cc_of(spec.group(1) if spec else ""),
                        "_slug": slug, "_path": path})
        if not out:
            raise NotSupported("Hero price-list navigation layout changed")
        self._models = out
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        code = STATE_CODE.get(g[0]) if g else None
        if not code:
            raise NotSupported(f"Hero state code for {city!r} unknown")
        cslug = city.lower().replace(" ", "-")
        out = []
        for m in self.models():
            cat = "scooters" if "/scooters/" in m["_path"] else "motorcycles"
            perf = "performance/" if "/performance/" in m["_path"] else ""
            url = f"{BASE}/en-in/{cat}/{perf}{m['_slug']}-price-in-{cslug}-in-{code}.html"
            r = self.s.get(url, ok=(200, 404))
            if r.status_code == 404 or "price-list-table-component" not in r.text:
                continue
            page = r.text
            sec = page[page.find('class="price-list-table-component"'):]
            sec = sec[:sec.find("</table>")]
            shown_city = re.search(r'class="location-span">([^<]+)<', page)
            if shown_city and shown_city.group(1).strip().lower() != city.lower():
                continue                          # the site fell back to another city: do not mislabel
            for row in re.findall(r"<tr>(.*?)</tr>", sec, re.S):
                cells = [clean(c) for c in re.findall(r"<td>(.*?)</td>", row, re.S)]
                if len(cells) != 2:
                    continue
                price = inr(cells[1])
                if not price:
                    continue
                fuel = "Petrol"
                out.append(Variant(model=m["name"], variant=cells[0], fuel=fuel,
                                   transmission=trans_2w(m["body_type"], fuel), ex_showroom_inr=price, city=city,
                                   source_url=url, body_type=m["body_type"], engine_cc=m.get("engine_cc"),
                                   model_url=m["url"], image_url=m.get("image_url")))
        if not out:
            raise NotSupported(f"Hero publishes no price pages for {city!r}")
        return out

    def dealers(self, city: str = "Hyderabad"):
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown")
        page_url = f"{LOCATOR}/location/{g[0].lower().replace(' ', '-')}/{city.lower().replace(' ', '-')}"
        return dashloc_dealers(self.s, COMPANY_ID, city, g[0], LOCATOR, page_url)

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter (campaign pages under /en-in/campaigns/offers/)")


ADAPTER = HeroAdapter()
