# WanderFuel Customer 360

**Agent-powered customer analytics platform for an Indonesian travel companion startup.**

---

## The Story

As Head of Data at WanderFuel, my first major initiative was simple on paper: answer the question "who are our most valuable customers?" It took six weeks to discover why nobody had answered it before.

WanderFuel's booking data lives in three completely separate systems. Our app database knows our hotel guests by `customer_id`, email, and phone — but it only sees hotel bookings. Our vendor partner API — the one that supplies flights and experiences — identifies everyone by email alone. No customer_id. No phone. And our third-party CRM tool, where all the support tickets land, has both email and phone but with yet another layer of identity fragmentation: the support email often doesn't match the booking email.

Ibu Siti Nurhaliza from Surabaya booked a hotel through our app, a Garuda flight through the vendor, a cooking class in Ubud, and then opened a CRM ticket because her flight was delayed. Four events. One human. Three different identifiers across our systems. Zero ability to link them.

The board wanted a Customer 360 dashboard showing lifetime value, booking history, and loyalty tiers. What we had instead was three spreadsheets and a prayer.

This repository is the answer. An end-to-end data pipeline that ingests intentionally messy travel booking data from three simulated sources, resolves fragmented customer identities, builds dimensional models in ClickHouse, and serves everything through a Streamlit dashboard — with an agentic AI analytics layer on the roadmap. The simulation is standalone, generating a shared world with realistic Indonesian travel data across all sources. Dagster orchestrates the landing→cleansing→modeling→serving pipeline. Everything is Indonesian: names, phones, addresses, IDR currency, domestic flight routes, Bahasa support tickets, and Lebaran/Natal seasonal spikes.

## Architecture

```
                                     ┌─────────────────────────────────┐
                                     │      LangChain AI (Phase 6)      │
                                     │  query | explain | recommend     │
                                     └─────────────┬───────────────────┘
                                                   │
  ┌──────────────────┐                             │
  │   SIMULATION     │                             │
  │   (standalone)   │                             ▼
  │                  │              ┌──────────────────────────┐
  │  shared world    │              │    Streamlit C360        │
  │  (SQLite)        │              │    (Bahasa/bilingual)    │
  │                  │              └────────────┬─────────────┘
  │  ┌────────────┐  │                           │
  │  │ App OLTP    │──┼──┐     ┌──────────────────▼──────────┐
  │  │ (Postgres)  │  │  │     │     ClickHouse (Gold)        │
  │  └────────────┘  │  │     │  fact_bookings + dim_customer │
  │  ┌────────────┐  │  │     └──────────────┬───────────────┘
  │  │ Vendor API  │──┼──┼─┐                   │
  │  │ (FastAPI)   │  │  │ │   ┌───────────────▼──────────────┐
  │  └────────────┘  │  │ │   │      dbt Silver (cleanse)     │
  │  ┌────────────┐  │  │ │   │  phones/emails/dates/money    │
  │  │ CRM SFTP      │──┼──┼─┼─┐ └──────────────┬───────────────┘
  │  │ (SFTP)│  │  │ │ │                  │
  │  └────────────┘  │  │ │ │  ┌───────────────▼──────────────┐
  └──────────────────┘  │ │ │  │   MinIO Parquet (Bronze)     │
                        │ │ │  └──────────────┬───────────────┘
                        ▼ ▼ ▼                 │
                   ┌──────────────────────────▼──────────────┐
                   │          Dagster (orchestration)         │
                   │        land → silver → gold → serve       │
                   └─────────────────────────────────────────┘
```

## Project Structure

