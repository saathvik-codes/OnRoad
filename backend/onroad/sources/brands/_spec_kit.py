"""
Shared helpers for brand adapters' specs(): turn a manufacturer's own spec / feature tables into Spec and Feature rows.

Not an adapter itself (no ADAPTER); the leading underscore keeps brand loaders from treating it as one.

Nothing here invents a value: spec values are the manufacturer's text (a unit printed only in the row label, e.g.
"Wheelbase (mm)", is appended to a bare number), and a feature is emitted only for a cell that marks it as fitted.
"""

from __future__ import annotations

import re

from ..base import FEATURE_KEYS, Feature, Spec

# ----------------------------------------------------------------------------------------------------------------------
# cell values

_TICK = re.compile(r"^(?:[✓✔☑●•■√✅]|&#10003;|&#10004;|yes|y|std\.?|standard|s|available|fitted)$", re.I)
_NEG = re.compile(r"^(?:[-–—_✗✘×x]|x\b.*|no|n|na|n/a|n\.a\.?|nil|none|not available|not applicable|optional|opt\.?|o|"
                  r"option|accessory|dealer fitted.*)$", re.I)
_TICK_LEAD = re.compile(r"^(?:[✓✔☑●√✅]|&#1000[34];)\s*")


def norm_space(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def is_tick(v: str) -> bool:
    return bool(_TICK.match(norm_space(v)))


def present(v: str | None) -> bool:
    """True when a feature-table cell says the item is fitted (tick, 'Yes', or descriptive text)."""
    v = norm_space(v)
    if not v or _NEG.match(v):
        return False
    return True


def feature_label(label: str, value: str) -> str:
    """Manufacturer wording: the row label, plus the cell text when the cell says more than a tick."""
    label, value = norm_space(label), norm_space(value)
    rest = _TICK_LEAD.sub("", value).strip()
    if not rest or is_tick(value) or rest.lower() == label.lower():
        return label
    if not label:
        return rest
    if rest.lower().startswith(label.lower()):
        return rest
    return f"{label}: {rest}"


# ----------------------------------------------------------------------------------------------------------------------
# keys

SPEC_RULES: list[tuple[str, str, str]] = [
    # (regex on "<section> | <label>", group, key) - first match wins
    (r"ground clearance", "Dimensions", "ground_clearance"),
    (r"wheel ?base", "Dimensions", "wheelbase"),
    (r"\b(kerb|curb|unladen) (weight|mass)|\| ?kerb weight", "Dimensions", "kerb_weight"),
    (r"\boverall length|\| ?length\b|^length\b", "Dimensions", "length"),
    (r"\boverall width|\| ?width\b|^width\b", "Dimensions", "width"),
    (r"\boverall height|\| ?height\b|^height\b", "Dimensions", "height"),
    (r"boot (space|capacity|volume)|luggage (capacity|space|volume)|cargo (volume|capacity|space)|trunk (capacity|volume|space)"
     r"|^boot\b|\| ?boot\b", "Capacity", "boot_space"),
    (r"fuel tank", "Capacity", "fuel_tank"),
    (r"seating capacity|seat(ing)? capacity|no\.? of seats|number of seats|\| ?seating\b|\| ?seats?\b|^seats?\b", "Capacity", "seating_capacity"),
    (r"battery (capacity|energy|size)|usable (energy|capacity)|battery.*kwh|capacity \(kwh\)", "Battery", "battery_capacity"),
    (r"charg(ing|e) time|time to charge|\bdc (fast )?charg|\bac (charg|wall)|fast charg|charging \(", "Battery", "charging_time"),
    (r"\brange\b(?!.*rover)", "Battery", "range"),
    (r"\barai\b|\bmidc\b|certified (fuel|mileage)|mileage", "Efficiency", "mileage_arai"),
    (r"fuel (efficiency|economy|consumption)", "Efficiency", "fuel_efficiency"),
    (r"displacement|engine capacity|cubic capacity|\bcc\b|swept volume", "Engine", "displacement"),
    (r"torque", "Engine", "max_torque"),
    (r"max(imum|\.)? ?(power|output)|peak power|power output|motor power|\| ?power\b|^power\b|total (max\.? )?output|system output",
     "Engine", "max_power"),
    (r"engine (type|description)|^engine\b *(\||$)|\| ?engine$|engine \| ?type$|motor type|^type of engine", "Engine", "engine_type"),
    (r"front brakes?|brakes? \| ?front|brakes?.*\bfront\b(?!.*rear)", "Chassis", "front_brakes"),
    (r"rear brakes?|brakes? \| ?rear|brakes?.*\brear\b(?!.*front)", "Chassis", "rear_brakes"),
    (r"tyre size|tire size|tyres?( & wheels?)?$|tires?$|tyres? \||wheels? (&|and) tyres?|tyre(s)? &|\| ?tyres?\b|tyre dimension"
     r"|wheel & tyre", "Chassis", "tyre_size"),
    (r"transmission|gear ?box|gear type", "Performance", "gearbox"),
    (r"drive ?train|drive ?type|driveline|wheel drive|drive \| ?type|^drive$|\| ?drive$|drive system", "Performance", "drivetrain"),
]
_SPEC_RX = [(re.compile(rx, re.I), g, k) for rx, g, k in SPEC_RULES]

# labels that are technical data but not one of the keys above (never treated as equipment)
TECH = re.compile(
    r"suspension|turning (radius|circle)|gross|g\.?v\.?w|valve|cylinder|bore|stroke|compression|\btrack\b|overhang|steering (gear|type)"
    r"|gear ratio|final drive|stabili[sz]er|charging system|emission|fuel type|fuel system|aspiration|approach angle|departure angle"
    r"|ramp|wading|top speed|acceleration|0 ?- ?100|payload|towing|motor generator|voltage|battery type|cell|spare (wheel|tyre)|"
    r"\bobd\b|\bbs ?(vi|6)\b|lxwxh|l x w x h|\bmm\b|\bkg\b|\bnm\b|\bkw\b|\bps\b|\bbhp\b|\bhp\b|\brpm\b|^type$|^front$|^rear$|^grade$",
    re.I)


def spec_key(section: str, label: str) -> tuple[str, str] | None:
    text = f"{norm_space(section)} | {norm_space(label)}".strip(" |").lower()
    for rx, g, k in _SPEC_RX:
        if rx.search(text):
            return g, k
    return None


FEATURE_RULES: list[tuple[str, str]] = [
    (r"(\b6|six)[ -]?(srs )?air ?bags?", "airbags_6"),
    (r"dual (front )?(srs )?air ?bags?|(\b2|two)[ -]?(srs )?air ?bags?|driver (&|and|\+) (co-?driver|(front )?passenger) "
     r"(srs )?air ?bags?|front (srs )?air ?bags? \(driver|driver \+ co driver", "airbags_2"),
    (r"360|surround view|panoramic view monitor|around view|multi-?view camera|bird'?s?[ -]eye", "camera_360"),
    (r"blind ?spot|\bbsm\b|\bbsd\b|lane ?watch", "blind_spot_monitor"),
    (r"\badas\b|toyota safety sense|honda sensing|i-?activsense|autonomous emergency brak|automatic emergency brak|\baeb\b|"
     r"forward collision|lane keep|lane departure|adaptive cruise|\bacc\b|collision mitigation|pre-?collision|lane trac|"
     r"road departure|traffic jam assist|lane centr|rear cross traffic|level ?2", "adas"),
    (r"electronic stability|stability (control|programme|program)|\besc\b|\besp\b|\bvsc\b|\bvdc\b|\bvsa\b|\bdsc\b", "esc"),
    (r"hill[ -]?(hold|start|assist|launch)|\bhsa\b|\bhac\b|\bhhc\b", "hill_hold"),
    (r"tyre[ -]?pressure|tire[ -]?pressure|\btpms\b", "tpms"),
    (r"isofix|i-size", "isofix"),
    (r"front (parking|park) (sensor|assist)|front & rear (parking )?sensors|front and rear (parking )?sensors", "front_parking_sensors"),
    (r"(rear|reverse|reversing|back) (parking |park )?(sensors?|assist sensors?)|parking sensors? ?\(rear|"
     r"rear park(ing)? distance|park distance control.*rear", "rear_parking_sensors"),
    (r"(rear|reverse|reversing|back)[ -]?(view |parking |park )?(assist )?camera|parking camera|rear ?view camera|"
     r"reverse park assist camera|camera.*(rear|reverse)", "rear_camera"),
    (r"rear disc|disc brakes?.*rear|(front|all)[ &]+rear disc|4[- ]wheel disc|all[- ]wheel disc|four[- ]wheel disc", "rear_disc_brakes"),
    (r"auto(matic)?[ -]?(head ?(lamp|light)s?|light|lamp)|dusk[ -]sensing|light sensor|auto on/?off head|auto high beam|"
     r"automatic high beam", "auto_headlamps"),
    (r"rain[ -]?sens", "rain_sensing_wipers"),
    (r"electr(ic|onic|ical) parking brake|\bepb\b|e-?parking brake|electric park brake", "electric_parking_brake"),
    (r"wireless.*(android|apple|carplay)|(android|apple|carplay).*wireless", "wireless_android_auto_carplay"),
    (r"android ?auto|apple ?car ?play|carplay", "android_auto_carplay"),
    (r"wireless (phone |smartphone |mobile )?charg|qi charg|wireless charger|inductive charg", "wireless_charger"),
    (r"head[- ]?up display|heads[- ]up display|\bhud\b", "hud"),
    (r"(fully )?digital (instrument|driver|cluster|meter|display)|tft (instrument |multi-?information )?cluster|"
     r"virtual cockpit|instrument cluster.*(digital|tft)|(digital|tft).*instrument cluster|full[- ]?(digital|tft)", "digital_cluster"),
    (r"touch ?screen|touch-screen|infotainment (system|screen|display)", "touchscreen"),
    (r"connected car|connected (vehicle|services|technology|tech)|i-?connect|\bconnect\b.*(app|tech)|telematics|i-?smart|"
     r"bluelink|my ?honda connect|nissanconnect|jeep connect|uconnect|myskoda|my skoda connect|volkswagen connect|"
     r"(remote|smart ?watch).*(lock|unlock|climate|ac|engine|vehicle|check|control)|e-?call|emergency call|\bsos\b", "connected_car"),
    (r"remote (engine |vehicle )?start|remote .*start", "remote_start"),
    (r"premium (audio|sound|speaker)|\bbose\b|\bjbl\b|harman|infinity|\bsony\b|\bcanton\b|dynaudio|\bfocal\b|arkamys|"
     r"\bdirac\b|burmester|bang ?& ?olufsen|\bb&o\b|meridian", "premium_audio"),
    (r"adaptive cruise", "adas"),
    (r"cruise control|\bcruise\b", "cruise_control"),
    (r"push[ -]?(button|start)|start[/ -]stop (button|switch)|engine start[ -/]stop|one[- ]touch start|keyless start|"
     r"smart start", "push_button_start"),
    (r"keyless|smart (key|entry|access)|passive entry|kessy|intelligent key|i-?key|remote central locking", "keyless_entry"),
    (r"panoramic (sun|moon|glass )?roof|panoramic roof|panorama", "panoramic_sunroof"),
    (r"sun ?roof|moon ?roof|\bsky ?roof", "sunroof"),
    (r"ventilat(ed|ion).*seat|seats?.*ventilat|cooled seats?", "ventilated_seats"),
    (r"(power(ed)?|electric(al(ly)?)?|\d+[- ]way (power|electric)).*(driver|front) seats?|(driver|front) seats?.*"
     r"(power(ed)?|electric(al(ly)?)?) adjust|power seat|\d+[- ]way power", "powered_driver_seat"),
    (r"(auto(matic)?|digital|dual[- ]zone|tri[- ]zone|three[- ]zone|fully automatic) (temperature |climate|air ?con|a/?c\b)"
     r"|climate control|climatronic|auto ac\b|auto air", "auto_climate"),
    (r"rear (ac|a/c|air ?con|aircon|air) ?(vents?|duct|outlets?)|rear vents|rear seat (ac|air) vent|rear ac\b|vents? for rear",
     "rear_ac_vents"),
    (r"ambient (light|lighting|illumination)|mood light", "ambient_lighting"),
    (r"cool(ed|ing) glove ?box|chilled glove|glove ?box.*cool", "cooled_glovebox"),
    (r"rear (seat )?(centre|center|central)? ?arm ?rest", "rear_armrest"),
    (r"height[- ]adjust(able|ment)?.*(driver|seat)|(driver|front).*seat.*height adjust|driver seat height|seat height adjust",
     "height_adjustable_seat"),
    (r"led (projector )?head ?(lamp|light)s?|(full|bi|all)[- ]?led head|led (reflector|projector|matrix) head|head ?(lamp|light)s?: ?"
     r"(full )?led|matrix led|led (lens )?headlamp|^headlamps?: (full )?(led|bi-led)", "led_headlamps"),
    (r"led (drl|daytime|day ?time|day-time)|daytime running (lamp|light)s?.*led|drls?.*led|led.*(drl|daytime|day ?time)", "led_drl"),
    (r"alloy", "alloy_wheels"),
    (r"fog (lamp|light)", "fog_lamps"),
    (r"roof rail", "roof_rails"),
]
_FEAT_RX = [(re.compile(rx, re.I), k) for rx, k in FEATURE_RULES]
_NOT_ALLOY = re.compile(r"\b(steel|wheel cover|wheel cap)\b(?!.*alloy)", re.I)


def feature_key(text: str) -> str:
    t = norm_space(text)
    for rx, k in _FEAT_RX:
        if rx.search(t):
            if k == "alloy_wheels" and _NOT_ALLOY.search(t) and "alloy" not in t.lower():
                continue
            if k == "led_headlamps" and re.search(r"halogen|multi-?reflector", t, re.I) and not re.search(r"led head|full led", t, re.I):
                continue
            if k == "airbags_6" and not re.search(r"(\b6|six)[ -]?(srs )?air ?bags?", t, re.I):
                continue
            assert k in FEATURE_KEYS, k
            return k
    return "other"


# ----------------------------------------------------------------------------------------------------------------------
# spec values

_UNIT_IN_LABEL = re.compile(r"\((mm|cm|m|kg|l|litres?|liters?|kwh|km|kw|nm|ps|cc|km/l|kmpl|seats?)\)", re.I)
_LWH = re.compile(r"l\s*[x×*]\s*w\s*[x×*]\s*h|length\s*[x×]\s*width\s*[x×]\s*height", re.I)


def spec_value(label: str, value: str) -> str:
    """Value with units; a unit printed only in the label (e.g. 'Wheelbase (mm)') is carried onto a bare number."""
    v = norm_space(value)
    m = _UNIT_IN_LABEL.search(label or "")
    if m and re.fullmatch(r"[\d.,]+", v):
        v = f"{v} {m.group(1)}"
    return v


def split_lwh(label: str, value: str) -> list[tuple[str, str, str]] | None:
    """'Overall L x W x H' -> [(key, label, value)] x 3 when the value has exactly three parts; None otherwise."""
    if not _LWH.search(label or ""):
        return None
    v = norm_space(value)
    parts = [p.strip() for p in re.split(r"\s*[x×X*]\s*(?=\d)", v) if p.strip()]
    if len(parts) != 3 or not all(re.match(r"[\d.,]+", p) for p in parts):
        return None
    unit = _UNIT_IN_LABEL.search(label)
    tail = re.search(r"[a-zA-Z]+\.?$", parts[-1])
    out = []
    for key, nm, p in zip(("length", "width", "height"), ("Length", "Width", "Height"), parts):
        if re.fullmatch(r"[\d.,]+", p):
            if tail:
                p = f"{p} {tail.group(0)}"
            elif unit:
                p = f"{p} {unit.group(1)}"
        out.append((key, nm, p))
    return out


# ----------------------------------------------------------------------------------------------------------------------
# HTML tables

def table_grid(table) -> list[list[str]]:
    """bs4 <table> -> rectangular list of cell texts (rowspan / colspan expanded). Tick images become '✓', cross images '-'."""
    rows: list[list[str]] = []
    spans: dict[tuple[int, int], str] = {}
    for r, tr in enumerate(table.find_all("tr")):
        row: list[str] = []
        c = 0
        cells = iter(tr.find_all(["td", "th"], recursive=False))
        while True:
            if (r, c) in spans:
                row.append(spans.pop((r, c)))
                c += 1
                continue
            cell = next(cells, None)
            if cell is None:
                break
            t = cell_text(cell)
            cs = int(re.sub(r"\D", "", str(cell.get("colspan") or "1")) or 1)
            rs = int(re.sub(r"\D", "", str(cell.get("rowspan") or "1")) or 1)
            for _ in range(cs):
                row.append(t)
                for j in range(1, rs):
                    spans[(r + j, c)] = t
                c += 1
        while (r, c) in spans:
            row.append(spans.pop((r, c)))
            c += 1
        rows.append(row)
    return rows


def cell_text(cell) -> str:
    t = norm_space(cell.get_text(" ", strip=True))
    if not t:
        img = cell.find("img")
        if img is not None:
            ref = ((img.get("alt") or "") + " " + (img.get("src") or "") + " " + " ".join(img.get("class") or [])).lower()
            if "tick" in ref or "check" in ref or "yes" in ref:
                return "✓"
            if "cross" in ref or "no" in ref.split() or "minus" in ref:
                return "-"
        icon = cell.find(["i", "span"], class_=re.compile(r"tick|check|yes", re.I))
        if icon is not None:
            return "✓"
    return t


# ----------------------------------------------------------------------------------------------------------------------
# variant dimensions (used to decide which published column / qualifier applies to which priced variant)

_FUEL_TOK = [
    (r"\b(e-?)?cng\b", "CNG"), (r"\bdiesel\b|\bcrdi\b|\btdi\b|multijet|\bdci\b|i-?dtec", "Diesel"),
    (r"strong hybrid|\bhybrid\b|e-?drive|e:hev|\bshev\b|e-?tech", "Strong Hybrid"),
    (r"\bpetrol\b|\bgasoline\b|neo ?drive|\btsi\b|turbo petrol|\bmpi\b", "Petrol"),
    (r"\bev\b|electric\b", "Electric"),
]
_TRANS_TOK = [
    (r"\bamt\b|\bags\b|ez-?shift|easy-?r\b", "AMT"), (r"\bimt\b", "iMT"), (r"\bdct\b|\bdsg\b|\bdca\b|\bedc\b", "DCT"),
    (r"\bcvt\b|e-?cvt|\bivt\b|x-?tronic", "CVT"), (r"\bm/?t\b|\bmanual\b|\d ?mt\b", "MT"),
    (r"\ba/?t\b|\bautomatic\b|\d ?at\b|\btc\b", "AT"),
]
_DRIVE_TOK = [(r"\b4x4\b|\b4wd\b|\bawd\b|\b4motion\b|\ballgrip\b", "4WD"), (r"\b4x2\b|\b2wd\b|\bfwd\b|\brwd\b", "2WD")]


def dims(text: str) -> dict[str, set[str]]:
    """Fuel / transmission / drive tokens a piece of text names (empty set = not named)."""
    t = norm_space(text).lower()
    out: dict[str, set[str]] = {"fuel": set(), "trans": set(), "drive": set()}
    for rx, v in _FUEL_TOK:
        if re.search(rx, t):
            out["fuel"].add(v)
    for rx, v in _TRANS_TOK:
        if re.search(rx, t):
            out["trans"].add(v)
    for rx, v in _DRIVE_TOK:
        if re.search(rx, t):
            out["drive"].add(v)
    return out


def variant_dims(name: str, fuel: str | None, transmission: str | None) -> dict[str, set[str]]:
    d = dims(name)
    if fuel and not d["fuel"]:
        d["fuel"] = {fuel if fuel != "Hybrid" else "Strong Hybrid"}
    if not d["trans"] and transmission:
        d["trans"] = {{"Manual": "MT", "Automatic": "AT", "e-CVT": "CVT", "DSG": "DCT"}.get(transmission, transmission)}
    return d


_QUAL = re.compile(r"\(([^()]{1,60})\)|\[([^\[\]]{1,60})\]|[-–:]\s*([^-–:]{1,40}?)\s*variants?\b|\bfor ([\w /&+-]{1,40}?) variants?\b"
                   r"|\bin ([\w /&+-]{1,30}?) (?:variants?|only)\b|\bonly (?:on|in|for) ([\w /&+-]{1,30})", re.I)


def qualifiers(text: str) -> dict[str, set[str]]:
    """Dimensions named in a qualifier of a label/value: '(AT)', '[4WD]', '- 4WD Variants', 'only on AT'."""
    out: dict[str, set[str]] = {"fuel": set(), "trans": set(), "drive": set()}
    for m in _QUAL.finditer(text or ""):
        q = next(g for g in m.groups() if g)
        d = dims(q)
        for k in out:
            out[k] |= d[k]
    return out


def applies(text: str, vd: dict[str, set[str]]) -> bool:
    """False when a qualifier in `text` names a fuel / gearbox / drive the variant does not have."""
    q = qualifiers(text)
    for k in ("fuel", "trans", "drive"):
        if q[k] and vd[k] and not (q[k] & vd[k]):
            # a plain "AT" qualifier also covers the brand's other automatics (CVT / DCT / AMT)
            if k == "trans" and "AT" in q[k] and vd[k] & {"AMT", "CVT", "DCT"}:
                continue
            return False
    return True


def column_matches(header: str, vd: dict[str, set[str]]) -> bool:
    """A column header that names fuel / gearbox / drive only covers variants that have one of those."""
    h = dims(header)
    for k in ("fuel", "trans", "drive"):
        if h[k] and vd[k] and not (h[k] & vd[k]):
            if k == "trans" and "AT" in h[k] and vd[k] & {"AMT", "CVT", "DCT"}:
                continue
            return False
    return True


# ----------------------------------------------------------------------------------------------------------------------
# builder


class SpecSink:
    """Collects rows for one priced variant, de-duplicating spec keys (repeated rows are joined) and feature labels."""

    def __init__(self, model: str, variant: str, fuel: str | None, transmission: str | None):
        self.model, self.variant, self.fuel, self.transmission = model, variant, fuel, transmission
        self.vd = variant_dims(variant, fuel, transmission)
        self._specs: dict[str, list] = {}
        self._feats: dict[str, Feature] = {}

    def spec(self, group: str, key: str, label: str, value: str, src: str, check: bool = True):
        value = norm_space(value)
        if not value or (check and not applies(f"{label} {value}", self.vd)) or _NEG.match(value):
            return
        if key in self._specs:
            cur = self._specs[key]
            if value not in cur[2].split(" ; "):
                cur[2] = f"{cur[2]} ; {value}"
            return
        self._specs[key] = [group, norm_space(label), value, src]

    def feature(self, label: str, value: str, src: str, key: str | None = None, check: bool = True):
        if not present(value):
            return
        lab = feature_label(label, value)
        if not lab or (check and not applies(lab, self.vd)):
            return
        k = key or feature_key(lab)
        if lab.lower() not in self._feats:
            self._feats[lab.lower()] = Feature(self.model, self.variant, self.fuel, self.transmission, k, lab[:300], src)

    def row(self, section: str, label: str, value: str, src: str, kind: str = "auto"):
        """One published row: becomes a spec when its label is a spec key, equipment when it is not technical data."""
        label, value = norm_space(label), norm_space(value)
        if not label and not value:
            return
        parts = split_lwh(label, value)
        if parts:
            for key, nm, v in parts:
                self.spec("Dimensions", key, nm, v, src)
            return
        sk = spec_key(section, label) if kind != "feature" else None
        if sk:
            self.spec(sk[0], sk[1], label, spec_value(label, value), src)
            return
        if kind == "spec" or TECH.search(label):
            return
        self.feature(label, value, src)

    @property
    def has_data(self) -> bool:
        return bool(self._specs or self._feats)

    def out(self) -> tuple[list[Spec], list[Feature]]:
        specs = [Spec(self.model, self.variant, self.fuel, self.transmission, g, k, lab, val, src)
                 for k, (g, lab, val, src) in self._specs.items()]
        return specs, list(self._feats.values())


def strip_colour(variant: str) -> str:
    """'V AT 2WD NEODRIVE [Cafe White x Midnight Black]' -> 'V AT 2WD NEODRIVE' (colour / trim-colour suffixes only)."""
    return norm_space(re.sub(r"\s*\[[^\]]*\]\s*$", "", variant))


# ----------------------------------------------------------------------------------------------------------------------
# column tables: a published spec / feature table whose columns are trims (or fuels, gearboxes ...)

HEADER_WORDS = {"", "features", "feature", "grade", "grades", "fuel type", "fuel", "variant", "variants", "parameters",
                "seat options", "specifications", "specification", "trim", "trims", "model", "version", "versions",
                "technical specifications", "key features", "transmission"}


class PubTable:
    """cols: one header string per value column; rows: (section, label, [cell per column])."""

    def __init__(self, cols: list[str], rows: list[tuple[str, str, list[str]]], src: str, kind: str = "auto"):
        self.cols, self.rows, self.src, self.kind = cols, rows, src, kind


def html_tables(tables, src: str, label_cols: int = 1, header_words: set[str] | None = None,
                kind: str = "auto", section: str = "") -> list[PubTable]:
    """bs4 <table>s -> PubTables. Leading rows whose first cell is a header word form the column headers; a table without
    its own header row reuses the previous table's header when the column count is the same. Rows whose cells are all
    equal are section titles."""
    words = HEADER_WORDS | {w.lower() for w in (header_words or set())}
    out: list[PubTable] = []
    prev: list[str] | None = None
    for t in tables:
        g = [r for r in table_grid(t) if any(c for c in r)]
        if not g:
            continue
        width = max(len(r) for r in g)
        g = [r + [""] * (width - len(r)) for r in g]
        heads = []
        while g and re.sub(r"[^a-z ]", "", g[0][0].lower()).strip() in words and len(set(g[0])) > 1:
            heads.append(g.pop(0))
        if heads:
            cols = [" ".join(h[i] for h in heads) for i in range(label_cols, width)]
        elif prev is not None and len(prev) == width - label_cols:
            cols = prev
        else:
            cols = [""] * (width - label_cols)
        prev = cols
        rows, sec = [], section
        for r in g:
            if len(set(r)) == 1:
                sec = r[0]
                continue
            label = r[0]
            vals = r[label_cols:]
            if label_cols == 2:
                detail = r[1]
                vals = [detail if (detail and is_tick(v)) else ("" if detail and not present(v) else v) for v in vals]
            rows.append((sec, label, vals))
        out.append(PubTable(cols, rows, src, kind))
    return out


def grade_tokens(text: str, vocab) -> set[str]:
    t = re.sub(r"\s+\((O|o)\)", "(O)", norm_space(text))
    found = set()
    for g in sorted(vocab, key=len, reverse=True):
        rx = r"(?<![\w(+-])" + re.escape(g) + r"(?![\w(+-])"
        if re.search(rx, t):
            found.add(g)
            t = re.sub(rx, " ", t)
    return found


def apply_tables(sink: SpecSink, tables: list[PubTable], grade: str | None = None, vocab=(), col_ok=None) -> None:
    """Feed every row of `tables` that applies to the sink's variant. A column applies when its header names no other
    grade / fuel / gearbox / drive. When several columns apply with different values, the row is ambiguous and skipped."""
    for t in tables:
        idx = []
        for i, h in enumerate(t.cols):
            if col_ok is not None:
                if not col_ok(h):
                    continue
            else:
                if not column_matches(h, sink.vd):
                    continue
                if vocab:
                    gt = grade_tokens(h, vocab)
                    if gt and grade not in gt:
                        continue
            idx.append(i)
        if not idx:
            continue
        for sec, label, vals in t.rows:
            vs = {norm_space(vals[i]) for i in idx if i < len(vals)}
            if len(vs) != 1:
                continue
            sink.row(sec, label, vs.pop(), t.src, t.kind)
