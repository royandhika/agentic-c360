# WanderFuel Customer 360

**End-to-end customer analytics platform with entity resolution, CLV scoring, and agentic AI — built for an Indonesian travel startup.**

---

## The Story

As Head of Data at WanderFuel, my first major initiative was simple on paper: answer the question "who are our most valuable customers?" It took six weeks to discover why nobody had answered it before.

WanderFuel's booking data lives in three completely separate systems. Our app database knows our hotel guests by `customer_id`, email, and phone — but it only sees hotel bookings. Our vendor partner API — the one that supplies flights and experiences — identifies everyone by email alone. No customer_id. No phone. And our third-party CRM tool, where all the support tickets land, has both email and phone but with yet another layer of identity fragmentation: the support email often doesn't match the booking email.

Ibu Siti Nurhaliza from Surabaya booked a hotel through our app, a Garuda flight through the vendor, a cooking class in Ubud, and then opened a CRM ticket because her flight was delayed. Four events. One human. Three different identifiers across our systems. Zero ability to link them.

The board wanted a Customer 360 dashboard showing lifetime value, booking history, and loyalty tiers. What we had instead was three spreadsheets and a prayer.

This repository is the answer. An end-to-end data pipeline that ingests intentionally messy travel booking data from three simulated sources, resolves fragmented customer identities, builds dimensional models and CLV/churn analytics in ClickHouse, and serves everything through a Streamlit dashboard — with an agentic AI analytics layer on the roadmap. The simulation is standalone, generating a shared world with realistic Indonesian travel data across all sources. Dagster orchestrates the landing→cleansing→modeling→serving pipeline. Everything is Indonesian: names, phones, addresses, IDR currency, domestic flight routes, Bahasa support tickets, and Lebaran/Natal seasonal spikes.

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
  └──────────────────┘  │ │ │  │ ClickHouse Bronze (MergeTree)│
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
  STORY.md                           # Project backstory (read this first)
  plan.md                            # Architecture source of truth
  AGENTS.md                          # Agent conventions and gotchas
  README.md                          # This file
  Makefile                           # Full lifecycle: setup, generate, backfill, orchestrator, dbt, app
  docker-compose.yml                 # Mock sources (Postgres app OLTP, vendor API, SFTP CRM)
  docker-compose.orchestrator.yml    # ClickHouse + Dagster webserver + daemon
  docker-compose.serving.yml         # Streamlit Customer 360 dashboard
  .env.example                       # Environment variable template
  .env                               # Credentials (gitignored)
  simulation/                        # Standalone data generator (cron/script driven)
    config.yaml                      # SEED, volume, error/dupe/drift knobs
    world/                           # Persistent world state (SQLite)
    gen/                             # Faker-based daily generator (id_ID locale)
    lib/                             # Shared simulation library (provinces, cities, routes, hotels)
    sources/
      app_oltp/init/                 # Postgres schema + seed SQL
      vendor_api/main.py             # FastAPI app with /flights and /experiences endpoints
      crm_sftp/tickets/              # SFTP JSON writer (daily ticket exports)
    scripts/
      backfill.py                    # Generate N days of travel history
      run_day.py                     # Generate one travel day
      reset.sh                       # Wipe world state + artifacts
  dagster_pipeline/                  # Dagster assets + resources + definitions
    dagster_pipeline/
      assets/
        app_oltp.py                  # bronze_customers + bronze_hotel_bookings (+ checks)
        vendor_api.py                # bronze_flights + bronze_experiences (+ checks)
        crm_sftp.py                  # bronze_tickets (+ checks)
        _helpers.py                  # schema ensure, partition truncate, insert/read bronze
      bronze_schema.sql              # 5 MergeTree tables partitioned by ingest_date
      dbt_assets.py                  # Silver → Gold dbt orchestration in Dagster
      resources.py                   # PostgresResource, VendorApiResource, SFTPSourceResource, ClickHouseResource
      definitions.py                 # Asset + check + resource wiring
  dbt/                               # Silver cleanse + Gold dims/facts/marts
    macros/
      bronze_table.sql               # Partition-filtered bronze subquery
      normalize_email.sql            # Lowercase, trim, typo fixes
      normalize_phone.sql            # Indonesian +62 E.164 normalization
      normalize_amount_idr.sql       # IDR cleansing (strip Rp, thousand dots, decimals)
      strip_honorifics.sql           # Remove Bpk/Ibu/Sdr/etc. prefixes
    models/
      bronze/
        schema.yml
      silver/
        silver_customers.sql         # App OLTP → cleansed customers (email, phone, name, address)
        silver_hotel_bookings.sql    # App OLTP → cleansed hotel bookings
        silver_flight_bookings.sql   # Vendor API → cleansed flight bookings
        silver_experience_bookings.sql # Vendor API → cleansed experience bookings
        silver_tickets.sql           # CRM SFTP → cleansed support tickets
        schema.yml
      gold/
        dim_customer.sql             # Resolved customer identity across all 3 sources
        fact_bookings.sql            # Unified booking fact (hotel + flight + experience)
        mart_customer_clv.sql        # CLV, churn risk score, loyalty tier, recommended action
        mart_route_monthly.sql       # Monthly route/ destination with holiday windows
        schema.yml
    tests/                           # dbt custom assertion tests (email valid, phone E.164, amount positive)
  streamlit_app/                     # Customer 360 dashboard (port 8501)
    queries/                         # ClickHouse SQL modules (executive, customer, 360, routes, AI templates)
    components/                      # Reusable UI: KPI cards, identity panel, booking timeline, ticket list, map
    pages/                           # 5 pages: Executive, Explorer, Customer 360, Route Analytics, AI Assistant
    data/id_cities.csv               # 72 Indonesian cities with lat/lng for the route map
    config.py                        # ClickHouse connection singleton (env vars only)
    labels.py                        # Label dictionary (English; bilingual-ready)
    format.py                        # IDR, phone, tier/status badge formatters
    tests/                           # format unit tests + live ClickHouse smoke tests
  ops/                               # dbt profiles.yml (ClickHouse connection)
  docs/                              # Documentation
  .agents/                           # Agent skills and configuration
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