```
agentic-c360/
  STORY.md                        # Project backstory (read this first)
  plan.md                         # Architecture source of truth
  AGENTS.md                       # Agent conventions and gotchas
  README.md                       # This file
  Makefile                        # Common tasks (setup, generate, backfill, reset)
  docker-compose.yml              # Mock sources (Postgres app OLTP, vendor API)
  docker-compose.orchestrator.yml     # MinIO, ClickHouse, Dagster
  .env.example                    # Environment variable template
  simulation/                     # Standalone data generator (cron/script driven)
    config.yaml                   # SEED, volume, error/dupe/drift knobs
    world/                        # Persistent world state (SQLite)
    gen/                          # Faker-based daily generator (id_ID locale)
    lib/                          # Shared simulation library
    sources/
      app_oltp/                   # PostgreSQL seed + daily inserter
      vendor_api/                 # FastAPI app serving JSON bookings
      crm_sftp/                     # SFTP JSON writer (daily ticket exports)
    scripts/
      backfill.py                 # Generate N days of travel history
      run_day.py                  # Generate one travel day
      reset.sh                    # Wipe world state + artifacts
  dagster_pipeline/               # Land → MinIO Parquet orchestration
  dbt/                            # (planned) Silver cleanse + Gold dims/facts
  streamlit_app/                  # (planned) Customer 360 dashboard
  ops/                            # (planned) dbt profiles, ClickHouse init SQL
  docs/                           # Documentation
  .agents/                        # Agent skills and configuration
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- `make`

### Credentials

ALL credentials MUST be set in the `.env` file. No hardcoded credentials, secrets, API keys, or passwords are permitted anywhere in the codebase. See `.env.example` for required variables.

### Setup

```bash
# Install Python deps and create venv
make setup

# Start mock sources (Postgres app OLTP, vendor API)
make generator-up
```

### Generate Simulated History

```bash
# Generate one travel day
make generate DATE=2024-08-15

# Generate a day with holiday volume spike (Lebaran/Natal/Imlek)
make generate DATE=2024-04-10 HOLIDAY=1

# Backfill a full year of data
make backfill DAYS=365

# Backfill with a specific start date
make backfill DAYS=90 BACKFILL_START=2024-01-01
```

### Pipeline Infrastructure (Phase 2+)

```bash
# Start all containers (simulation sources + pipeline)
make orchestrator-up

# Stop all containers
make orchestrator-down
```

### Dashboard & Transformations (Future Phases)

```bash
# Run dbt transformations (Silver → Gold in ClickHouse)
dbt run --profiles-dir ops/

