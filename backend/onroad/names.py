"""
Display names for variants. Stored names stay exactly as each source publishes them (prices are matched on them);
this only tidies what buyers read:
  * the brand / model name repeated at the start goes ("XTREME 160R 4V PRO" under Xtreme 160R 4V -> "PRO" -> "Pro");
  * SHOUTED words become Title case; real acronyms and codes (AMT, DCT, ABS, HTX, 4X4, T160 ...) stay as they are;
  * seat codes read as words ("7STR", "[7S]" -> "7-seater"), model years as "MY2027", stray dashes and spaces go;
  * internal codes in brackets become a short suffix ("Rizta S (RIZS1LR)" -> "Rizta S · LR").
If two variants of a model would end up with the same display name, both keep their published names.
"""
from __future__ import annotations

import re

ACRONYM = {"ABS", "CBS", "AMT", "CVT", "DCT", "DSG", "IVT", "IMT", "MT", "AT", "TC", "EV", "CNG", "LED", "TFT", "ADAS", "AWD", "FWD",
           "RWD", "4WD", "2WD", "TSI", "TDI", "GDI", "MPI", "CRDI", "DLX", "STD", "OBD", "USD", "ESP", "IFS", "AC", "PS", "RHD", "HTE",
           "HTK", "HTX", "GTX", "GT", "DX", "SX", "LX", "VX", "ZX", "EX", "MX", "AX", "RS", "RR", "SE", "LE", "XE", "XT", "XZ", "XM",
           "XL", "XLS", "MY", "O", "II", "III", "IV", "V", "SV", "SVR", "GTS", "AMG", "JCW", "HSE", "TVS", "KTM", "BMW", "MG", "BYD",
           "BSVI", "SUV", "MUV", "IDC", "WB", "FE", "N", "R", "S", "T", "X", "Z"}


TITLE = {"PRO", "MAX", "TOP", "NEW", "RED", "ONE", "DUO", "FIT", "ZEN"}


def _word(w: str) -> str:
    if "-" in w.strip("-"):
        return "-".join(_word(p) for p in w.split("-"))
    core = re.sub(r"[^A-Za-z]", "", w)
    if not core or not w.isupper() or core in ACRONYM or re.search(r"[\d()]", w) or (len(core) <= 3 and core not in TITLE):
        return w
    return w[:1] + w[1:].lower() if w[:1].isalpha() else w[:1] + w[1:2] + w[2:].lower()


def pretty(brand: str, model: str, name: str) -> str:
    s = (name or "").strip()
    if not s:
        return s
    short = (brand or "").split(" ")[0]
    bare = re.sub(r"^(?:" + re.escape(brand) + "|" + re.escape(short) + r")\s+", "", model or "", flags=re.I) if brand else model
    for prefix in (f"{brand} {model}", f"{short} {bare}", model, bare, brand, short):
        if prefix and re.match(re.escape(prefix) + r"\b", s, re.I) and len(s) > len(prefix) + 1:
            s = s[len(prefix):].strip()
    s = re.sub(r"^[-–:·,\s]+", "", s)
    if re.search(r"citro", brand or "", re.I):                # Citroen's price list: "Comfort Edition - You", "Na Max", "- 7s"
        s = re.sub(r"^Comfort Edition\s*-\s*(.+)$", r"\1 · Comfort Edition", s)
        s = re.sub(r"^Na\s+(.+?)(\s*·|\s*-|$)", r"\1 · non-turbo\2", s)
    s = re.sub(r"\s*-\s*(\d)\s?[sS]\b", r" · \1-seater", s)              # "Turbo Max - 7s" -> "Turbo Max · 7-seater"
    s = re.sub(r"\(?\b(?:BS-?VI(?:\.2)?|BS-?6(?:\.2)?|OBD-?2B?|ODB-?2B?|E20)\b\)?", " ", s, flags=re.I)  # on every new vehicle
    s = re.sub(r"^\(([^()]{2,12})\)\s*", r"\1 ", s)                       # "(2.7L) 4x2 AT" -> "2.7L 4x2 AT"
    s = re.sub(r"\b(?:NON[ -]?AC|NAC)\b", "Non-AC", s, flags=re.I)
    s = re.sub(r"\s*\[([A-Za-z][A-Za-z ]{3,40})\]", r" · \1", s)          # "[Platinum White Pearl]" -> "· Platinum White Pearl"
    if re.search(r"\b(?:Sd|Td|Ug|SD|TD|UG)\b", s) and re.search(r"pulsar|platina|avenger|dominar|bajaj", (model + brand).lower()):
        s = re.sub(r"\b(?:Sd|SD)\b", "Single Disc", s); s = re.sub(r"\b(?:Td|TD)\b", "Twin Disc", s); s = re.sub(r"\bUg\b", "UG", s)
    s = re.sub(r"\[(\d)S\]|\b(\d)\s?STR\b", lambda m: f"{m.group(1) or m.group(2)}-seater", s, flags=re.I)
    s = re.sub(r"\(MY(\d{4})\)", r"· MY\1", s)
    s = re.sub(r"\(RIZ[SZ]1?([A-Z0-9]{2,3})\)", lambda m: "· " + m.group(1), s)   # Ather codes: (RIZS1LR) -> · LR
    s = re.sub(r"\s*-\s*(?=[A-Za-z])", " – ", s) if re.search(r"\s-\S|\S-\s", s) else s
    s = re.sub(r"\s{2,}", " ", s).strip(" -–·,")
    s = " ".join(_word(w) for w in s.split(" "))
    if re.fullmatch(r"Starting price.*", s, re.I):
        return "Base (starting price)"
    if not s or s.lower() in ((model or "").lower(), (bare or "").lower()):
        return "Standard"                                          # the variant is just the model
    return s


def display_names(brand: str, model: str, variants: list[dict], key: str = "name") -> None:
    """Adds display_name to each variant dict in place. Two variants that would read the same are told apart by fuel,
    then gearbox ("HX 2 · CNG"); if even that doesn't separate them, both keep their published names."""
    out = [pretty(brand, model, v.get(key) or "") for v in variants]
    def counts(xs):
        c: dict[str, int] = {}
        for x in xs:
            c[x.lower()] = c.get(x.lower(), 0) + 1
        return c
    for field in ("fuel", "transmission"):
        c = counts(out)
        out = [d if c[d.lower()] == 1 or not v.get(field) or v[field].lower() in d.lower() else f"{d} · {v[field]}"
               for v, d in zip(variants, out)]
    c = counts(out)
    for v, d in zip(variants, out):
        v["display_name"] = d if c[d.lower()] == 1 else v.get(key)
