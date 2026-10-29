"""
Per-variant spec fill from each variant's own CarDekho page, for figures that differ between engines and gearboxes
(power, torque, mileage, kerb weight) and model figures the manufacturer sheet missed (ground clearance, tank).

Rules, so it never contradicts or invents:
  * only specs a variant has no row for are written; manufacturer rows are never replaced;
  * our variant is matched to theirs on fuel and manual/automatic first (and turbo where a model has both), then on
    the trim words both names share; without a shared trim word the page is only a same-engine twin and gives
    engine figures and mileage, nothing trim-specific;
  * the page's fuel must match and, where we know the engine size, its displacement must be within 60 cc;
  * every value passes brochure_specs' unit + range checks; robots.txt allows /overview/ pages; one page per ~1.2 s.

    python -m onroad.variant_specs_fill kia,hyundai
"""
from __future__ import annotations

import json
import re
import sys
import time

import httpx

from . import db
from .brochure_specs import UA, _canon_label, canon, plausible
from .online_specs import BRAND, KEEP, SLUG, _fuel

MILEAGE_L = re.compile(r"^(arai |claimed |city |highway )?(mileage|fuel efficiency|fuel economy)( \(arai\))?$", re.I)
MILEAGE_V = re.compile(r"(\d{1,2}(?:\.\d{1,2})?)\s*(kmpl|km/l|km/kg|kmpkg)", re.I)
WANT = KEEP | {"Mileage"}
ENGINE_FIGS = {"Max power", "Max torque", "Displacement", "Mileage", "Cylinders", "Kerb weight", "Top speed"}
NEEDED = {"Max power", "Max torque", "Ground clearance", "Mileage", "Kerb weight", "Displacement", "Fuel tank"}
AUTO = re.compile(r"\b(at|amt|ags|dct|dca|ivt|cvt|tc|automatic|e-?cvt|dsg|\d(at|dct|dsg|ivt|cvt|tc))\b", re.I)
TURBO = re.compile(r"turbo|\btsi\b|t-?gdi|turbojet|mstallion", re.I)
NOISE = {"smartstream", "crdi", "vgt", "gdi", "mt", "at", "dct", "ivt", "cvt", "amt", "petrol", "diesel", "cng", "manual",
         "automatic", "turbo", "paint", "group", "dual", "tone", "dt", "new", "with", "and", "the", "n"}


