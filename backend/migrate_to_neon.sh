#!/usr/bin/env bash
set -euo pipefail

LOCAL_DB_URL="${LOCAL_DB_URL:-postgresql://postgres:postgres@localhost:5432/trading_db}"
NEON_DB_URL="${NEON_DB_URL:-postgresql://neondb_owner:npg_GsX2EZMb0kPN@ep-bold-sunset-atkhla7e.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require}"
DUMP_FILE="${DUMP_FILE:-trading_db.dump}"

echo "==> Dumping local database..."
pg_dump -Fc -d "$LOCAL_DB_URL" -f "$DUMP_FILE"
echo "    Dump written to $DUMP_FILE ($(du -h "$DUMP_FILE" | cut -f1))"

echo "==> Restoring into Neon..."
pg_restore --no-owner --no-privileges --if-exists --clean \
  -d "$NEON_DB_URL" \
  "$DUMP_FILE"

echo "==> Done. Verifying table list on Neon..."
psql "$NEON_DB_URL" -c '\dt'

echo "==> Migration complete."
