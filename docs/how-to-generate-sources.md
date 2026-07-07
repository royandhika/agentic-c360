# How to Generate Source Data

A step-by-step guide to producing realistic Indonesian retail data with the simulation generator. You do **not** need ClickHouse, MinIO, Spark, or Dagster — just Python 3.10+, Docker, and this repo.

All data is Indonesian: `id_ID` locale names, `+62` phones, Rupiah (`Rp`) currency, QRIS/COD/e-wallet payments, Bahasa Indonesia support tickets, and seasonal holiday spikes (Lebaran, Natal, Imlek).

---

## 1. Prerequisites

Check you have the right tools:

```bash
python3 --version
# Must be 3.10 or above

docker --version && docker compose version
# Both should print a version number
```

---

## 2. Install Python dependencies

```bash
cd /home/yor/e2e
pip install -r simulation/requirements.txt
```

If you prefer a virtual environment:

```bash
cd /home/yor/e2e
python3 -m venv venv && source venv/bin/activate
pip install -r simulation/requirements.txt
```

The required packages: `faker` (Indonesian locale), `pyyaml`, `click`, `psycopg2-binary`.

---

## 3. Start the infrastructure

This starts two containers — **nothing else**:

- **`postgres_crm`** — PostgreSQL 16 for mock CRM data (port 5432)
- **`mock_ecom_api`** — FastAPI mock e-commerce API (port 8000)

```bash
cd /home/yor/e2e
docker compose up -d
```

Wait a few seconds for Postgres to initialise, then verify:

```bash
docker compose ps
# Both services should show "running" or "healthy"
```

Test the e-commerce API is responding:

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

---

## 4. Generate one day of data

First, look at the config knobs (optional but helpful):

```bash
cat simulation/config.yaml
```

Key settings: `daily_volume_min`/`_max` (0–5000 rows/day total), per-source caps (`ecom_cap`, `pos_cap`, `crm_cap`), error/dupe rates, and `drift_year` for POS schema drift.

Now generate a single retail day:

```bash
cd /home/yor/e2e
PYTHONPATH=simulation:simulation/src python simulation/scripts/run_day.py --date 2024-08-15
```

What this does under the hood:

- Rolls a random daily volume (0–5000 rows) and randomly splits it across three sources
- E-commerce: writes JSON orders into the FastAPI app's SQLite store
- POS: drops a CSV file at `simulation/sources/inbox/pos/sales_20240815.csv` (deliberately **ISO-8859-1 encoded**, not UTF-8)
- CRM: inserts customers, tickets, and interactions into PostgreSQL

Verify the output:

```bash
# Check the e-commerce API now has data
curl "http://localhost:8000/orders?since=2024-08-15"

# Check the POS CSV was created
ls -la simulation/sources/inbox/pos/

# Check CRM data landed in Postgres
docker exec postgres_crm psql -U crm_user -d crm_mock -c "SELECT count(*) FROM customers;"
docker exec postgres_crm psql -U crm_user -d crm_mock -c "SELECT count(*) FROM tickets;"
```

---

## 5. Generate with holiday uplift

Holiday mode amplifies volume (up to 3× for Lebaran, 1.5×–2.5× for Natal/Imlek/Tahun Baru) and shifts the product mix to seasonal items (sarung, mukena, kue lebaran, baju kurung, etc.):

```bash
cd /home/yor/e2e
PYTHONPATH=simulation:simulation/src python simulation/scripts/run_day.py --date 2024-04-10 --holiday
```

The `--holiday` flag uses an internal Indonesian national-libur calendar to detect matching dates and applies the uplift automatically. Run it on any date — if it is not a holiday the flag is a no-op.

---

## 6. Backfill a year of history

Generate 365 days ending today. Each day is **idempotent** — re-running skips dates already generated:

```bash
cd /home/yor/e2e
PYTHONPATH=simulation:simulation/src python simulation/scripts/backfill.py --days 365
```

For a specific date range (e.g. 30 days starting 1 June 2024):

```bash
cd /home/yor/e2e
PYTHONPATH=simulation:simulation/src python simulation/scripts/backfill.py --days 30 --start 2024-06-01
```

---

## 7. Reset everything and start over

This wipes all generated state — the world database, all POS CSVs, the e-commerce SQLite store, and CRM Postgres tables:

```bash
cd /home/yor/e2e
bash simulation/scripts/reset.sh
```

After reset you are back to a clean slate. Data generated before reset is **gone for good** — there is no undo.

---

## 8. Stop the infrastructure

```bash
cd /home/yor/e2e
docker compose down
```

Add `-v` to also remove the Postgres data volume (forces a fresh DB next time you start):

```bash
docker compose down -v
```

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'faker'` | Dependencies not installed | `pip install -r simulation/requirements.txt` |
| `psycopg2 not found` | Missing PostgreSQL driver | `pip install psycopg2-binary` (included in requirements.txt) |
| `postgres_crm` not running | Docker not started that service | `docker compose up -d postgres_crm` |
| `Cannot connect to CRM` / `Connection refused on port 5432` | Postgres needs ~5s to initialise on first start | Wait and retry; check `docker compose ps` for "healthy" |
| `No CSV files in pos/` | Low daily volume rolled a zero-volume day | Check `simulation/config.yaml` `daily_volume_min`; try again on a different date |
| `orders?since=...` returns `[]` | No orders generated for that date yet | Run `run_day.py --date` for that date first |
| Port 5432 or 8000 already in use | Another Postgres or server is running locally | Stop the conflicting service first, or change the port in `docker-compose.yml` |
| Reset script says "postgres_crm not running" | Container is down | It's harmless — the script still removes files. Start Docker before the next `run_day.py` |
| `docker compose: command not found` | Old Docker version | Use `docker-compose` (with hyphen) instead, or upgrade Docker |