def read_variant(html: str) -> tuple[dict, str | None]:
    """The spec table of one variant page; the first value of a spec is this variant's (later ones are rival cars)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg"]):
        t.decompose()
    nodes = [re.sub(r"\s+", " ", x).strip() for x in soup.stripped_strings]
    out, fuel = {}, None
    for i, n in enumerate(nodes[:-1]):
        v = nodes[i + 1]
        if re.fullmatch(r"fuel type", n, re.I):
            fuel = fuel or v.lower()
        if len(n) > 40:
            continue
        if MILEAGE_L.match(n):
            m = MILEAGE_V.search(v)
            if m and "Mileage" not in out and 5 <= float(m.group(1)) <= 45:
                unit = m.group(2).lower().replace("km/l", "kmpl").replace("kmpkg", "km/kg")
                out["Mileage"] = ("Engine", f"{m.group(1)} {unit}")
            continue
        if not _canon_label(n):
            continue
        got = canon("", n, v)
        if got and got[1] not in out:
            out[got[1]] = (got[0], got[2])
    return out, fuel


def read_features(html: str) -> list[tuple[str, str]]:
    """(label, value) of every equipment item the variant page marks as fitted: a tick, or a value such as "6" for
    the number of airbags. Items marked with a cross are left out."""
    out, seen = [], set()
    for sec in re.finditer(r'<h3[^>]*data-vani-focus="([^"]+)"[^>]*>.*?</h3>\s*<table[^>]*>(.*?)</table>', html, re.S):
        group = re.sub(r"&amp;", "&", sec.group(1))
        if re.search(r"engine|transmission|fuel|suspension|steering|brake|dimension|capacit|performance", group, re.I):
            continue                                              # these sections are specifications, read elsewhere
        for row in re.finditer(r"<tr>(.*?)</tr>", sec.group(2), re.S):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row.group(1), re.S)
            if len(cells) < 2:
                continue
            label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cells[0])).strip()
            cell = cells[1]
            if not label or label in seen or "icon-delete" in cell or "icon-cross" in cell or "icon-close" in cell:
                continue
            value = "" if "icon-check" in cell else re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cell)).strip()
            if value.lower() in ("no", "not available", "-", "na", "n/a"):
                continue
            seen.add(label)
            out.append((label, value))
    return out


def _tok(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9+]+", (s or "").lower())
            if w not in NOISE and not re.fullmatch(r"\d+(\.\d+)?|[dg]\d\.\d\w*|\d(mt|at|dct|ivt|cvt|amt|tc|dsg)", w)}


def cd_variants(c: httpx.Client, url: str) -> list[tuple[str, str]]:
    """(name, url) of every variant the model page lists in its structured data."""
    r = c.get(url)
    if r.status_code != 200:
        return []
    out = []
    for m in re.finditer(r'"@type":"Product","name":"([^"]+)","sku":"[^"]*","url":"(https://www\.cardekho\.com/overview/[^"]+)"', r.text):
        if (m.group(1), m.group(2)) not in out:
            out.append((m.group(1), m.group(2)))
    return out


def run_model(c: httpx.Client, conn, model_id: str) -> dict:
    brand, slug = model_id.split("/", 1)
    name = (conn.execute("SELECT name FROM models WHERE id = ?", (model_id,)).fetchone() or [""])[0]
    theirs = cd_variants(c, f"https://www.cardekho.com/{BRAND.get(brand, brand.replace('_', '-'))}/{SLUG.get(model_id, slug)}")
    if not theirs:
        return {"model": model_id, "theirs": 0}
    mwords = _tok(name) | _tok(brand.replace("_", " "))
    cands = []
    for nm, u in theirs:
        fuel = "diesel" if re.search(r"diesel", nm, re.I) else "cng" if re.search(r"cng", nm, re.I) else \
            "electric" if re.search(r"electric|\bev\b|kwh|long range|\blr\b", nm, re.I) else "petrol"
        d = re.search(r"\b(\d\.\d)\b", nm)
        cands.append({"url": u, "fuel": fuel, "auto": bool(AUTO.search(nm)), "turbo": bool(TURBO.search(nm)), "trim": _tok(nm) - mwords,
                      "disp": d.group(1) if d else None})
    vs = conn.execute("SELECT id, name, fuel, transmission, engine_cc FROM variants WHERE model_id = ? AND COALESCE(active, 1) = 1",
                      (model_id,)).fetchall()
    if any(_fuel(v[2]) == "electric" for v in vs):
        for x in cands:                       # an EV model's page names rarely say "electric"
            if x["fuel"] == "petrol" and all(_fuel(v[2]) == "electric" for v in vs):
                x["fuel"] = "electric"
    mixed = len({bool(TURBO.search(v[1] or "")) for v in vs}) > 1
    pages, ts, n, matched = {}, time.strftime("%Y-%m-%dT%H:%M:%S"), 0, 0
    feats_of: dict[str, list] = {}
    from .sources.brands._spec_common import feature_keys, feature_label
    for vid, vname, vfuel, vtrans, vcc in vs:
        have = {_canon_label(x[0]) or x[0] for x in conn.execute("SELECT label FROM specs WHERE variant_id = ?", (vid,))}
        if any(re.search(r"mileage|fuel efficiency|fuel economy", h or "", re.I) for h in have):
            have.add("Mileage")
        need = WANT - have
        no_feats = not conn.execute("SELECT 1 FROM features WHERE variant_id = ? LIMIT 1", (vid,)).fetchone()
        if not need & NEEDED and not no_feats:
            continue
        f = _fuel(vfuel)
        auto = (vtrans or "manual").lower() != "manual"
        pool = [x for x in cands if x["fuel"] == f and (x["auto"] == auto or f == "electric")]
        if mixed:
            pool = [x for x in pool if x["turbo"] == bool(TURBO.search(vname or ""))]
        own = conn.execute("""SELECT source_url FROM prices WHERE variant_id = ? AND source_url LIKE 'https://www.cardekho.com/overview/%'
                              ORDER BY fetched_at DESC LIMIT 1""", (vid,)).fetchone()
        if not pool and not own:
            continue
        mine = _tok(vname) - mwords
        my_disp = (re.search(r"(?<![\d.])(\d\.\d)(?![\d.])", vname or "") or [None, None])[1]
        hint = re.search(r"(?:tce|e-tech|tsi|tgdi|t-gdi|\bhp|\bps)\s*(\d{2,3})\b", vname or "", re.I)
        hint = int(hint.group(1)) if hint else None
        if my_disp:
            pool = [x for x in pool if x["disp"] in (None, my_disp)] or pool
        # several engine sizes left and nothing in our name says which: engine figures would be a guess
        ambiguous = not my_disp and not hint and len({x["disp"] for x in pool} - {None}) > 1
        ranked = sorted(pool, key=lambda x: (-len(mine & x["trim"]), len(x["trim"] - mine)))
        # a variant we priced from a variant page already knows its page: use it, exactly
        if own:
            ranked = [x for x in cands if x["url"] == own[0]] or [{"url": own[0], "fuel": f, "auto": auto, "turbo": False,
                                                                  "trim": mine, "disp": None}]
            mine = ranked[0]["trim"] | mine
            pool = ranked
            ambiguous = False
        best = specs = None
        for cand in ranked[:3]:
            if cand["url"] not in pages:
                r = c.get(cand["url"])
                pages[cand["url"]] = read_variant(r.text) if r.status_code == 200 else ({}, None)
                feats_of[cand["url"]] = read_features(r.text) if r.status_code == 200 else []
                time.sleep(1.2)
            sp, pfuel = pages[cand["url"]]
            if (not sp and not (own and feats_of.get(cand["url"]))) or (pfuel and _fuel(pfuel) != f and not own):
                continue
            m = re.match(r"(\d+) cc", sp.get("Displacement", (None, ""))[1])
            if vcc and m and abs(vcc - int(m.group(1))) > 60:
                continue
            if hint:                                    # "TCe 160" must be the ~160 PS engine
                pm = re.match(r"([\d.]+)\s*(bhp|ps|kw|hp)", sp.get("Max power", (None, ""))[1], re.I)
                if not pm:
                    continue
                ps = float(pm.group(1)) * {"bhp": 1.014, "hp": 1.014, "ps": 1.0, "kw": 1.36}[pm.group(2).lower()]
                if abs(ps - hint) / hint > 0.12:
                    continue
            best, specs = cand, sp
            break
        if not best:
            continue
        exact = bool(mine & best["trim"])
        matched += 1
        if no_feats and exact:
            for label, value in feats_of.get(best["url"], []):
                for key in feature_keys(label, value):
                    k = key if key != "other" else "cd_" + re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:40]
                    conn.execute("INSERT OR IGNORE INTO features (variant_id, key, label, source_url, fetched_at) VALUES (?, ?, ?, ?, ?)",
                                 (vid, k, feature_label(label, value), best["url"], ts))
                    n += 1
        for label, (grp, value) in specs.items():
            if label not in need:
                continue
            if not exact and label in ("Kerb weight", "Tyre size", "Seating capacity", "Boot space"):
                continue
            if ambiguous and label in ENGINE_FIGS:
                continue
            if label != "Mileage" and not plausible(label, value, "car"):
                continue
            if (label in ("Range", "Battery capacity") and f != "electric") or \
                    (label in ("Displacement", "Fuel tank", "Cylinders", "Mileage") and f == "electric"):
                continue
            key = "online_" + re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
            conn.execute("INSERT OR REPLACE INTO specs VALUES (?, ?, ?, ?, ?, ?, ?)", (vid, grp, key, label, value, best["url"], ts))
            n += 1
    return {"model": model_id, "variants": len(vs), "matched": matched, "pages": len(pages), "written": n}


def run(brands: list[str]) -> None:
    with db.connect() as conn, httpx.Client(headers=UA, timeout=40, follow_redirects=True) as c:
        for b in brands:
            for (mid,) in conn.execute("SELECT id FROM models WHERE brand_slug = ? AND active = 1 AND coalesce(vehicle_type, 'car') = 'car'",
                                       (b,)).fetchall():
                try:
                    res = run_model(c, conn, mid)
                except Exception as e:
                    res = {"model": mid, "error": str(e)[:120]}
                conn.commit()
                print(json.dumps(res), flush=True)
                time.sleep(1)


if __name__ == "__main__":
    run(sys.argv[1].split(","))
