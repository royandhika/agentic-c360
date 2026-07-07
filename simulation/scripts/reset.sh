#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIM_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Resetting simulation state ==="

# 1. Remove world database
if [ -f "$SIM_DIR/world/world.db" ]; then
    rm -f "$SIM_DIR/world/world.db"
    echo "  - Removed world/world.db"
fi

# 2. Remove generated POS CSVs
if [ -d "$SIM_DIR/sources/inbox/pos" ]; then
    rm -f "$SIM_DIR/sources/inbox/pos/sales_*.csv"
    echo "  - Removed POS CSV files"
fi

# 3. Remove ecommerce SQLite store
if [ -f "$SIM_DIR/sources/ecommerce_api/store/ecom_store.db" ]; then
    rm -f "$SIM_DIR/sources/ecommerce_api/store/ecom_store.db"
    echo "  - Removed ecom_store.db"
fi

# 4. Truncate CRM Postgres (if accessible)
if command -v docker &> /dev/null && docker ps --format '{{.Names}}' 2>/dev/null | grep -q postgres_crm; then
    docker exec postgres_crm psql -U crm_user -d crm_mock -c "
        TRUNCATE interactions, tickets, customers CASCADE;
    " 2>/dev/null && echo "  - Truncated CRM Postgres tables" || echo "  - (CRM Postgres truncate skipped — container may not be running)"
else
    echo "  - (CRM Postgres truncate skipped — docker not available or postgres_crm not running)"
fi

# 5. Recreate ecom store directory with .gitkeep
mkdir -p "$SIM_DIR/sources/ecommerce_api/store"
touch "$SIM_DIR/sources/ecommerce_api/store/.gitkeep"

echo "=== Reset complete ==="
