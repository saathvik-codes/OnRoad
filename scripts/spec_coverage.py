"""
Spec coverage per brand for the specs buyers look at first. Counts active variants that have NO row for each
concept (matched on the spec label, however the source spelled it).

    python scripts/spec_coverage.py [db] [car|bike]
"""
import re
import sqlite3
import sys

CONCEPTS = {
    "power": r"power|bhp|\bps\b",
    "torque": r"torque",
    "engine": r"displacement|engine capacity|engine \(cc\)|\bcc\b|battery",
    "ground": r"ground clearance",
    "mileage": r"mileage|fuel efficiency|fuel economy|range|arai",
    "kerb": r"kerb|curb|weight",
    "tank": r"fuel tank|tank capacity",
    "boot": r"boot|luggage|storage",
    "length": r"length",
    "wheelbase": r"wheelbase",
    "seats": r"seating",
}


def coverage(db: str, vtype: str = "car"):
    c = sqlite3.connect(db)
    rows = c.execute("""SELECT v.id, m.brand_slug, m.name, lower(group_concat(s.label, ' | '))
                        FROM variants v JOIN models m ON m.id = v.model_id LEFT JOIN specs s ON s.variant_id = v.id
                        WHERE v.active = 1 AND m.active = 1 AND coalesce(m.vehicle_type, 'car') = ?
                        GROUP BY v.id""", (vtype,)).fetchall()
    out = {}
    for vid, brand, model, labels in rows:
        b = out.setdefault(brand, {"n": 0, **{k: 0 for k in CONCEPTS}, "models": {}})
        b["n"] += 1
        for k, rx in CONCEPTS.items():
            if k == "tank" or k == "boot":
                pass
            if not re.search(rx, labels or ""):
                b[k] += 1
                b["models"].setdefault(model, set()).add(k)
    return out


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "data/onroad.db"
    vt = sys.argv[2] if len(sys.argv) > 2 else "car"
    res = coverage(db, vt)
    keys = list(CONCEPTS)
    print(f"{'brand':16}{'vars':>5} " + " ".join(f"{k[:6]:>6}" for k in keys))
    tot = {k: 0 for k in keys}; n = 0
    for brand, b in sorted(res.items()):
        n += b["n"]
        for k in keys:
            tot[k] += b[k]
        print(f"{brand:16}{b['n']:>5} " + " ".join(f"{b[k]:>6}" for k in keys))
    print(f"{'MISSING TOTAL':16}{n:>5} " + " ".join(f"{tot[k]:>6}" for k in keys))