### Start the Full Pipeline

Startup order matters: mock sources → pipeline infra → dashboard.

```bash
# 1. Start mock sources (Postgres, vendor API, SFTP CRM)
make generator-up

# 2. Start pipeline infrastructure (ClickHouse + Dagster)
make orchestrator-up

# 3. Start Customer 360 dashboard (Streamlit on port 8501)
make app-up
```

### Generate Data & Run Transformations

```bash
# Generate one travel day (after sources are up)
make generate DATE=2026-07-01

# Backfill a year of history
make backfill DAYS=365

# With holiday spike (Lebaran, Natal, Imlek, school holidays)
make generate DATE=2026-04-10 HOLIDAY=1

# Run all dbt models (Silver → Gold) inside the Dagster container
make dbt-build
```

### Stop Everything

```bash
make app-down           # Stop dashboard
make orchestrator-down  # Stop ClickHouse + Dagster
make generator-down     # Stop mock sources

# Or wipe everything (volumes, venv, generated data):
make generator-clean
make orchestrator-clean
```

## Data Domains

### Bronze Layer (Landing)

Dagster assets extract each source daily and land rows directly into 5 ClickHouse bronze tables (MergeTree, partitioned by `ingest_date`). No intermediate files — pandas DataFrames flow via PyArrow directly to ClickHouse.

| Bronze Table | Source | Primary Key |
|---|---|---|
| `bronze_customers` | App OLTP (Postgres) | `customer_id` |
| `bronze_hotel_bookings` | App OLTP (Postgres) | `booking_id` |
| `bronze_flights` | Vendor API (FastAPI) | `booking_ref` |
| `bronze_experiences` | Vendor API (FastAPI) | `booking_ref` |
| `bronze_tickets` | CRM SFTP | `ticket_id` |

### Silver Layer (Cleansing)

dbt incremental models cleanse the raw bronze data. Each silver table is a 1:1 cleansed counterpart of its bronze source.

