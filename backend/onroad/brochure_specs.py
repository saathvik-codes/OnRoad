"""
Spec sheets from each manufacturer's official brochure PDF, for brands whose website does not publish per-variant specs
as text (Jeep's spec page is a single image, Hyundai/Kia load theirs through scripts, MG/Nissan/Skoda only link a PDF ...).

The brochure's "Technical specifications" page is read word by word with positions (pdfplumber): words are grouped into
lines, a line's left-most cluster is the row label, the other clusters are values placed in the column they sit under.
Only rows whose label is a recognised spec term are kept (length, wheelbase, displacement, power, torque, tyres, ...), so
marketing copy never becomes a "spec".

A row with one value applies to every variant. A row with one value per powertrain column is matched to a variant by
fuel (petrol / diesel / CNG / electric) and, among same-fuel columns, by turbo / non-turbo words in the variant name;
when that is still ambiguous, the value is written with each column's name ("1.5 MPi: 115 PS · 1.5 Turbo: 160 PS")
instead of guessing. Adapter specs are never overwritten: a brochure row is added only when the variant has no row with
the same meaning.

    python -m onroad.brochure_specs jeep,mg          # brands to read (model page -> brochure link -> specs)
    python -m onroad.brochure_specs --pdf <url> <model_id>   # one brochure for one model
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from urllib.parse import urljoin

import httpx

from . import db

from .sources.brands._2w_common import USER_AGENT
UA = {"User-Agent": USER_AGENT}

SPEC_LABEL = re.compile(
    r"\b(?:length|width|height|wheel ?base|ground clearance|boot|luggage|cargo|tank|kerb|gross|seating|seats?|"
    r"displacement|engine|cylinders?|bore|stroke|power|torque|transmission|gear ?box|clutch|suspension|brakes?|tyres?|tires?|"
    r"wheels?|turning|battery|range|charg\w*|motor|top speed|acceleration|fuel|mileage|efficiency|emission|drive|frame|"
    r"rake|trail|steering|valves?|compression|cooling|ignition|starting|weight|cam\b|approach|departure|breakover|wading|"
    r"configuration|type|front|rear|size|spare|capacity)\b", re.I)
# terms that make a page a spec page; at least three must appear
PAGE_TERMS = [r"displacement|engine capacity|cubic capacity", r"max(?:imum)?\.? ?power|power \(", r"torque", r"wheel ?base",
              r"overall length|length \(", r"fuel tank|tank capacity", r"kerb|weight", r"tyre|tire", r"ground clearance",
              r"suspension", r"battery|range"]
NOISE = re.compile(r"^(?:\*|#|\^|disclaimer|note|terms|images? shown|accessories)", re.I)


def page_words(page) -> list[dict]:
    return [w for w in page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False, extra_attrs=["fontname"])
            if w.get("upright", True)]


_OCR = None


def ocr_words(image) -> list[dict]:
    """Text boxes from an image (a spec sheet published as a picture, or a scanned brochure page), same shape as
    page_words. Uses RapidOCR when it is installed; without it, image-only sheets are simply skipped."""
    global _OCR
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return []
    import numpy as np
    _OCR = _OCR or RapidOCR()
    res, _ = _OCR(np.asarray(image.convert("RGB")))
    out = []
    for box, text, conf in res or []:
        if float(conf) < 0.6:
            continue                                         # unsure reads never become specs
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        out.append({"text": text.strip(), "x0": min(xs), "x1": max(xs), "top": min(ys), "bottom": max(ys), "fontname": ""})
    return out


def _lines(words: list[dict]) -> list[list[dict]]:
    words.sort(key=lambda w: (round(w["top"]), w["x0"]))
    lines: list[list[dict]] = []
    for w in words:
        # same line when the word overlaps the line's first word by at least half its height (labels often sit a few
        # points lower than their values)
        if lines:
            a = lines[-1][0]
            overlap = min(a["bottom"], w["bottom"]) - max(a["top"], w["top"])
            if overlap >= 0.5 * min(a["bottom"] - a["top"], w["bottom"] - w["top"]):
                lines[-1].append(w); continue
        lines.append([w])
    out = []
    for ln in lines:
        ln.sort(key=lambda w: w["x0"])
        clusters: list[dict] = []
        for w in ln:
            gap = 1.0 * (w["bottom"] - w["top"])           # a word space is ~0.3x the height; columns sit much further apart
            if clusters and w["x0"] - clusters[-1]["x1"] <= gap:
                c = clusters[-1]
                c["text"] += " " + w["text"]; c["x1"] = w["x1"]
            else:
                clusters.append({"text": w["text"], "x0": w["x0"], "x1": w["x1"], "top": w["top"],
                                 "bold": bool(re.search(r"bold|black|heavy|semibold|demi", w.get("fontname", ""), re.I))})
        out.append(clusters)
    return out


def parse_page(words: list[dict]) -> dict:
    """{'columns': [...], 'rows': [{'grp', 'label', 'values': [...]}]} for one spec page's words."""
    lines = _lines(words)
    labelled = [ln[0] for ln in lines if SPEC_LABEL.search(ln[0]["text"]) and re.search(r"[a-z]", ln[0]["text"], re.I)]
    if len(labelled) < 4:
        return {"columns": [], "rows": []}
    left = sorted(c["x0"] for c in labelled)[len(labelled) // 4]   # the label column's left edge (robust to strays)
    label_right = sorted(c["x1"] for c in labelled)[int(len(labelled) * 0.8)]
    # the column count is the most common number of value cells on a line; their mean centres are the column positions
    multi = [[c for c in ln if c["x0"] > label_right - 5] for ln in lines]
    multi = [v for v in multi if len(v) >= 2]
    counts = {}
    for v in multi:
        counts[len(v)] = counts.get(len(v), 0) + 1
    ncols = max(counts, key=lambda k: (counts[k], k)) if counts else 0
    full = [v for v in multi if len(v) == ncols]
    col_x = [sum((v[i]["x0"] + v[i]["x1"]) / 2 for v in full) / len(full) for i in range(ncols)] if full else []
    cur: list[dict] = []

    def col_of(c):
        if not col_x:
            return 0
        if len(cur) == len(col_x) and c in cur:                 # a full line: cells are in column order
            return cur.index(c)
        x = (c["x0"] + c["x1"]) / 2
        return min(range(len(col_x)), key=lambda i: abs(col_x[i] - x))

    columns = [""] * len(col_x)
    lefts = [ln[0] for ln in lines if abs(ln[0]["x0"] - left) <= 18]
    bold_split = 0 < sum(c["bold"] for c in lefts) < len(lefts)    # headings set in bold, row labels regular
    items: list[tuple] = []                                       # ("head", text) | ("row", row) | ("vals", top, pieces)

    def pieces(vals):
        full = len(vals) == len(col_x) and len(vals) > 1
        return [(i if full else None, (c["x0"] + c["x1"]) / 2, c["text"], len(vals)) for i, c in enumerate(vals)]

    # two tables side by side ("Max. Torque | 400 Nm   Wheel Base (mm) | 2964"): a spec label inside a line starts a row
    # of its own, so the right-hand table's values never land in the left-hand row
    split_lines = []
    for ln in lines:
        cut = [i for i, c in enumerate(ln) if i > 0 and _canon_label(c["text"]) and not re.search(r"\d{2}", c["text"])
               and re.search(r"[a-z]{3}", c["text"], re.I)]
        if not cut:
            split_lines.append((ln, False)); continue
        bounds = [0] + cut + [len(ln)]
        for k in range(len(bounds) - 1):
            split_lines.append((ln[bounds[k]:bounds[k + 1]], k > 0))
    for ln, forced in split_lines:
        first = ln[0]
        is_label = forced or abs(first["x0"] - left) <= 18 and re.search(r"[a-z]{2}", first["text"], re.I)
        vals = ln[1:] if is_label else [c for c in ln if c["x0"] > label_right - 5]
        if is_label and not vals and (first["bold"] or not bold_split):
            items.append(("head", first["text"].strip(" :")))          # a heading line ("Engine", "Dimensions")
            continue
        if is_label and re.match(r"^(?:items?|variants?|specifications?|engine type|powertrain)$", first["text"], re.I) and len(vals) >= 2:
            cur[:] = vals
            for c in vals:                                       # the column header row
                columns[col_of(c)] = (columns[col_of(c)] + " " + c["text"]).strip()
            continue
        engine_words = r"petrol|diesel|cng|electric|turbo|mpi|gdi|crdi|kappa|\d\.\d ?l\b|\bmt\b|\bat\b|amt|cvt|dct|ivt"
        # an unlabelled header row: "1.2 Kappa petrol | 1.2 CNG", or variant names above the first row ("Sport | Limited")
        top_header = not any(it[0] == "row" for it in items) and not is_label and len(vals) >= max(2, len(col_x) - 1) \
            and not any(re.search(r"\d{3}", c["text"]) for c in vals)
        engine_header = len(vals) == len(col_x) > 1 and all(re.search(engine_words, c["text"], re.I) for c in vals)
        if not any(columns) and (top_header or engine_header) and not (is_label and _canon_label(first["text"])):
            cur[:] = vals
            for c in vals:
                if not columns[col_of(c)]:
                    columns[col_of(c)] = re.sub(r"[\[(]0[\])]", "(O)", c["text"].strip())   # OCR reads "(O)" as "[0]"
            continue
        if is_label:
            keep = not NOISE.search(first["text"]) and bool(SPEC_LABEL.search(first["text"]))
            items.append(("row", {"label": first["text"].strip(" :"), "top": first["top"], "keep": keep,
                                  "parts": [(first["top"], pieces(vals))] if vals else []}))
        elif vals:
            items.append(("vals", first["top"], pieces(vals)))
    # value lines without a label belong to the vertically nearest label in the same section (labels are often
    # centred against several value lines); on a tie, the label above
    rows: list[dict] = []
    grp, seg = "", []

    def flush():
        labels = sorted((it[1] for it in seg if it[0] == "row"), key=lambda r: r["top"])
        lines_ = sorted((it for it in seg if it[0] == "vals" and any(abs(r["top"] - it[1]) <= 80 for r in labels)),
                        key=lambda it: it[1])                     # far from every label: a diagram or a footnote
        n, m = len(labels), len(lines_)
        if n and m:
            # split the value lines into contiguous blocks, one per label, so each label sits at the centre of its
            # lines (own line included); a kept label left with no value at all costs extra
            def cost(j, a, b):
                r = labels[j]
                tops = [t for t, _ in r["parts"]] + [lines_[k][1] for k in range(a, b)]
                if not tops:
                    return 60.0 if r["keep"] else 0.0
                far = sum(1000 for t in tops if abs(t - r["top"]) > 80)
                return abs(sum(tops) / len(tops) - r["top"]) + far
            INF = float("inf")
            dp = [[INF] * (m + 1) for _ in range(n + 1)]
            back = [[0] * (m + 1) for _ in range(n + 1)]
            dp[0][0] = 0.0
            for j in range(1, n + 1):
                for i in range(m + 1):
                    for a in range(i + 1):
                        c = dp[j - 1][a] + cost(j - 1, a, i)
                        if c < dp[j][i]:
                            dp[j][i], back[j][i] = c, a
            i = m
            for j in range(n, 0, -1):
                a = back[j][i]
                labels[j - 1]["parts"] += [(lines_[k][1], lines_[k][2]) for k in range(a, i)]
                i = a
        for r in labels:
            if r["keep"]:
                r["grp"] = grp
                rows.append(r)

    for it in items:
        if it[0] == "head":
            flush(); seg = []; grp = it[1]
        else:
            seg.append(it)
    flush()
    for r in rows:
        r["parts"].sort(key=lambda p: p[0])
        multi = any(len(ps) > 1 for _, ps in r["parts"])
        cells: dict = {}
        for _, ps in r["parts"]:
            for i, x, text, n in ps:
                if not multi:
                    k = -1
                elif i is not None:
                    k = i
                else:
                    k = min(range(len(col_x)), key=lambda j: abs(col_x[j] - x)) if col_x else -1
                cells[k] = (cells.get(k, "") + " " + text).strip()
        r["cells"] = cells
    out = []
    for r in rows:
        cells = {k: v for k, v in r["cells"].items() if v and not NOISE.search(v)}
        if not cells:
            continue
        if -1 in cells or len(cells) == 1:
            values = [" ".join(cells.values())]
        else:
            values = [cells.get(i, "") for i in range(len(col_x))]
        out.append({"grp": r["grp"], "label": r["label"], "values": [re.sub(r"\s+", " ", v).strip() for v in values]})
    return {"columns": columns if any(columns) else [], "rows": out}


def read_pdf(data: bytes) -> dict:
    import pdfplumber
    best = {"columns": [], "rows": [], "text": ""}
    pages = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text() or ""
            page_text = len(t) > 80
            words = page_words(page) if page_text else None
            if words is None and len(pdf.pages) <= 40:           # a page printed as a picture: read it with OCR
                scale = 150 if max(page.width, page.height) < 1000 else 100
                words = ocr_words(page.to_image(resolution=scale).original)
                t = " ".join(w["text"] for w in words)
            best["text"] += " " + t
            score = sum(bool(re.search(p, t, re.I)) for p in PAGE_TERMS)
            if score >= 3 and words:
                parsed = parse_page(words)
                for r in parsed["rows"]:
                    r["ocr"] = not page_text
                if parsed["rows"]:
                    pages.append((i, parsed))
    # spec tables sometimes run over two pages: keep every page that parsed, columns from the first with a header
    for i, p in pages:
        if not best["columns"] and p["columns"]:
            best["columns"] = p["columns"]
        best["rows"] += p["rows"]
    best["pages"] = [i for i, _ in pages]
    return best


NUM = r"(\d{1,2}[ ,]?\d{3}|\d{2,4}(?:\.\d+)?)"           # "4 330", "4,330", "4330", "50", "1.5"


def _n(x: str) -> float:
    return float(re.sub(r"[ ,]", "", x))


def _mm(lo, hi):
    def f(v):
        m = re.search(NUM + r"\s*(?:mm)?(?![\d.])", v)
        return f"{int(_n(m.group(1)))} mm" if m and lo <= _n(m.group(1)) <= hi else None
    return f


def _unit(rx, lo, hi, fmt):
    def f(v):
        m = re.search(rx, v, re.I)
        return fmt.format(re.sub(r"[ ,]", "", m.group(1))) if m and lo <= _n(m.group(1)) <= hi else None
    return f


def _words(rx, n=80):
    def f(v):
        v = re.sub(r"\s+", " ", v).strip(" ,;")
        return v if re.search(rx, v, re.I) and len(v) <= n and not re.search(r"[-�]", v) else None
    return f


RPM = r"(?:[^@]{0,25}@\s*([\d ,~\-–]+?)\s*(?:r/min|rpm))?"


def _rpm(x):
    return f" @ {re.sub(r'(?<=\d) (?=\d{3})', '', x).strip()} rpm" if x else ""


def _power(v):
    m = re.search(r"(\d{1,3}(?:\.\d+)?)\s*(PS|kW|bhp|hp)\b" + RPM, v, re.I)
    if not m or not 1 <= float(m.group(1)) <= 1200:
        return None
    other = re.search(r"\((\d{1,3}(?:\.\d+)?)\s*(PS|kW|bhp|hp)\)", v, re.I)
    extra = f" ({other.group(1)} {other.group(2)})" if other and other.group(2).lower() != m.group(2).lower() else ""
    u = {"ps": "PS", "kw": "kW", "bhp": "bhp", "hp": "hp"}
    extra = extra.replace(other.group(2), u[other.group(2).lower()]) if extra else ""
    return f"{m.group(1)} {u[m.group(2).lower()]}{extra}{_rpm(m.group(3))}"


def _torque(v):
    m = re.search(r"(\d{1,4}(?:\.\d+)?)\s*Nm" + RPM, v, re.I)
    if not m or not 3 <= float(m.group(1)) <= 1500:
        return None
    return f"{m.group(1)} Nm{_rpm(m.group(2))}"


def _cc(v):
    m = re.search(r"\b(\d\.\d)\s*l\b", v, re.I)
    if m:
        return f"{m.group(1)} L"
    m = re.search(r"(\d{1,2}[ ,]?\d{3}|\d{2,4}(?:\.\d+)?)\s*(?:cc|cm3|cm³)\b", v, re.I)          # the unit is required
    return f"{int(_n(m.group(1)))} cc" if m and 48 <= _n(m.group(1)) <= 7000 else None


def _tyres(v):
    t = re.findall(r"\d{2,3}\s*/\s*\d{2,3}\s*(?:Z?R|-)\s*\d{2}(?:\.\d)?", v, re.I)
    return ", ".join(dict.fromkeys(re.sub(r"\s+", " ", re.sub(r"\s*/\s*", "/", x)).strip() for x in t)) or None


# (label pattern, group, canonical label, value reader): a brochure row is kept only when both match
CANON = [
    (r"\b(?:overall )?length\b(?!.*(?:boot|cargo|load|bed))", "Dimensions", "Length", _mm(1500, 6500)),
    (r"\b(?:overall )?width\b(?!.*(?:mirror|track|tyre|tire))", "Dimensions", "Width", _mm(600, 2600)),
    (r"\b(?:overall )?height\b(?!.*seat)", "Dimensions", "Height", _mm(900, 2300)),
    (r"wheel ?base", "Dimensions", "Wheelbase", _mm(1100, 3800)),
    (r"ground clearance", "Dimensions", "Ground clearance", _mm(100, 350)),
    (r"seat height", "Dimensions", "Seat height", _mm(550, 1000)),
    (r"\b(?:boot|luggage|cargo)\b(?!.*(?:light|lamp|net|cover))", "Dimensions", "Boot space",
     _unit(r"(\d{1,2}[ ,]?\d{3}|\d{2,4})\s*(?:l|litres?|liters?)\b", 10, 3000, "{} L")),
    (r"fuel tank|tank capacity", "Dimensions", "Fuel tank", _unit(r"(\d{1,3}(?:\.\d+)?)\s*(?:l|litres?|liters?)?\b", 2, 160, "{} L")),
    (r"kerb|curb|unladen", "Dimensions", "Kerb weight", _unit(r"(\d{1,2}[ ,]?\d{3}|\d{2,4})\s*(?:kg)?\b", 60, 4000, "{} kg")),
    (r"gross vehicle|gvw|gross weight", "Dimensions", "Gross weight", _unit(r"(\d{1,2}[ ,]?\d{3}|\d{3,4})\s*(?:kg)?\b", 150, 6000, "{} kg")),
    (r"turning (?:circle )?radius", "Dimensions", "Turning radius", _unit(r"(\d(?:\.\d{1,2})?)\s*m\b", 1.5, 8, "{} m")),
    (r"seating capacity|no\.? of seats|^seats?$", "Dimensions", "Seating capacity", _unit(r"\b([1-9])\b", 1, 9, "{}")),
    (r"displacement|engine capacity|cubic capacity|swept volume|engine size", "Engine", "Displacement", _cc),
    (r"max(?:imum)?\.? ?(?:net )?power|^power\b|power output|peak power", "Engine", "Max power", _power),
    (r"max(?:imum)?\.? ?(?:net )?torque|^torque\b|peak torque", "Engine", "Max torque", _torque),
    (r"no\.? of cylinders|^cylinders?\b", "Engine", "Cylinders", _unit(r"\b([1-8])\b", 1, 12, "{}")),
    (r"transmission|gear ?box", "Engine", "Transmission",
     _words(r"\d[- ]?speed|\bmanual\b|\bautomatic\b|\b(?:\d\s?)?(?:AMT|CVT|DCT|DSG|IVT|AT|MT|TC)\b|single[- ]speed", 60)),
    (r"drive ?(?:type|train)|driveline", "Engine", "Drive type", _words(r"\b(?:4x2|4x4|2wd|4wd|awd|fwd|rwd)\b", 30)),
    (r"top speed|max(?:imum)?\.? speed", "Performance", "Top speed", _unit(r"(\d{2,3})\s*(?:km/?h|kmph)", 20, 350, "{} km/h")),
    (r"battery (?:capacity|pack|energy)|^battery$|usable energy", "Battery & range", "Battery capacity",
     _unit(r"(\d{1,3}(?:\.\d+)?)\s*kWh", 1, 250, "{} kWh")),
    (r"\brange\b|driving range|certified range|\bidc\b|\bmidc\b", "Battery & range", "Range", _unit(r"(\d{2,4})\s*km\b", 30, 1200, "{} km")),
    (r"front suspension|suspension.*front", "Suspension & brakes", "Front suspension",
     _words(r"strut|mcpherson|link|beam|axle|wishbone|coil|telescopic|fork|usd|leaf|independent|double", 90)),
    (r"rear suspension|suspension.*rear", "Suspension & brakes", "Rear suspension",
     _words(r"strut|link|beam|axle|wishbone|coil|mono|swing|leaf|independent|torsion|shock|double", 90)),
    (r"front brakes?|brakes?.*front", "Suspension & brakes", "Front brakes", _words(r"disc|drum", 60)),
    (r"rear brakes?|brakes?.*rear", "Suspension & brakes", "Rear brakes", _words(r"disc|drum", 60)),
    (r"tyre|tire", "Wheels & tyres", "Tyre size", _tyres),
]
CANON = [(re.compile(a, re.I), g, l, f) for a, g, l, f in CANON]


def canon(grp: str, label: str, value: str):
    """(group, canonical label, cleaned value) or None. "Front", "Rear", "Size", "Type" rows take their meaning from
    the block they sit in ("Brakes" + "Front" = front brakes)."""
    text = f"{grp} {label}".strip() if re.fullmatch(r"(?:front|rear|size|type)\s*", label, re.I) else label
    unit = re.search(r"\((mm|kg|l|litres?|cc|cm3|nm|ps|kw|bhp|hp|km|kwh|km/h|kmph)\)", label, re.I)
    if unit and re.fullmatch(r"\d[\d ,.]*\W*", value.strip()):        # a bare number: the unit is in the label
        value = re.sub(r"^(\d[\d ,.]*)", r"\1 " + unit.group(1), value.strip())   # "TORQUE (Nm) | 478.5" -> "478.5 Nm"
    for rx, g, cl, read in CANON:
        if rx.search(text):
            v = read(value)
            return (g, cl, v) if v else None
    return None


def read_image(data: bytes) -> dict:
    from PIL import Image
    parsed = parse_page(ocr_words(Image.open(io.BytesIO(data))))
    for r in parsed["rows"]:
        r["ocr"] = True
    parsed["pages"] = [0] if parsed["rows"] else []
    return parsed


def _canon_label(label: str) -> str | None:
    for rx, _, cl, _ in CANON:
        if rx.search(label):
            return cl
    return None


FUEL_WORDS = {"petrol": r"petrol|gasoline|mpi|gdi|tsi|tgdi|t-gdi|vti|i-vtec|revotron|mstallion|ecoboost", "diesel": r"diesel|crdi|tdi|mhawk|revotorq|multijet|turbojet",
              "cng": r"cng", "electric": r"electric|\bev\b|kwh|motor"}


def _pick(columns: list[str], variant: dict) -> list[int]:
    """Indexes of the brochure columns that can belong to this variant."""
    if not columns:
        return []

    def vn(s):
        return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    name = vn(variant.get("name") or "")
    exact = [i for i, c in enumerate(columns) if vn(c) == name]       # columns named after variants ("Sport | Limited (O)")
    if exact:
        return exact
    loose = [i for i, c in enumerate(columns) if re.sub(r"\s+o$", "", vn(c)) == name]
    if len(loose) == 1:
        return loose
    inside = [i for i, c in enumerate(columns) if vn(c) and len(vn(c)) >= 4 and re.search(r"\b" + re.escape(vn(c)) + r"\b", name)]
    if len(inside) == 1:                                         # "RUBICON" column for "Wrangler Rubicon"
        return inside
    fuel = (variant.get("fuel") or "").lower()
    rx = FUEL_WORDS.get(fuel)
    others = [r for f, r in FUEL_WORDS.items() if f != fuel]
    mine = [i for i, c in enumerate(columns) if rx and re.search(rx, c, re.I)]
    idx = [i for i in mine if not any(re.search(r, columns[i], re.I) for r in others)] or mine   # "petrol with CNG" is CNG
    if not idx:
        idx = [i for i, c in enumerate(columns) if not any(re.search(r, c, re.I) for f, r in FUEL_WORDS.items() if f != fuel)]
    cc = variant.get("engine_cc")
    if len(idx) > 1 and cc:                                      # same fuel, several engines: "1.0 TSI" vs "1.5 TSI"
        sized = [i for i in idx if (m := re.search(r"\b(\d\.\d)\s*(?:l\b|litre|tsi|tdi|tgdi|t-gdi|gdi|mpi|turbo|\b)", columns[i], re.I))
                 and abs(float(m.group(1)) * 1000 - cc) <= 120]
        if sized:
            idx = sized
    if len(idx) > 1:                                             # same fuel, several engines: turbo or not
        name = (variant.get("name") or "").lower()
        turbo = bool(re.search(r"turbo|tgdi|t-gdi|gdi|tsi|\bt\b", name))
        narrowed = [i for i in idx if bool(re.search(r"turbo|t-?gdi|tsi", columns[i], re.I)) == turbo]
        if narrowed:
            idx = narrowed
        auto = bool(re.search(r"\b(?:at|amt|cvt|ivt|dct|dsg|automatic)\b", name + " " + (variant.get("transmission") or ""), re.I))
        narrowed = [i for i in idx if re.search(r"\b(?:at|amt|cvt|ivt|dct|dsg|automatic)\b", columns[i], re.I)] if auto else \
                   [i for i in idx if re.search(r"\b(?:mt|manual)\b", columns[i], re.I)]
        if narrowed:
            idx = narrowed
    return idx


def rows_for(parsed: dict) -> list[dict]:
    """Brochure rows reduced to recognised specs with validated values: [{grp, label, values}] ('' where a cell fails)."""
    out, seen = [], set()
    for r in parsed["rows"]:
        got = [canon(r["grp"], r["label"], v) if v else None for v in r["values"]]
        ok = [g for g in got if g]
        if not ok or ok[0][1] in seen:
            continue
        if r.get("ocr") and len({g[2] for g in ok}) > 1:
            continue                                         # OCR column positions can shift: keep table-wide values only
        if len(r["values"]) > 1 and len(ok) < len([v for v in r["values"] if v]) / 2:
            continue                                         # most cells failed: the row is mis-read, drop all of it
        seen.add(ok[0][1])
        out.append({"grp": ok[0][0], "label": ok[0][1], "values": [g[2] if g else "" for g in got]})
    return out


def apply(conn, model_id: str, parsed: dict, url: str, fetched: str, fill_only: bool = False) -> int:
    """Write the document's specs to every variant they belong to. fill_only: only labels the variant has no row for
    yet (a secondary source never replaces the brochure)."""
    rows, columns = rows_for(parsed), parsed["columns"]
    variants = [dict(r) for r in conn.execute("SELECT id, name, fuel, transmission, engine_cc FROM variants WHERE model_id = ? AND COALESCE(active, 1) = 1",
                                              (model_id,))]
    vt = (conn.execute("SELECT COALESCE(b.vehicle_type, 'car') FROM models m JOIN brands b ON b.slug = m.brand_slug WHERE m.id = ?",
                       (model_id,)).fetchone() or ["car"])[0]
    n = 0
    for v in variants:
        mine = "" if fill_only else "AND key NOT LIKE 'brochure_%'"
        have = {_canon_label(r[0]) for r in conn.execute(f"SELECT label FROM specs WHERE variant_id = ? {mine}", (v["id"],))}
        picks = _pick(columns, v)
        for r in rows:
            vals = r["values"]
            if len(vals) == 1:
                value = vals[0]
            else:
                use = [i for i in (picks or range(len(vals))) if i < len(vals) and vals[i]]
                if not use:
                    continue
                distinct = list(dict.fromkeys(vals[i] for i in use))
                if len(distinct) == 1:
                    value = distinct[0]
                elif columns and all(i < len(columns) and columns[i] for i in use):
                    value = " · ".join(f"{columns[i]}: {vals[i]}" for i in use)
                else:
                    continue                                     # several values and no column names: can't say which
            if not value or r["label"] in have or not plausible(r["label"], value, vt):
                continue
            ev = (v.get("fuel") or "").lower() in ("electric", "ev")
            if r["label"] in ("Range", "Battery capacity") and not ev or r["label"] in ("Displacement", "Fuel tank", "Cylinders") and ev:
                continue                                         # a petrol car has no battery range; an EV no fuel tank
            key = "brochure_" + re.sub(r"[^a-z0-9]+", "_", r["label"].lower()).strip("_")
            conn.execute("INSERT OR REPLACE INTO specs VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (v["id"], r["grp"], key, r["label"], value[:300], url, fetched))
            n += 1
    return n


CDN_HOSTS = ("scene7.com", "storyblok.com", "amazonaws.com", "cloudfront.net", "akamaized.net")


def _official(url: str, page_url: str) -> bool:
    """The document must come from the manufacturer: same site family as the model page, or the brand's media CDN."""
    from urllib.parse import urlparse
    h, ph = urlparse(url).hostname or "", urlparse(page_url).hostname or ""
    core = lambda host: {p for p in re.split(r"[.\-]", host) if len(p) > 3 and p not in ("www", "com", "india", "cdn", "media", "static")}
    return bool(core(h) & core(ph)) or h.endswith(CDN_HOSTS)


def _clean_url(u: str) -> str:
    return u.replace("\\u002F", "/").replace("\\/", "/").replace("&amp;", "&").replace("&quot;", '"')


def brochure_links(html: str, base: str) -> list[str]:
    html = _clean_url(html)
    links = {urljoin(base, u) for u in re.findall(r"""["'(]([^"'()\s]+?\.pdf)(?:[?#][^"'\s]*)?["')]""", html, re.I)}
    good = [u for u in links if re.search(r"brochure|spec|leaflet|catalog", u, re.I) and _official(u, base)]
    return sorted(good, key=lambda u: (not re.search(r"spec", u, re.I), len(u)))


def spec_images(html: str, base: str) -> list[str]:
    """Spec sheets published as a picture (Jeep): original image files with 'specification' in the name."""
    found = re.findall(r"""(/[^"'\s,]*?specifications?[^"'\s,]*?\.(?:jpe?g|png))(?=[."'\s,])""", _clean_url(html), re.I)
    return list(dict.fromkeys(urljoin(base, u) for u in found if _official(urljoin(base, u), base)))[:2]


def spec_pages(html: str, base: str) -> list[str]:
    """Same-site pages a model page links as its specifications."""
    from urllib.parse import urlparse
    out = []
    for u in re.findall(r"""href=["']([^"'#]+)["']""", _clean_url(html)):
        full = urljoin(base, u)
        if re.search(r"spec", urlparse(full).path, re.I) and urlparse(full).hostname == urlparse(base).hostname \
                and not full.lower().endswith(".pdf") and full not in out:
            out.append(full)
    return out[:2]


def _names_model(text: str, model_name: str) -> bool:
    """The document is about this model: its distinctive name word appears in it."""
    words = [w for w in re.findall(r"[a-z0-9]+", model_name.lower()) if len(w) >= 2 and w not in ("new", "the", "all", "grand", "plus")]
    t = text.lower()
    return any(re.search(r"\b" + re.escape(w) + r"\b", t) for w in words) if words else True


def run_model(c: httpx.Client, conn, model_id: str, page_url: str | None, pdf_url: str | None = None) -> dict:
    name = (conn.execute("SELECT name FROM models WHERE id = ?", (model_id,)).fetchone() or [""])[0]
    tried = []
    if pdf_url:
        docs = [pdf_url]
    else:
        from urllib.parse import urlparse
        html = c.get(page_url).text
        pages_html = [(page_url, html)]
        docs = brochure_links(html, page_url) + spec_images(html, page_url)
        for sp in spec_pages(html, page_url):
            time.sleep(0.5)
            h2 = c.get(sp).text
            pages_html.append((sp, h2))
            docs += brochure_links(h2, sp) + spec_images(h2, sp)
        # the brand's "download a brochure" page: keep the PDFs whose file name carries this model's name
        tokens = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) >= 3 and w not in ("new", "the", "all", "grand", "plus")]
        for bp in list(dict.fromkeys(urljoin(page_url, u) for u in re.findall(r"""["']((?:https?:/)?/[^"'#\s<>]*brochure[^"'#\s<>]*)["']""", _clean_url(html), re.I)
                                     if not u.lower().endswith(".pdf")))[:2]:
            if urlparse(bp).hostname != urlparse(page_url).hostname:
                continue
            time.sleep(0.5)
            docs += [u for u in brochure_links(c.get(bp).text, bp) if any(t in u.lower() for t in tokens)]
        docs = list(dict.fromkeys(docs))
    for u in docs[:6]:
        r = c.get(u)
        if r.status_code != 200:
            continue
        if r.content.startswith(b"%PDF"):
            parsed = read_pdf(r.content)
            if not _names_model(parsed["text"], name):
                tried.append(f"{u} (not about {name})"); continue
        elif r.headers.get("content-type", "").startswith("image/"):
            parsed = read_image(r.content)
        else:
            continue
        kept = rows_for(parsed)
        if len(kept) >= 4:
            n = apply(conn, model_id, parsed, u, time.strftime("%Y-%m-%dT%H:%M:%S"))
            result = {"model": model_id, "doc": u, "specs": [k["label"] for k in kept], "columns": parsed["columns"], "written": n}
            break
        tried.append(f"{u} ({len(kept)} specs)")
    else:
        result = {"model": model_id, "doc": None, "tried": tried or docs[:3]}
    if not pdf_url:                                              # what the model's own pages publish, for specs still missing
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        jl = jsonld_engines(html)
        if jl["rows"]:
            result["page_engine_specs"] = apply(conn, model_id, jl, page_url, ts, fill_only=True)
        for u, h in pages_html:
            hs = html_specs(h)
            if len(hs["rows"]) >= 2:
                result["page_specs"] = result.get("page_specs", 0) + apply(conn, model_id, hs, u, ts, fill_only=True)
    return result


