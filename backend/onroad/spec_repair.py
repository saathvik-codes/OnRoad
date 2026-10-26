"""
Repairs stored spec rows that an older parser labelled wrongly or wrote in an untidy format. Runs before every
snapshot (scripts/refresh_job.py), so a fix here reaches the app on the next refresh. It never invents a value: rows
are relabelled to what the source said, reformatted, or deleted.

  * a bike's seat height filed as overall "Height", a scooter's seat length filed as overall "Length";
  * a power-to-weight figure filed as power or kerb weight;
  * "4 594", "2,498" and "0.045 m3 (45 l)" become "4594 mm", "2498 mm" and "45 L";
  * anything still outside the sane range for its label is removed (manufacturer rows included: a wrong number is
    worse than a blank).
"""
from __future__ import annotations

import re

from .brochure_specs import _canon_label, plausible

DIMS = ("Length", "Width", "Height", "Wheelbase", "Ground clearance", "Seat height")
PLAUS = ("Length", "Width", "Height", "Wheelbase", "Ground clearance", "Kerb weight", "Fuel tank")


def _int(s: str) -> int | None:
    m = re.fullmatch(r"\s*(\d{1,2})[ ,](\d{3})\s*(mm)?\s*", s or "") or re.fullmatch(r"\s*(\d{3,4})()\s*(mm)?\s*", s or "")
    return int(m.group(1) + m.group(2)) if m else None


def repair(conn) -> dict:
    n = {"relabelled": 0, "reformatted": 0, "removed": 0}
    rows = conn.execute("""SELECT s.rowid, s.key, s.label, s.value, coalesce(m.vehicle_type, 'car') FROM specs s
                           JOIN variants v ON v.id = s.variant_id JOIN models m ON m.id = v.model_id""").fetchall()
    for rowid, key, raw, value, vt in rows:
        label = _canon_label(raw) or raw
        k = (key or "").lower()
        # seat dimensions filed as the vehicle's; power-to-weight ratios are not power or weight
        if label in ("Height", "Length") and re.search(r"seat|saddle|seating", k):
            conn.execute("UPDATE specs SET label = ? WHERE rowid = ?", ("Seat height" if label == "Height" else "Seat length", rowid))
            n["relabelled"] += 1
            continue
        if re.search(r"weight_ratio|power_to_weight", k) or (label == "Kerb weight" and k.startswith("max_power"))                 or (label == "Max power" and re.search(r"weight|ratio", raw or "", re.I)):
            conn.execute("DELETE FROM specs WHERE rowid = ?", (rowid,))
            n["removed"] += 1
            continue
        new = value or ""
        if label in DIMS:
            cm = re.fullmatch(r"\s*(\d{2,3}(?:\.\d)?)\s*cm\s*", new, re.I)
            x = round(float(cm.group(1)) * 10) if cm else _int(new)
            if x is not None:
                new = f"{x} mm"
        elif label == "Kerb weight":
            m = re.fullmatch(r"\s*(\d{1,2})[ ,](\d{3})\s*(kg)?\s*", new) or re.fullmatch(r"\s*(\d{2,4})()\s*(kg)?\s*", new)
            if m:
                new = f"{int(m.group(1) + m.group(2))} kg"
        elif label == "Fuel tank":
            m = re.search(r"\((\d{1,3}(?:\.\d)?)\s*l\)", new, re.I) or re.fullmatch(r"\s*(\d{1,3}(?:\.\d+)?)\s*(?:l|litres?|liters?)?\s*", new, re.I)
            if m:
                new = f"{m.group(1)} L"
        if new != (value or ""):
            conn.execute("UPDATE specs SET value = ? WHERE rowid = ?", (new, rowid))
            n["reformatted"] += 1
        # a single clean number that is impossible for this kind of vehicle goes; ranges and notes stay as published
        if label in PLAUS and re.fullmatch(r"\d+(\.\d+)? (mm|kg|L)", new) and not plausible(label, new, "bike" if vt == "bike" else "car"):
            conn.execute("DELETE FROM specs WHERE rowid = ?", (rowid,))
            n["removed"] += 1
    return n


if __name__ == "__main__":
    import json
    from contextlib import closing
    from . import db
    with closing(db.connect()) as conn, conn:
        print(json.dumps(repair(conn)))
