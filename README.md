# agentic-c360

End-to-end Customer 360 pipeline with agentic AI analytics for Indonesian omnichannel retail.

## What it does

Ingests intentionally messy multi-source retail data (POS CSV, e-commerce API, CRM Postgres), resolves customer identities across phone/email silos, builds dimensional models in ClickHouse, and serves an AI-powered analytics dashboard via Streamlit. Every piece of data is Indonesian — names, phones, addresses, IDR currency, and Bahasa Indonesia support tickets.

## Architecture

```
 simulation (cron)
      |
 mock sources                   agentic/AI layer
 +--+---+----+                 (query, explain,
 | Ecom | POS | CRM |           recommend, alert)
 +--+---+----+---+--+                |
      |          |                   |
  Dagster     Sling        Streamlit dashboard
      |          |                   ^
      v          v                   |
  MinIO Parquet (Bronze)        dbt gold
      |                    (fact_transactions,
      v                     dim_customer)
  dbt silver                       |
  (cleanse, normalize)             |
      |                            |
      +--> ClickHouse <------------+
```

## Project structure

```
agentic-c360/
  plan.md                         # Architecture source of truth
  AGENTS.md                       # Agent conventions and gotchas
  Makefile                        # Common tasks (setup, generate, backfill, reset)
  docker-compose.yml              # Mock sources (Postgres CRM, e-commerce API)
  .env.example                    # Environment variable template
  simulation/                     # Standalone data generator (cron/script driven)
    config.yaml                   # SEED, volume, error/dupe/drift knobs
    gen/                          # Faker-based daily generator (id_ID locale)
    src/                          # Shared simulation library
    sources/                      # Three mock source implementations
      ecommerce_api/              # FastAPI app serving JSON orders
      pos_csv/                    # Daily CSV writer (ISO-8859-1 encoded)
      postgres_crm/               # Postgres seed + daily inserter
    scripts/
      backfill.py                 # Generate N days of history
      run_day.py                  # Generate one retail day
      reset.sh                    # Wipe world state + artifacts
    world/                        # Persistent world state (SQLite)
  dagster_pipeline/               # (planned) Land -> MinIO Parquet orchestration
  dbt/                            # (planned) Silver cleanse + Gold dims/facts
  streamlit_app/                  # (planned) Customer 360 dashboard
  ops/                            # (planned) dbt profiles, ClickHouse init SQL
  docs/                           # Documentation
  .agents/                        # Agent skills and configuration
```

## Getting started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- `make`

### Setup

```bash
# Install Python deps and create venv
make setup

# Start mock sources (Postgres CRM, e-commerce API)
make infra-up
```

### Generate simulated history

```bash
# Generate one retail day
make generate DATE=2024-08-15

# Generate a day with holiday volume spike (Lebaran/Natal/Imlek)
make generate DATE=2024-04-10 HOLIDAY=1

# Backfill a full year of data
make backfill DAYS=365

# Backfill with a specific start date
make backfill DAYS=90 BACKFILL_START=2024-01-01
```

### Planned steps (not yet implemented)

```bash
# Start pipeline infrastructure (Dagster, MinIO, ClickHouse)
docker compose -f docker-compose.pipeline.yml up -d

# Run Dagster landing pipeline (Bronze -> MinIO Parquet)
dagster dev -m dagster_pipeline

# Run dbt transformations (Silver -> Gold in ClickHouse)
dbt run --profiles-dir ops/

# Launch Customer 360 dashboard
streamlit run streamlit_app/app.py
```

### Cleanup

```bash
make reset        # Wipe simulation state and generated artifacts
make infra-down   # Stop mock source containers
make clean        # Remove venv
```

## Tech stack

| Layer            | Technology                                                 |
|------------------|------------------------------------------------------------|
| Orchestration    | Dagster                                                    |
| Transformation   | dbt (SQL) + Pandas (in-memory landing)                     |
| Landing          | MinIO (S3-compatible), Parquet                             |
| Warehouse        | ClickHouse                                                 |
| Visualization    | Streamlit                                                  |
| Sources (mock)   | FastAPI (e-commerce), CSV (POS), Postgres + Sling (CRM)    |
| Simulation       | Python, Faker (`id_ID`), SQLite/DuckDB                     |
| AI / agentic     | LLM-powered query, explain, and alert layer over ClickHouse |

## Roadmap

| Phase | Deliverable                                                        |
|-------|--------------------------------------------------------------------|
| 0     | Infra — docker-compose for MinIO, ClickHouse, Postgres, Dagster    |
| 1     | Simulation — world state, Faker generator, three mock sources      |
| 2     | Landing (Bronze) — Dagster ops extract each source to MinIO Parquet |
| 3     | Silver — dbt models: phone/email, date/money, nulls, dedupe        |
| 4     | Gold — fact_transactions + dim_customer with entity resolution      |
| 5     | Serving — Streamlit Customer 360; CLV + loyalty tiers              |
| 6     | Daily run — cron for simulation, Dagster schedule for pipeline      |

## Indonesian data

All generated data reflects Indonesian retail reality: `id_ID` Faker locale for names (including Balinese birth-order and single-name elders), `+62`/`08` phone formats, full RT/RW/kelurahan/kota/provinsi addresses, IDR currency (Rp with dot-thousand separator), QRIS/COD/GoPay/OVO/Bank Transfer payment methods, Bahasa Indonesia CRM ticket bodies, and Lebaran/Natal/Imlek/Tahun Baru seasonal spikes. Source systems inject deliberate messiness — encoding drift, schema drift, name-spelling variation, and identity fragmentation — to test real-world entity resolution.

## Design constraint: simulation is standalone

The **simulation** is standalone, driven by cron or manual scripts (`run_day.py`, `backfill.py`). Dagster does not run the generator. Dagster orchestrates only the landing pipeline: extract from mock sources, land Parquet in MinIO, and trigger dbt → ClickHouse → Streamlit. Putting the generator inside Dagster is a design error.
