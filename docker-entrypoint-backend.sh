#!/bin/sh
set -e

# First boot on a fresh disk: start from the public seed DB (catalogue, prices, specs, dealers; no user data).
DB_PATH="${DB_PATH:-/app/data/onroad.db}"
mkdir -p "$(dirname "$DB_PATH")"
if [ ! -f "$DB_PATH" ]; then
    echo "[entrypoint] Seeding database at $DB_PATH from /app/data/seed.db"
    cp /app/data/seed.db "$DB_PATH"
else
    # an existing disk keeps its users and history; only the spec sheets from a newer seed are merged in
    python - "$DB_PATH" <<'PY' || echo "[entrypoint] spec merge skipped"
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute("ATTACH '/app/data/seed.db' AS seed")
# catalogue tables only (models, variants, prices, specs, galleries, showroom matches); accounts, quotes, reviews untouched
have = {r[0] for r in c.execute("SELECT name FROM main.sqlite_master WHERE type = 'table'")}
seed = {r[0] for r in c.execute("SELECT name FROM seed.sqlite_master WHERE type = 'table'")}
for t, how in (("models", "REPLACE"), ("variants", "REPLACE"), ("prices", "IGNORE"), ("specs", "REPLACE"), ("features", "IGNORE"),
               ("model_gallery", "IGNORE"), ("dealer_places", "IGNORE")):
    if t not in seed:
        continue
    if t not in have:
        c.execute(c.execute("SELECT sql FROM seed.sqlite_master WHERE name = ?", (t,)).fetchone()[0])
    cols = [r[1] for r in c.execute(f"PRAGMA main.table_info({t})")]
    common = [x for x in cols if x in {r[1] for r in c.execute(f"PRAGMA seed.table_info({t})")}]
    n = c.execute(f"INSERT OR {how} INTO main.{t} ({','.join(common)}) SELECT {','.join(common)} FROM seed.{t}").rowcount
    print(f"[entrypoint] merged {n} {t} rows from seed")
c.commit()
PY
fi
mkdir -p "${IMG_CACHE:-$(dirname "$DB_PATH")/img_cache}"

exec "$@"