| Silver Table | Cleansing Applied |
|---|---|
| `silver_customers` | `normalize_email`, `normalize_phone` (E.164 +62), `strip_honorifics`, city/province TitleCase |
| `silver_hotel_bookings` | `normalize_amount_idr` (strip Rp/dots/decimals, round), payment method normalization, status translation (batal→cancelled) |
| `silver_flight_bookings` | Same money/payment/status cleansing; IATA codes uppercased; passenger names stripped |
| `silver_experience_bookings` | Same cleansing; participants coalesced to 1 when missing |
| `silver_tickets` | `normalize_email`, `normalize_phone`, `strip_honorifics`, mojibake character stripping (Bahasa content) |

dbt macros shared across all models: `bronze_table()` (partition-filtered bronze read), `normalize_email()`, `normalize_phone()`, `normalize_amount_idr()`, `strip_honorifics()`.

### Gold Layer (Dimensional Models + Marts)

| Gold Table | Purpose | Key Fields |
|---|---|---|
| `dim_customer` | Resolved customer identity across all 3 sources via email/phone bridge | `resolved_customer_id`, `emails[]`, `phones[]`, `source_customer_ids[]`, `source_systems[]`, `identity_confidence` (high/phone_bridge/email), `clv_idr`, `loyalty_tier` (gold/silver/churn_risk), `dormant_days` |
| `fact_bookings` | Unified booking fact across hotel + flight + experience | `booking_id`, `resolved_customer_id`, `booking_type`, `provider`, `city`, `origin→destination` (flights), `amount_idr`, `status`, `seat_class`, `guests`/`participants` |
| `mart_customer_clv` | Per-customer CLV, churn score, support health, recommended action | `clv_idr`, `aov_idr`, `churn_risk_score` (0–1 weighted: CLV + dormancy + cancellations + critical tickets), `has_support_ticket`, `critical_ticket_count`, `avg_resolution_hours`, `distinct_booking_types`, `recommended_action` (retain/reengage/cross_sell/reactivate) |
| `mart_route_monthly` | Monthly route/destination aggregation with holiday flags | `route_key` (ORIG-DEST or city), `year_month`, `booking_count`, `unique_travelers`, `amount_idr_total/avg`, `cancel_rate`, `no_show_rate`, `business_class_share`, `holiday_window` (lebaran/natal/imlek/school/none) |

**Loyalty tier bands (IDR):** Gold ≥ Rp 10.000.000 CLV, Silver Rp 2.000.000–9.999.999, Churn‑Risk < Rp 2.000.000 or dormant > 90 days.

**Churn risk formula:** 0.40 × CLV factor + 0.40 × dormancy factor + 0.15 × cancel/no-show ratio + 0.05 × critical tickets factor. Score ≥ 0.7 → `reactivate`; single-category booker → `cross_sell`; gold + low risk → `retain`; else → `reengage`.

### Streamlit Dashboard (Serving)

Five-page Customer 360 dashboard at `http://localhost:8501`:

| Page | Audience | Content |
|---|---|---|
| **Executive Overview** | CEO / Head of Data | 5 KPI cards (total customers, avg CLV, revenue, churn risk %, open tickets), identity resolution funnel, tier mix donut, revenue by type, monthly trend, top destinations, Indonesia route map (72 cities), top 10 customers |
| **Customer Explorer** | Ops / Account Managers | Searchable table of `mart_customer_clv` with filters (tier, churn score, recommended action, booking type range, omnichannel toggle), 10+ sortable columns, click → Customer 360 drill-down |
| **Customer 360** | Deep dive | Identity resolution panel (emails, phones, source systems, confidence), booking timeline (Plotly scatter by date/amount), recent bookings table, support tickets (expandable, Bahasa body), booking-type gap analysis, churn gauge, recommended action card |
| **Route Analytics** | Revenue / Product team | Top routes/destinations table, monthly trend lines, holiday-window comparison (Lebaran/Natal/Imlek/school), business-class share ranking, Indonesia map scoped to filtered route type |
| **AI Assistant** | Phase 6 placeholder | Reserved chat UI with disabled input ("Coming in Phase 6"), AI hook containers wired into Executive and Customer 360 pages |

