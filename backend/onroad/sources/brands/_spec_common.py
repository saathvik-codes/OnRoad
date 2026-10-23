"""
Helpers shared by the brand adapters' specs() methods (Maruti Suzuki, Hyundai, Kia, Mahindra).

Not an adapter itself (no ADAPTER); the leading underscore keeps brand loaders from treating it as one.
Nothing here invents a value: units are only attached when the manufacturer's own field label names the unit
(e.g. "Length (mm)" + "3995" -> "3995 mm"), and feature keys are only a classification of the manufacturer's label.
"""

from __future__ import annotations

import re
from collections import Counter

from ._ga_common import clean

# Values that mean "not fitted" / "not published" in the brands' spec feeds.
ABSENT = {"", "no", "none", "na", "n/a", "-", "--", "0", "0.0", "nil", "not available", "x", "×", "✗", "null", "optional",
          "safety"}   # Maruti's CMS has a few cells literally holding the section name "Safety"


def absent(value) -> bool:
    return value is None or clean(str(value)).strip().lower() in ABSENT


_NUM_ONLY = re.compile(r"^\s*([\d][\d.,]*)\s*(\*{0,3})\s*(\([^)]*\))?\s*$")
_AT_PAIR = re.compile(r"^\s*([\d][\d.,]*)\s*@\s*([\d][\d.,\s\-–]*?)\s*(\*{0,3})\s*$")


def with_unit(value: str, unit: str | None) -> str:
    """'3995' + 'mm' -> '3995 mm'; '335*' + 'L' -> '335 L*'; anything that already has words is returned unchanged."""
    v = clean(str(value))
    if not unit:
        return v
    m = _NUM_ONLY.match(v)
    if m:
        return f"{m.group(1)} {unit}{m.group(2)}" + (f" {m.group(3)}" if m.group(3) else "")
    return v


def with_rpm_unit(value: str, unit: str) -> str:
    """'139 @ 4300' + 'Nm' -> '139 Nm @ 4300 rpm' (only for bare 'number @ number' cells)."""
    v = clean(str(value))
    m = _AT_PAIR.match(v)
    if m:
        return f"{m.group(1)} {unit} @ {m.group(2).strip()} rpm{m.group(3)}"
    return with_unit(v, unit)


def humanize(key: str) -> str:
    """camelCase field name -> 'Camel Case' (used only when the feed has no display label for a field)."""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", key).replace("_", " ")
    return s[:1].upper() + s[1:]


def outlier_dimensions(rows: list[tuple[str, str, str]]) -> set[tuple[str, str]]:
    """
    rows: (model, variant_key, value) for one dimension field. Returns {(model, variant_key)} whose value is a lone
    disagreement inside a model whose other variants (>= 3) all agree - e.g. Maruti's CMS gives one Alto K10 variant
    Dzire dimensions. Those cells are dropped (never replaced).
    """
    by_model: dict[str, list[tuple[str, str]]] = {}
    for model, vk, val in rows:
        by_model.setdefault(model, []).append((vk, val))
    bad = set()
    for model, items in by_model.items():
        cnt = Counter(v for _, v in items)
        if len(cnt) < 2:
            continue
        top, n = cnt.most_common(1)[0]
        for vk, v in items:
            if v != top and cnt[v] == 1 and n >= 3 and n == len(items) - 1:
                bad.add((model, vk))
    return bad


