# Simulation — Standalone Data Generator

The simulation is a standalone Faker-based Python application that generates one day of messy Indonesian travel booking data across three mock source systems, maintaining a single shared customer identity pool (SQLite world state) so the same human appears across all sources.

## Architecture

```
                      config.yaml + env vars
                           │
                           ▼
                  ┌─────────────────┐
                  │  DailyGenerator  │  (gen/generator.py)
                  │   the engine     │
                  └───┬───────┬──────┘
                      │       │
         ┌────────────┤       ├────────────┐
         ▼            ▼       ▼            ▼
  ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
  │ WorldState│ │ App OLTP│ │Vendor API│ │  CRM SFTP  │
  │ (SQLite) │ │(Postgres│ │(SQLite)  │ │  (SFTP   │
  │ world.db  │ │customers│ │vendor.db │ │  JSON)    │
  │          │ │+ hotel  │ │flights + │ │ tickets_  │
  │ customers│ │bookings │ │experiences│ │YYYYMMDD.  │
  │ hotels   │ └─────────┘ └─────────┘ │   json     │
  │ airlines │                        └──────────┘
  │ airports │
  │ routes   │   ┌───────────────────┐
  │experiences│  │lib/id_locales.py │
  │ gen_log  │   │ static reference  │
  └──────────┘   │ data (ID domain)  │
                 └───────────────────┘
```

Four components:

| Component | File | Role |
|---|---|---|
| Static reference data | `lib/id_locales.py` | 54 hotels, 20 airlines, 34 airports, 55 domestic routes, 37 experiences, payment methods, CRM templates — all Indonesian |
| World state | `world/world.py` | SQLite DB managing shared customer identity, seed catalogues, and idempotency log |
| Generator engine | `gen/generator.py` | `DailyGenerator` — generates one day of data across all three mock sources |
| Mock sources | `sources/` | App OLTP (Postgres), Vendor API (FastAPI/SQLite), CRM SFTP (JSON files) |

## How it runs

The flow from `scripts/run_day.py --date YYYY-MM-DD`:

1. **Idempotency check** — `world.was_generated(date)` returns `True` if that day is already in `generation_log`; skip.
2. **Deterministic seeding** — `rng.seed(config.seed + md5(date))` so every run for a given date produces identical output.
3. **Volume split** — normal mode: random split across 4 domains within configured caps. Holiday mode: uses caps directly (max volume per domain).
4. **Generate** — calls `_generate_hotel_bookings()`, `_generate_flight_bookings()`, `_generate_experience_bookings()`, `_generate_crm_tickets()`.
5. **Identity resolution** — each generator method uses `world.get_or_create_customer()` to look up or create a shared customer record by email/phone, ensuring the same human appears across sources.
6. **Log completion** — writes a row to `generation_log` with row counts per domain.

## Component reference

| File | Role |
|---|---|
| `config.yaml` | Tuning knobs (seed, volume caps, error rates). Postgres credentials from env vars, config.yaml as local-dev fallback. |
| `requirements.txt` | `faker>=30`, `pyyaml>=6`, `click>=8`, `psycopg2-binary>=2.9` |
| `lib/id_locales.py` | Static reference data — provinces, cities, postal prefixes, phone prefixes, hotels, airlines, airports, domestic/international routes, experiences, payment methods, holidays, CRM ticket templates (Bahasa Indonesia). All Indonesian. |
| `world/world.py` | `WorldState` class — SQLite DB with tables: `customers`, `hotels`, `airlines`, `airports`, `experiences`, `generation_log`. Manages shared customer identity pool via `get_or_create_customer()` (lookup by email/phone, create if not found). Seeds catalogues on first run. |
| `gen/generator.py` | `DailyGenerator` class — the engine. Opens Postgres connection, SQLite vendor DB, and writes CRM ticket JSON files to the SFTP server directory. Provides `generate(date, holiday_mode)`. Four private generation methods, plus messiness helpers. |
| `sources/app_oltp/init/` | PostgreSQL DDL (`01-schema.sql`) and seed data (`02-seed.sql`). Tables: `customers`, `hotel_bookings`. |
| `sources/vendor_api/main.py` | FastAPI app serving `GET /flights?since=` and `GET /experiences?since=` from SQLite `vendor.db`. The Docker container for the mock vendor API. |
| `sources/crm_sftp/tickets/` | Directory where `tickets_YYYYMMDD.json` files land. Mimics SFTP upload. |
| `scripts/run_day.py` | CLI entry point: `--date YYYY-MM-DD [--holiday]`. One day. |
| `scripts/backfill.py` | CLI entry point: `--days N [--start YYYY-MM-DD] [--holiday]`. N days. Skips already-generated dates. |
| `scripts/reset.sh` | Wipes `world.db`, `vendor.db`, CRM JSON files, and truncates Postgres tables. |

## Data flow (step by step)