All charts use Plotly (dark theme). Labels are English (bilingual-ready via `labels.py`). IDR formatted with dot-thousand separator (`Rp X.XXX.XXX`). No credentials hardcoded — ClickHouse connection reads from `.env`.

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
| Orchestration | Dagster (assets + checks + DailyPartitionsDefinition + BackfillPolicy) |
| Landing | ClickHouse bronze (MergeTree, pyarrow → insert_arrow, partitioned by `ingest_date`) |
| Cleansing | dbt Silver (5 incremental models, 5 macros, 11 custom assertion tests) |
| Modeling | dbt Gold (dim_customer, fact_bookings, mart_customer_clv, mart_route_monthly) |
| Warehouse | ClickHouse (wanderfuel database) |
| Entity Resolution | Email/phone bridge with confidence scoring (high/phone_bridge/email) |
| Quant Analytics | CLV (IDR), churn risk scoring (weighted 0–1), loyalty tiers (Gold/Silver/Churn-Risk), customer AOV, route holiday seasonality |
| Visualization | Streamlit 1.59 (5 pages, Plotly dark theme, mapbox Indonesia route map) |
| AI / Agentic | LangChain + LLM (Phase 6 — placeholder UI slots built, no LLM integration yet) |

## Roadmap

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Infra — docker-compose for ClickHouse, Postgres, Dagster, vendor API | ✅ Done |
| 1 | Simulation — world state, Faker generator, three mock sources, backfill | ✅ Done |
| 2 | Landing (Bronze) — Dagster assets extract each source to ClickHouse bronze tables | ✅ Done |
| 3 | Silver — dbt models: phone/email, date/money, nulls, dedupe, 5 macros, 11 assertion tests | ✅ Done |
| 4 | Gold — dim_customer (entity resolution), fact_bookings (unified), mart_customer_clv (CLV/churn/tier), mart_route_monthly (seasonality) | ✅ Done |
| 5 | Serving — Streamlit Customer 360 (5 pages, Plotly charts, drill-down, route map) | ✅ Done |
| 6 | AI — LangChain agent over ClickHouse for query, explain, recommend | ⏸️ Placeholder UI built |

## Indonesian Data

All generated data reflects Indonesian travel reality. The `id_ID` Faker locale produces Indonesian names (including Balinese birth-order names like Wayan/Made/Nyoman/Ketut, Muslim names, and single-name elders), `+62`/`08` phone formats, full RT/RW/kelurahan/kota/provinsi addresses, and Indonesian-patterned emails.

Currency is always IDR (Rupiah). Booking amounts range from Rp 100.000 (budget experience) to Rp 15.000.000+ (international business-class flights). Payment methods cover the Indonesian mobile-first landscape: QRIS, GoPay, OVO, DANA, ShopeePay, LinkAja, COD, and Bank Transfer (BCA, Mandiri, BRI, BNI).

Travel patterns are domestic-dominant: CGK-DPS (Jakarta-Bali), SUB-CGK, KNO-CGK, UPG-DPS, CGK-JOG, with some regional/international routes. Hotels cluster in tourist destinations across Bali, Yogyakarta, Lombok, and Labuan Bajo. Support tickets are in Bahasa Indonesia covering real travel issues: flight delays, hotel mismatches, refund requests, date changes.

Seasonal spikes model real Indonesian travel behaviour: Lebaran (mudik travel surge), Natal dan Tahun Baru (holiday travel), Imlek (getaway bookings), and school holiday periods (Juni-Juli, Desember) where family bookings spike 3-5x.

The simulation injects deliberate messiness — encoding drift, schema drift across years, name-spelling variation, phone format inconsistency, email typos and aliases, date format variations, and identity fragmentation — to test real-world entity resolution.

## Design Constraint: Simulation is Standalone

The **simulation** is standalone, driven by cron or manual scripts (`run_day.py`, `backfill.py`). Dagster does not run the generator. Dagster orchestrates only the landing pipeline: extract from mock sources, land directly in ClickHouse bronze tables, and trigger dbt → ClickHouse → Streamlit. Putting the generator inside Dagster is a design error.
