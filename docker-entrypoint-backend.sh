#!/bin/sh
set -e

# If a persistent disk is mounted and the DB doesn't exist yet, seed it.
if [ -n "$DB_PATH" ] && [ "$DB_PATH" != "/app/data/onroad.db" ]; then
    DB_DIR=$(dirname "$DB_PATH")
    mkdir -p "$DB_DIR"
    if [ ! -f "$DB_PATH" ]; then
        echo "[entrypoint] Seeding database from image copy to $DB_PATH ..."
        cp /app/data/onroad.db "$DB_PATH"
        echo "[entrypoint] Seed complete."
    else
        echo "[entrypoint] Existing database found at $DB_PATH — skipping seed."
    fi
    # Also ensure img_cache dir exists on the persistent disk
    mkdir -p "${IMG_CACHE:-$DB_DIR/img_cache}"
fi

exec "$@"