```
config.yaml + env vars
     │
     ▼
DailyGenerator.__init__()
     │
     ├─► WorldState (SQLite world.db) ─── shared customer identity pool
     │       • seed_data(): load hotels, airlines, airports, experiences
     │       • get_or_create_customer(): lookup by email/phone, create if new
     │       • get_random_existing_customers(): pick existing customers for repeat bookings
     │       • update_lifetime_value(): accumulate LTV per customer
     │       • get_random_hotel/airline/route/experience(): pick from catalogues
     │       • log_day(): idempotency tracking
     │       • was_generated(): skip already-generated dates
     │
     ├─► PostgreSQL (app_oltp) ─────────── customers + hotel_bookings
     │       • _upsert_app_customer(): SELECT by email/phone → UPDATE or INSERT
     │       • _generate_hotel_bookings(): ~40% of volume, 80% existing customers
     │       • DDL created automatically on first run
     │
     ├─► SQLite (vendor.db) ─────────────── flight_bookings + experience_bookings
     │       • _generate_flight_bookings(): ~30% of volume, domestic routes, IDR
     │       • _generate_experience_bookings(): ~20% of volume
     │       • Tables created automatically on first run
     │
     └─► CRM SFTP (tickets JSON) ─────────── tickets_YYYYMMDD.json
             • _generate_crm_tickets(): ~10% of volume, Bahasa Indonesia
             • Identity fragmentation: alternate emails/phones
             • Each file is an array of ticket objects, uploaded to SFTP
```

## Identity fragmentation

The same human appears across sources with different identifiers:

| Source | customer_id | email | phone |
|---|---|---|---|
| App OLTP (Postgres) | Yes | Yes | Yes |
| Vendor API (FastAPI) | No | Yes | No |
| CRM SFTP | No | Yes | Yes |

The world state (`customers` table) stores each resolved person with a canonical record containing `email`, `phone`, `alternate_email`, and `alternate_phone`. When the generator needs a customer for vendor API or CRM, it may use an alternate email/phone, creating deliberate identity drift:

- **Vendor API** uses `email` only. If a customer has an `alternate_email` set, the generator may use that instead, creating a booking that won't trivially match the app OLTP email.
- **CRM** uses both `email` and `phone`. It may use the canonical email and an alternate phone, or vice versa, or entirely different email+phone combos.
- **Phone bridging**: Because CRM has phone, it serves as the bridge — a CRM ticket with email `X` and phone `Y` can link vendor API bookings (email `X`) to app OLTP customers (phone `Y`), even when email `X` was never seen in app OLTP.

`get_or_create_customer()` resolves via a lookup chain: try phone match first (canonical or alternate), then case-insensitive email match.

## Messiness

Deliberate data problems injected into generated data, controlled by `config.yaml`:

| Problem | Rate | Mechanism |
|---|---|---|
| Phone format variation | ~88% of phones | Strip `+62`, insert/remove hyphens/spaces, `0` prefix drift, `000-000-0000` / `TIDAK ADA` sentinels |
| Email typos/aliases | ~10% | UPPERCASE, `gnail.com` / `gmaill.com`, `+alias` suffix, trailing whitespace |
| Name casing/honorifics | ~28% | ALL CAPS, all lowercase, `Bpk.` / `Ibu` / `Sdr.` prefix, first-name-only |
| Amount drift | by `error_rate` | ±1/50/100 IDR perturbation, phantom cents |
| Duplicate bookings | by `dupe_rate` | Near-identical re-insertion with ±Rp 1–100 difference |
| Nulls/sentinels | by `error_rate` | `TIDAK ADA`, `tidak diketahui`, `000-000-0000`, empty strings |
| Schema drift | year-based | 2022 lacks `loyalty_tier` and `preferred_airline`; 2024+ includes them |
| Date format drift | CRM output | Occasional Indonesian month abbreviations (`15 Agt 2024`) instead of ISO |
| Postcode/city mismatch | ~5% | City and postal code deliberately inconsistent |

## Configuration

All knobs in `simulation/config.yaml`:

| Key | Default | Description |
|---|---|---|
| `seed` | `42` | Deterministic reproducibility base seed |
| `locale` | `id_ID` | Faker locale for names, phones, addresses |
| `currency` | `IDR` | Currency code (never changes) |
| `daily_volume_min` | `0` | Floor for random volume split |
| `daily_volume_max` | `5000` | Ceiling for random volume split |
| `hotel_cap` | `2000` | Max hotel bookings per day (~40%) |
| `flight_cap` | `1500` | Max flight bookings per day (~30%) |
| `experience_cap` | `1000` | Max experience bookings per day (~20%) |
| `crm_cap` | `500` | Max CRM tickets per day (~10%) |
| `error_rate` | `0.03` | Probability of amount/phone/email/name corruption |
| `dupe_rate` | `0.005` | Probability of near-duplicate booking insertion |
| `drift_year` | `2024` | Reference year for schema drift decisions |
| `messiness_intensity` | `0.05` | General messiness multiplier |
| `holiday_mode` | `false` | When true, uses caps directly instead of random split |
| `world_db_path` | `simulation/world/world.db` | Path relative to repo root |
| `vendor_db_path` | `simulation/sources/vendor_api/store/vendor.db` | Path relative to repo root |

