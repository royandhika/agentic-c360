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

if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'app_oltp'; then
        docker exec -i app_oltp psql -U app_user -d app_oltp \
            -c "TRUNCATE TABLE hotel_bookings, customers CASCADE;" 2>/dev/null || true
    fi
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'crm_sftp'; then
        docker exec -i crm_sftp sh -c "rm -f /home/crm_vendor/tickets/*.json" 2>/dev/null || true
    fi
fi

touch "$SIM_DIR/sources/vendor_api/store/.gitkeep"
touch "$SIM_DIR/world/.gitkeep" 2>/dev/null || mkdir -p "$SIM_DIR/world" && touch "$SIM_DIR/world/.gitkeep"

echo "Reset complete."
