#!/bin/sh
set -e

# First boot on a fresh disk: start from the public seed DB (catalogue, prices, specs, dealers; no user data).
DB_PATH="${DB_PATH:-/app/data/onroad.db}"
mkdir -p "$(dirname "$DB_PATH")"
if [ ! -f "$DB_PATH" ]; then
    echo "[entrypoint] Seeding database at $DB_PATH from /app/data/seed.db"
    cp /app/data/seed.db "$DB_PATH"
fi
mkdir -p "${IMG_CACHE:-$(dirname "$DB_PATH")/img_cache}"

exec "$@"