# (regex on "label value" lower-cased, feature key). Order matters only for readability; every match is returned.
_RULES: list[tuple[re.Pattern, str]] = [(re.compile(p, re.I), k) for p, k in [
    (r"\b6\s*airbags?\b|\bsix\s*airbags?\b|\b6\s*\(six\)\s*airbags?", "airbags_6"),
    (r"\bdual\s*(front\s*)?airbags?|\b2\s*airbags?\b|driver\s*(and|&|\+)\s*(co-?driver|passenger)\s*airbags?"
     r"|airbags?\s*[-:(]?\s*driver\s*(and|&|\+)\s*(co-?driver|passenger)|front\s*airbags?\s*\(\s*driver\s*(and|&|\+)", "airbags_2"),
    (r"\besc\b|\besp\b|electronic\s*stability|vehicle\s*stability\s*(management|control)|\bvsm\b|\bvdc\b", "esc"),
    (r"hill[\s-]*(start\s*)?(hold|assist)", "hill_hold"),
    (r"\btpms\b|tyre[\s-]*pressure\s*monitor|tire[\s-]*pressure\s*monitor", "tpms"),
    (r"isofix", "isofix"),
    (r"(rear|reverse|reversing)\s*parking\s*(assist\s*)?sensors?", "rear_parking_sensors"),
    (r"front\s*parking\s*sensors?", "front_parking_sensors"),
    (r"(rear|reverse|reversing|back)[\s-]*(parking\s*|view\s*)?camera|camera\s*with\s*(dynamic\s*)?guidelines", "rear_camera"),
    (r"360\s*°?\s*(degree\s*)?(view\s*|hd\s*view\s*|surround\s*view\s*)?(monitor|camera)|surround\s*view\s*(monitor|camera)", "camera_360"),
    (r"\badas\b|level\s*-?\s*2|\bl2\b", "adas"),
    (r"blind[\s-]*spot\s*(view\s*)?(monitor|warning|collision|detection|view)", "blind_spot_monitor"),
    (r"rear\s*disc|(all|4|four)[\s-]*wheel\s*disc|disc\s*brakes?\s*-?\s*(all|front\s*(and|&)\s*rear)", "rear_disc_brakes"),
    (r"auto(matic)?\s*head\s*(lamps?|lights?)(?!\s*level)|(head\s*lamps?|headlights?)\s*[-(]\s*auto\b"
     r"|automatic\s*headlamps", "auto_headlamps"),
    (r"rain[\s-]*sens", "rain_sensing_wipers"),
    (r"electr(on)?ic\s*parking\s*brake|\bepb\b", "electric_parking_brake"),
    (r"touch\s*-?\s*screen", "touchscreen"),
    (r"digital\s*(display\s*in\s*)?(instrument\s*)?cluster|(tft|lcd)\s*(colou?r\s*)?(instrument\s*)?cluster"
     r"|full(y)?[\s-]*digital|digital\s*instrument|instrument\s*cluster.*(digital|tft)", "digital_cluster"),
    (r"wireless.*(android\s*auto|apple\s*car\s*play|carplay)|(android\s*auto|car\s*play|carplay).*wireless", "wireless_android_auto_carplay"),
    (r"android\s*auto|apple\s*car\s*play|carplay", "android_auto_carplay"),
    (r"connected\s*car|suzuki\s*connect|bluelink|blue\s*link|kia\s*connect|adrenox|connected\s*(car\s*)?tech"
     r"|connected\s*services|\bi-?connect\b|embedded\s*sim|\be-?sim\b", "connected_car"),
    (r"wireless\s*(phone\s*|smartphone\s*|mobile\s*)?charg", "wireless_charger"),
    (r"\binfinity\b|\bbose\b|harman|arkamys|\bjbl\b|\bsony\b|premium\s*(sound|audio)|meridian|dolby\s*atmos", "premium_audio"),
    (r"head[\s-]*up\s*display|\bhud\b", "hud"),
    (r"cruise\s*control", "cruise_control"),
    (r"keyless\s*(entry|go)|smart\s*key|passive\s*entry|remote\s*keyless", "keyless_entry"),
    (r"push[\s-]*(button\s*)?start|start[\s/-]*stop\s*button|engine\s*start[\s/-]*stop(?!.*idle)", "push_button_start"),
    (r"remote\s*(engine\s*)?start", "remote_start"),
    (r"(auto(matic)?|fully\s*automatic|full\s*auto)\s*(temperature|climate)|climate\s*control", "auto_climate"),
    (r"rear\s*(ac|a/c|air[\s-]*con(ditioning|ditioner)?)\s*vents?|rear\s*vents?|ac\s*vents?\s*\(?rear", "rear_ac_vents"),
    (r"ventilated.*seats?|seats?.*ventilat|seat\s*ventilation", "ventilated_seats"),
    (r"(power(ed)?|electric(al(ly)?)?)\s*(adjust(able)?\s*)?driver\s*seat|driver\s*seat.*(power(ed)?|electric(al(ly)?)?)\s*adjust"
     r"|\d+[\s-]*way\s*(power(ed)?|electric(al(ly)?)?)", "powered_driver_seat"),
    (r"pan[ao]r[ao]mic", "panoramic_sunroof"),
    (r"\bsun\s*roof\b|\bsunroof\b|moon\s*roof", "sunroof"),
    (r"ambient", "ambient_lighting"),
    (r"cool(ed|ing)\s*glove", "cooled_glovebox"),
    (r"rear\s*(centre\s*|center\s*|seat\s*)?arm[\s-]*rest", "rear_armrest"),
    (r"height[\s-]*adjust(able|ment)?\s*(\(.*?\)\s*)?(driver('s)?\s*)?seat|seat\s*height\s*adjust", "height_adjustable_seat"),
    (r"\bled\b.*head\s*(lamps?|lights?)|head\s*(lamps?|lights?).*\bled\b|bi-?led|led\s*projector", "led_headlamps"),
    (r"\bled\b.*\b(drls?|daytime)|\b(drls?|daytime\s*running\s*(lamps?|lights?))\b.*\bled\b", "led_drl"),
    (r"alloy\s*wheels?|\balloys?\b", "alloy_wheels"),
    (r"\bfog\s*(lamps?|lights?)", "fog_lamps"),
    (r"roof\s*rails?", "roof_rails"),
]]

