#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIM_DIR="$(dirname "$SCRIPT_DIR")"
PROJ_DIR="$(dirname "$SIM_DIR")"

echo "Wiping simulation state and generated artifacts..."

rm -f "$SIM_DIR/world/world.db"

rm -f "$SIM_DIR/sources/vendor_api/store/vendor.db"
rm -f "$SIM_DIR/sources/vendor_api/store/vendor.db-wal"
rm -f "$SIM_DIR/sources/vendor_api/store/vendor.db-shm"

rm -f "$SIM_DIR/sources/crm_sftp/tickets/tickets_"*.json

if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'app_oltp'; then
            docker exec -i app_oltp psql -U "${POSTGRES_APP_USER:-RoyAndhika}" -d "${POSTGRES_APP_DB:-app_oltp}" \
                -c "TRUNCATE TABLE hotel_bookings, customers CASCADE;" 2>/dev/null || true
    fi
fi

touch "$SIM_DIR/sources/vendor_api/store/.gitkeep"
touch "$SIM_DIR/world/.gitkeep" 2>/dev/null || mkdir -p "$SIM_DIR/world" && touch "$SIM_DIR/world/.gitkeep"

echo "Reset complete."