FUEL_LD = {"benzine": "petrol", "gasoline": "petrol", "petrol": "petrol", "diesel": "diesel", "cng": "cng", "electric": "electric",
           "electricity": "electric", "hybrid": "petrol"}


def jsonld_engines(html: str) -> dict:
    """schema.org Vehicle -> vehicleEngine on the model page (Skoda, Jeep, VW ...): power, torque, displacement per engine,
    in the same shape read_pdf returns, one column per engine ("1.0 TSI petrol")."""
    engines = []
    for m in re.finditer(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", html, re.S | re.I):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        for d in data if isinstance(data, list) else [data]:
            if isinstance(d, dict):
                eng = d.get("vehicleEngine")
                engines += eng if isinstance(eng, list) else [eng] if isinstance(eng, dict) else []
    cols, power, torque, disp = [], [], [], []

    def qv(x):
        if isinstance(x, list):
            x = x[0] if x else None
        if isinstance(x, dict) and x.get("value") not in (None, ""):
            try:
                val = float(str(x["value"]).replace(",", ""))
            except ValueError:
                return None
            return f"{val:g} {x.get('unitText') or x.get('unitCode') or ''}".strip()
        return None
    for e in engines:
        fuel = FUEL_LD.get(str(e.get("fuelType") or "").strip().lower(), str(e.get("fuelType") or ""))
        cols.append(f"{e.get('name') or ''} {fuel}".strip())
        power.append(qv(e.get("enginePower")) or "")
        torque.append(qv(e.get("torque")) or "")
        d = qv(e.get("engineDisplacement"))
        disp.append((d.replace("CMQ", "cc").replace("cm3", "cc")) if d else "")
    rows = []
    for label, vals in (("Max power", power), ("Max torque", torque), ("Displacement", disp)):
        if any(vals):
            rows.append({"grp": "Engine", "label": label, "values": vals})
    return {"columns": cols, "rows": rows, "pages": [], "text": ""}


def run(brands: list[str], only_missing: bool = True) -> list[dict]:
    out = []
    with db.connect() as conn, httpx.Client(headers=UA, timeout=60, follow_redirects=True) as c:
        for b in brands:
            for mid, url in conn.execute("SELECT id, url FROM models WHERE brand_slug = ? AND url IS NOT NULL", (b,)).fetchall():
                if only_missing:
                    thin = conn.execute("""SELECT COUNT(*) FROM variants v WHERE v.model_id = ? AND COALESCE(v.active,1) = 1
                                           AND (SELECT COUNT(*) FROM specs s WHERE s.variant_id = v.id) < 8""", (mid,)).fetchone()[0]
                    if not thin:
                        continue
                try:
                    out.append(run_model(c, conn, mid, url))
                except Exception as e:                           # one bad brochure never stops the brand
                    out.append({"model": mid, "error": str(e)[:120]})
                conn.commit()
                time.sleep(1)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "--pdf":
        with db.connect() as conn, httpx.Client(headers=UA, timeout=60, follow_redirects=True) as c:
            print(json.dumps(run_model(c, conn, sys.argv[3], None, sys.argv[2]), indent=1))
            conn.commit()
    else:
        for r in run(sys.argv[1].split(",")):
            print(json.dumps(r, ensure_ascii=False))


def html_specs(html: str) -> dict:
    """Spec label/value pairs printed in a page's HTML (Citroen, Harley-Davidson, Land Rover spec pages): a short text
    node naming a spec, followed within the next few text nodes by a value that passes that spec's check. A label shown
    with different values on the same page (one per engine or trim) is left out: the page doesn't say which is which."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg"]):
        t.decompose()
    nodes = [re.sub(r"\s+", " ", s).strip() for s in soup.stripped_strings]
    nodes = [n for n in nodes if n]
    found: dict[str, set] = {}
    groups: dict[str, str] = {}
    for i, n in enumerate(nodes):
        if len(n) > 40 or not _canon_label(n):
            continue
        for v in nodes[i + 1:i + 4]:
            if _canon_label(v) and len(v) <= 40 and not re.search(r"\d", v):
                break                                        # reached the next label
            got = canon("", n, v)
            if got:
                found.setdefault(got[1], set()).add(got[2]); groups[got[1]] = got[0]
                break
    rows = [{"grp": groups[k], "label": k, "values": [next(iter(v))]} for k, v in found.items() if len(v) == 1]
    return {"columns": [], "rows": rows, "pages": [], "text": ""}


# what a car or a two-wheeler can physically measure; anything outside is a mis-read cell, never written
PLAUSIBLE = {"car": {"Length": (2900, 5800), "Width": (1400, 2300), "Height": (1200, 2200), "Wheelbase": (1900, 3700),
                     "Kerb weight": (600, 3800), "Fuel tank": (20, 120), "Ground clearance": (110, 320)},
             "bike": {"Length": (1500, 2800), "Width": (550, 1150), "Height": (850, 1650), "Wheelbase": (1100, 1800),
                      "Kerb weight": (60, 460), "Fuel tank": (3, 32), "Ground clearance": (100, 300), "Seat height": (600, 950)}}


def plausible(label: str, value: str, vehicle_type: str) -> bool:
    lim = PLAUSIBLE.get(vehicle_type or "car", {}).get(label)
    if not lim or "·" in value:
        return True
    m = re.match(r"([\d.]+)", value)
    return not m or lim[0] <= float(m.group(1)) <= lim[1]
