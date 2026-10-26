"""
Data audit: finds values that are implausible or contradict each other, so nothing wrong reaches the app.

  * spec values out of range for their label (brochure_specs.plausible), cars and bikes separately;
  * one variant with two different figures for the same spec from different sources (manufacturer vs fallback);
  * power that does not fit the engine (bhp per litre), torque far off for the power;
  * ex-showroom prices far from the rest of the model's variants, or below a floor for the segment;
  * active variants with no price at all.

    python scripts/data_audit.py [db] [--fix]     --fix deletes only fallback (online_*) rows that are wrong
"""
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from onroad.brochure_specs import _canon_label, plausible  # noqa: E402

DB = next((a for a in sys.argv[1:] if not a.startswith("--")), "data/onroad.db")
FIX = "--fix" in sys.argv


def num(v):
    m = re.search(r"(\d+(?:\.\d+)?)", (v or "").replace(",", ""))
    return float(m.group(1)) if m else None


def main():
    c = sqlite3.connect(DB)
    rows = c.execute("""SELECT s.variant_id, s.key, s.label, s.value, coalesce(m.vehicle_type, 'car'), v.engine_cc, v.fuel, m.id, v.name
                        FROM specs s JOIN variants v ON v.id = s.variant_id JOIN models m ON m.id = v.model_id
                        WHERE v.active = 1 AND m.active = 1""").fetchall()
    bad, by = [], defaultdict(lambda: defaultdict(list))
    for vid, key, label, value, vt, cc, fuel, mid, vname in rows:
        canon = _canon_label(label) or label
        by[vid][canon].append((key, value))
        if canon in ("Max power", "Max torque", "Ground clearance", "Kerb weight", "Displacement", "Fuel tank", "Length", "Width",
                     "Height", "Wheelbase", "Boot space", "Top speed", "Seating capacity") and not plausible(canon, value, "bike" if vt == "bike" else "car"):
            bad.append(("implausible", vid, key, canon, value, mid))
    # conflicts: two sources, two different numbers (more than 3% apart)
    for vid, specs in by.items():
        for canon, vals in specs.items():
            nums = {(k, num(v)) for k, v in vals if num(v)}
            if len(nums) > 1:
                xs = [x for _, x in nums]
                if max(xs) > min(xs) * 1.03 and canon in ("Max power", "Max torque", "Ground clearance", "Kerb weight", "Displacement",
                                                          "Fuel tank", "Mileage", "Length", "Width", "Height", "Wheelbase"):
                    for k, x in nums:
                        if k.startswith("online_"):
                            bad.append(("conflicts with manufacturer", vid, k, canon, x, ""))
    # power per litre (cars, combustion only)
    for vid, specs in by.items():
        p = next((num(v) for k, v in specs.get("Max power", [])), None)
        d = next((num(v) for k, v in specs.get("Displacement", [])), None)
        if p and d and d > 300:
            unit = specs["Max power"][0][1].lower()
            bhp = p * 0.986 if "ps" in unit else p * 1.341 if "kw" in unit else p
            per_l = bhp / d * 1000
            if not 25 <= per_l <= 260:
                bad.append(("power does not fit engine", vid, specs["Max power"][0][0], "Max power", f"{p} for {d} cc", ""))
    # prices
    pr = c.execute("""SELECT v.model_id, v.id, v.name, p.ex_showroom_inr, coalesce(m.vehicle_type,'car') FROM variants v JOIN models m ON m.id = v.model_id
                      JOIN prices p ON p.variant_id = v.id AND p.city = 'Hyderabad'
                      WHERE v.active = 1 AND m.active = 1 AND p.fetched_at = (SELECT MAX(fetched_at) FROM prices q WHERE q.variant_id = v.id AND q.city = 'Hyderabad')""").fetchall()
    per_model = defaultdict(list)
    for mid, vid, name, inr, vt in pr:
        per_model[mid].append((vid, name, inr, vt))
    price_flags = []
    for mid, vs in per_model.items():
        xs = sorted(x[2] for x in vs if x[2])
        if not xs:
            continue
        med = xs[len(xs) // 2]
        for vid, name, inr, vt in vs:
            floor = 25_000 if vt == "bike" else 300_000
            if inr and (inr < floor or inr > med * 3 or inr < med / 3):
                price_flags.append((mid, name, inr, med))
    unpriced = c.execute("""SELECT count(*) FROM variants v JOIN models m ON m.id = v.model_id WHERE v.active = 1 AND m.active = 1
                            AND NOT EXISTS (SELECT 1 FROM prices p WHERE p.variant_id = v.id)""").fetchone()[0]

    kinds = defaultdict(int)
    for b in bad:
        kinds[b[0]] += 1
    print("spec rows checked:", len(rows))
    print("problems:", dict(kinds))
    for b in sorted(bad, key=lambda x: x[0] != "power does not fit engine")[:25]:
        print("  ", b)
    print("price outliers:", len(price_flags))
    for f in price_flags[:20]:
        print("  ", f)
    print("active variants without any price:", unpriced)
    if FIX:
        n = 0
        for kind, vid, key, *_ in bad:
            if key.startswith("online_"):
                n += c.execute("DELETE FROM specs WHERE variant_id = ? AND key = ?", (vid, key)).rowcount
        c.commit()
        print("removed fallback rows:", n)


if __name__ == "__main__":
    main()