Credentials (Postgres, SFTP) are in `.env` only. On first run the Makefile auto-creates `.env` from `.env.example`. Never hardcode credentials — `docker-compose.yml` uses `${VAR}` substitution and the generator reads `os.getenv()`.

## Startup order (fresh clone)

```
make setup        # 1. creates .env (if missing), installs Python deps
make generator-up  # 2. Docker Compose reads .env → starts app_oltp, vendor_api, crm_sftp
make generate     # 3. runs generator, 3 sources populated
```

### Who reads `.env` and when

| Component | Reads `.env` | How |
|---|---|---|
| **Makefile** | Every `make` invocation | `-include .env` + `export` — loads vars, passes to child processes |
| **Docker Compose** | `docker compose up` | Auto-reads `.env` from cwd, substitutes `${POSTGRES_APP_USER}` etc. into YAML |
| **Python generator** | `run_day.py` / `backfill.py` | `os.getenv('POSTGRES_APP_USER')` — picks up vars exported by Make |

The chain: Makefile → `.env` → export → Docker Compose (for containers) + Python child process (for scripts).

**Always use `make generate`** — running `python scripts/run_day.py` directly will not see `.env` vars because nothing exports them into the shell session.

## Running

```bash
# Generate one travel day
make generate DATE=2026-07-15

# Generate one day with holiday volume spike
make generate DATE=2026-04-10 HOLIDAY=1

# Backfill N days (skips already-generated dates)
make backfill DAYS=365

# Backfill from a specific start date
make backfill DAYS=90 BACKFILL_START=2025-01-01

# Wipe all simulation state and artifacts
make reset
```

## Holiday mode

The `holiday_mode` knob simulates Indonesian seasonal travel spikes:

- **Lebaran / Idul Fitri** (Mar–May): 3x uplift, mudik travel pattern
- **Natal / Tahun Baru** (Dec–Jan): 2.5x uplift, holiday travel
- **Imlek** (Jan–Feb): 1.8x uplift, getaway bookings (especially Bali/Singapore)
- **Libur Sekolah** (Jun–Jul): 2x uplift, family bookings
- **Libur Sekolah** (December): 2.2x uplift, family bookings
- **Kemerdekaan RI** (August): 1.3x uplift, long-weekend travel
- **Waisak / Nyepi** (Mar–May): 1.4x uplift, cultural travel

When `--holiday` is passed (or `HOLIDAY=1` in make), the generator uses domain caps directly (`hotel_cap`, `flight_cap`, `experience_cap`, `crm_cap`) instead of the random volume split, simulating peak demand where every domain hits capacity.

The date itself determines which holiday uplift applies (via `id_locales.HOLIDAYS_SEASONAL` month ranges), but the `--holiday` flag is what enables the cap-based volume override.

## Output verification

**PostgreSQL (App OLTP):**

```bash
docker exec -i app_oltp psql -U app_user -d app_oltp -c \
  "SELECT date(booking_ts), count(*) FROM hotel_bookings GROUP BY 1 ORDER BY 1 DESC LIMIT 5;"

docker exec -i app_oltp psql -U app_user -d app_oltp -c \
  "SELECT count(*) FROM customers; SELECT count(*) FROM hotel_bookings;"
```

**SQLite (Vendor API):**

```bash
sqlite3 simulation/sources/vendor_api/store/vendor.db \
  "SELECT substr(booking_ts, 1, 10) as day, count(*) FROM flight_bookings GROUP BY 1 ORDER BY 1 DESC LIMIT 5;"

sqlite3 simulation/sources/vendor_api/store/vendor.db \
  "SELECT count(*) FROM flight_bookings; SELECT count(*) FROM experience_bookings;"
```

**CRM SFTP ticket JSON:**

```bash
ls simulation/sources/crm_sftp/tickets/
python3 -c "import json; d=json.load(open('simulation/sources/crm_sftp/tickets/tickets_20260715.json')); print(len(d), 'tickets')"
```

**World state (generation log):**

```bash
sqlite3 simulation/world/world.db \
  "SELECT date, total_rows, hotel_rows, flight_rows, experience_rows, crm_rows, is_holiday FROM generation_log ORDER BY date DESC LIMIT 10;"
```

**Via the vendor API (when Docker is up):**

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/flights?since=2026-07-01&limit=5" | python3 -m json.tool
```

## For Dagster consumers

The pipeline (Phase 2+) will read from each source as if it's a real production system:

- **Hotel bookings**: `SELECT * FROM hotel_bookings WHERE booking_ts >= '{incremental_cursor}'` from Postgres
- **Flight bookings**: `GET /flights?since={incremental_cursor}` from vendor API
- **Experience bookings**: `GET /experiences?since={incremental_cursor}` from vendor API
- **CRM tickets**: Pull `tickets_YYYYMMDD.json` from SFTP server via SFTP client

The Dagster pipeline orchestrates landing these into MinIO Parquet (no local files), then dbt silver/gold in ClickHouse. The simulation is standalone and never runs inside Dagster.
