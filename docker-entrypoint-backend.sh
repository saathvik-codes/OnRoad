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
n = c.execute("INSERT OR REPLACE INTO specs SELECT * FROM seed.specs WHERE variant_id IN (SELECT id FROM main.variants)").rowcount
c.commit()
print(f"[entrypoint] merged {n} spec rows from seed")
PY
fi
mkdir -p "${IMG_CACHE:-$(dirname "$DB_PATH")/img_cache}"

exec "$@"