_NEG = {
    "auto_climate": re.compile(r"\bmanual\b", re.I),
    "sunroof": re.compile(r"pan[ao]r[ao]mic|fixed\s*glass", re.I),
    "rear_camera": re.compile(r"360|surround", re.I),
    "alloy_wheels": re.compile(r"spare|steel\s*wheel|wheel\s*cover", re.I),
    "android_auto_carplay": re.compile(r"wireless", re.I),
    "push_button_start": re.compile(r"\bidle\b", re.I),
    "keyless_entry": re.compile(r"\bwithout\b", re.I),
    "led_headlamps": re.compile(r"halogen(?!.*\bled\b.*head)", re.I),
    "digital_cluster": re.compile(r"analog(ue)?\s*(instrument|speedo|cluster)(?!.*digital)", re.I),
    "rear_armrest": re.compile(r"without", re.I),
    "adas": re.compile(r"\bl2\b.*(usb|type)", re.I),
}


def feature_keys(label: str, value: str | None = None) -> list[str]:
    """Classify one manufacturer feature line into FEATURE_KEYS (possibly several, e.g. 'ESC with Hill Hold'). Else ['other']."""
    text = clean(f"{label} {value or ''}")
    keys = []
    for rx, key in _RULES:
        if rx.search(text) and not (key in _NEG and _NEG[key].search(text)) and key not in keys:
            keys.append(key)
    if "wireless_android_auto_carplay" in keys and "android_auto_carplay" in keys:
        keys.remove("android_auto_carplay")
    if "panoramic_sunroof" in keys and "sunroof" in keys:
        keys.remove("sunroof")
    return keys or ["other"]


def feature_label(label: str, value) -> str:
    """Manufacturer label, plus the cell text when the cell says more than 'Yes' (e.g. 'Headlamps: LED')."""
    label = clean(label)
    v = clean(str(value)) if value is not None else ""
    if not v or v.lower() in {"yes", "y", "true", "standard", "std", "s", "✓", "✔", "available"}:
        return label
    v = re.sub(r"^(yes|✓|✔)\s*", "", v, flags=re.I).strip(" ()[]:-") or v
    return f"{label}: {v}" if v.lower() not in label.lower() else label