# Launch Customer 360 dashboard
streamlit run streamlit_app/app.py
```

### Cleanup

```bash
make reset        # Wipe simulation state and generated artifacts
make generator-down   # Stop mock source containers
make clean        # Remove venv
```

## Data Domains

### App OLTP (PostgreSQL)

The internal WanderFuel app database. The only source with complete customer identity. Contains `customers` (customer_id, email, phone, full_name, address) and `hotel_bookings` (linked via customer_id FK). Covers ~40% of daily booking volume. Hotels span Indonesian tourist destinations: Bali (Kuta, Seminyak, Ubud, Canggu), Yogyakarta, Bandung, Lombok, Labuan Bajo, Jakarta, Surabaya.

### Vendor API (FastAPI)

External partner supplying flights and experiences inventory. Two endpoints: `/flights` (flight_bookings) and `/experiences` (experience_bookings). Keyed by email only — no customer_id, no phone. Covers ~50% of daily volume. Airlines include Garuda, Lion Air, Citilink, Batik Air, AirAsia Indonesia. Routes are domestic (CGK-DPS, SUB-CGK, KNO-CGK) with some regional/international. Experiences cover cooking classes, dive trips, volcano treks, temple tours, snorkelling, and surfing lessons.

### CRM SFTP

Third-party CRM vendor drops daily JSON ticket exports via SFTP. Each file contains support interactions with both email and phone — the identity bridge. Ticket bodies in Bahasa Indonesia. Covers ~10% of daily volume. Support-ticket emails often differ from booking emails across the other sources.

### Identity Resolution Challenge

| Source | customer_id | email | phone |
|---|---|---|---|
| App OLTP (Postgres) | Yes | Yes | Yes |
| Vendor API (FastAPI) | No | Yes | No |
| CRM SFTP | No | Yes | Yes |

The pipeline resolves identity by matching email and normalized phone (`+62...`) across sources:

1. App OLTP provides the anchor — each `customer_id` has verified email and phone.
2. Vendor API bookings are resolved by matching email to known app OLTP customers.
3. CRM tickets are resolved by matching email or phone.
4. Phone bridging: if a vendor API email doesn't match directly, but a CRM ticket with that email also has a phone that matches a known customer → link via phone.
5. Unresolved customers get a placeholder ID; they may be resolved later when new identity data arrives.

## Tech Stack

| Layer | Technology |
|---|---|
| Simulation | Python, Faker (`id_ID`), SQLite (world state) |
| Source Systems | PostgreSQL (app OLTP), FastAPI/SQLite (vendor API), SFTP (CRM) |
| Orchestration | Dagster |
| Landing | MinIO (S3-compatible), Parquet |
| Transformation | dbt (SQL) + Pandas (in-memory landing) |
| Warehouse | ClickHouse |
| Visualization | Streamlit |
| AI / Agentic | LangChain + LLM (Phase 6) |

## Roadmap

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Infra — docker-compose for MinIO, ClickHouse, Postgres, Dagster, vendor API | Done |
| 1 | Simulation — world state, Faker generator, three mock sources, backfill | Done |
| 2 | Landing (Bronze) — Dagster assets extract each source to MinIO Parquet | Done |
| 3 | Silver — dbt models: phone/email, date/money, nulls, dedupe | — |
| 4 | Gold — fact_bookings + dim_customer with entity resolution in ClickHouse | — |
| 5 | Serving — Streamlit Customer 360; CLV + loyalty tiers (Gold/Silver/Churn-Risk) | — |
| 6 | AI — LangChain agent over ClickHouse for query, explain, recommend | — |

## Indonesian Data

All generated data reflects Indonesian travel reality. The `id_ID` Faker locale produces Indonesian names (including Balinese birth-order names like Wayan/Made/Nyoman/Ketut, Muslim names, and single-name elders), `+62`/`08` phone formats, full RT/RW/kelurahan/kota/provinsi addresses, and Indonesian-patterned emails.

Currency is always IDR (Rupiah). Booking amounts range from Rp 100.000 (budget experience) to Rp 15.000.000+ (international business-class flights). Payment methods cover the Indonesian mobile-first landscape: QRIS, GoPay, OVO, DANA, ShopeePay, LinkAja, COD, and Bank Transfer (BCA, Mandiri, BRI, BNI).

Travel patterns are domestic-dominant: CGK-DPS (Jakarta-Bali), SUB-CGK, KNO-CGK, UPG-DPS, CGK-JOG, with some regional/international routes. Hotels cluster in tourist destinations across Bali, Yogyakarta, Lombok, and Labuan Bajo. Support tickets are in Bahasa Indonesia covering real travel issues: flight delays, hotel mismatches, refund requests, date changes.

Seasonal spikes model real Indonesian travel behaviour: Lebaran (mudik travel surge), Natal dan Tahun Baru (holiday travel), Imlek (getaway bookings), and school holiday periods (Juni-Juli, Desember) where family bookings spike 3-5x.

The simulation injects deliberate messiness — encoding drift, schema drift across years, name-spelling variation, phone format inconsistency, email typos and aliases, date format variations, and identity fragmentation — to test real-world entity resolution.

## Design Constraint: Simulation is Standalone

The **simulation** is standalone, driven by cron or manual scripts (`run_day.py`, `backfill.py`). Dagster does not run the generator. Dagster orchestrates only the landing pipeline: extract from mock sources, land Parquet in MinIO, and trigger dbt → ClickHouse → Streamlit. Putting the generator inside Dagster is a design error.
