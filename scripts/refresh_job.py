"""
The data refresh, run by GitHub Actions (.github/workflows/refresh.yml) every 6 hours instead of on the API server.

  1. start from the latest published snapshot (falls back to data/seed.db);
  2. every brand's models, variants, prices, offers, dealers and specs for the launch city;
  3. other cities in rotation until the time budget is used (the position is kept in the snapshot);
  4. bank loan rates, offer-link check, crash tests, sales ranks; galleries and per-variant specs once a week;
  5. write dist/: catalogue.db.gz (no user data), manifest.json, research files. The workflow uploads them to the
     "data-latest" release and the server picks them up (onroad/snapshot.py).

    python scripts/refresh_job.py [--minutes 300]
"""
import argparse
import gzip
import logging
import os
import shutil
import sys
import time
import urllib.request
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "onroad.db"
os.environ["DB_PATH"] = str(DB)
os.environ.setdefault("FIRESTORE_SYNC", "0")
os.environ["SNAPSHOT_PULL"] = "0"
os.environ.pop("REFRESH_EVERY_HOURS", None)
sys.path.insert(0, str(ROOT / "backend"))

log = logging.getLogger("refresh_job")
RELEASE = os.getenv("SNAPSHOT_RELEASE", "https://github.com/saathvik-codes/OnRoad/releases/download/data-latest")


def base_db() -> str:
    try:
        with urllib.request.urlopen(f"{RELEASE}/catalogue.db.gz", timeout=120) as r, open(DB.with_suffix(".gz"), "wb") as f:
            shutil.copyfileobj(r, f)
        with gzip.open(DB.with_suffix(".gz"), "rb") as g, open(DB, "wb") as f:
            shutil.copyfileobj(g, f)
        DB.with_suffix(".gz").unlink()
        for name in ("popularity.json", "crash_tests.json"):
            try:
                with urllib.request.urlopen(f"{RELEASE}/{name}", timeout=60) as r:
                    (ROOT / "data" / "research" / name).write_bytes(r.read())
            except Exception:
                pass
        return "previous snapshot"
    except Exception as e:
        shutil.copy(ROOT / "data" / "seed.db", DB)
        return f"seed.db ({e})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=300)
    ap.add_argument("--out", default=str(ROOT / "dist"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    deadline = time.time() + args.minutes * 60
    log.info("base: %s", base_db())

    from onroad import db, ingest, snapshot
    from onroad.api import CITIES
    db.init()

    def state(k, v=None):
        with closing(db.connect()) as conn, conn:
            conn.execute("CREATE TABLE IF NOT EXISTS job_state (k TEXT PRIMARY KEY, v TEXT)")      # shipped with the snapshot
            if v is not None:
                conn.execute("INSERT OR REPLACE INTO job_state VALUES (?, ?)", (k, str(v)))
                return v
            r = conn.execute("SELECT v FROM job_state WHERE k = ?", (k,)).fetchone()
            return r[0] if r else None

    def step(name, fn):
        t = time.time()
        try:
            fn()
            log.info("%s done in %.0fs", name, time.time() - t)
        except Exception as e:
            log.warning("%s failed: %s", name, e)

    def weekly(name, fn):
        last = float(state(f"last_{name}") or 0)
        if time.time() - last > 7 * 86400 and time.time() < deadline - 1800:
            step(name, fn)
            state(f"last_{name}", time.time())

    step("brands (Hyderabad)", lambda: ingest.run(None, city="Hyderabad"))
    from onroad import loan_rates, offer_links
    step("loan rates", loan_rates.refresh)
    step("offer links", offer_links.run)
    from onroad import crash_tests_sync, popularity_sync
    step("crash tests", crash_tests_sync.sync)
    step("sales ranks", popularity_sync.run)

    def galleries():
        from onroad import gallery_sync, image_check
        gallery_sync.run(); gallery_sync.run_fallback(); image_check.run()
    weekly("photos", galleries)

    def variant_specs():
        from onroad import variant_specs_fill
        with closing(db.connect()) as conn:
            brands = [r[0] for r in conn.execute("SELECT DISTINCT brand_slug FROM models WHERE active = 1 AND coalesce(vehicle_type,'car') = 'car'")]
        variant_specs_fill.run(brands)
    weekly("variant_specs", variant_specs)

    # other cities in rotation until the budget is spent (leave 10 minutes to build the snapshot)
    cities = [c for c in CITIES if c != "Hyderabad"]
    i = int(state("city_cursor") or 0)
    done = 0
    while time.time() < deadline - 600 and done < len(cities):
        city = cities[i % len(cities)]
        step(f"city {city}", lambda: ingest.run(None, city=city))
        i += 1; done += 1
        state("city_cursor", i)

    def tidy():
        from onroad import spec_repair
        with closing(db.connect()) as conn, conn:
            log.info("spec repair: %s", spec_repair.repair(conn))
    step("spec repair", tidy)            # wrong labels / formats from older parsers never reach the app

    m = snapshot.build(Path(args.out))
    log.info("snapshot: %s", m)


if __name__ == "__main__":
    main()
