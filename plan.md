# WanderFuel Customer 360 — Architecture & Specification

> This document is the primary specification for a greenfield project. It defines *why* and *how* before all code exists. Once code lands, the code becomes the source of truth for *what*; this document remains the source of truth for *why*.

## Goal

An end-to-end data pipeline that ingests intentionally messy, heterogeneous travel booking data from three simulated source systems, lands it in MinIO as Parquet, cleanses it (Silver), builds dimensional models in ClickHouse (Gold), and serves a Customer 360 view through Streamlit — with entity resolution, CLV, and loyalty-tier segmentation. The endgame is an agent-powered AI analytics layer over ClickHouse.

All generated source data reflects **Indonesian travel reality** — Indonesian names, phone numbers (`+62`/`08` formats), emails, full RT/RW/kelurahan/kecamatan/kota/provinsi addresses, IDR currency, domestic flight routes, Indonesian hotel cities, Bahasa Indonesia support tickets, and Lebaran/Natal/Imlek/school-holiday seasonal spikes.

## Problem Statement

WanderFuel's booking data is fragmented across three silos:

- **App OLTP (PostgreSQL)**: hotel bookings linked to `customer_id`. Full customer identity — customer_id, email, phone, name, address. But this covers only ~40% of total bookings.
- **Vendor API (FastAPI)**: flights and experiences bookings. Keyed by **email only** — no customer_id, no phone. ~50% of volume.
- **CRM SFTP**: support ticket JSON files via SFTP. Has both **email and phone**, but the support-ticket email sometimes differs from the booking email. ~10% of volume.

The same human appears across all three systems under different identifiers. Hotels have `customer_id` (resolved), but flights and experiences only carry an email — and that email might differ from the one in CRM. Resolving these identities is the central analytical challenge.

## Stack

- **Orchestration:** Dagster
- **Transformation:** dbt (SQL, Silver + Gold) + Pandas (in-memory landing writes)
- **Landing zone:** MinIO (S3-compatible), Parquet, **no intermediate local files**
- **Warehouse:** ClickHouse
- **Visualization / Customer 360:** Streamlit
- **AI / agentic layer:** LangChain-powered query, explain, and recommend engine over ClickHouse
- **Source systems:**
  - App OLTP (PostgreSQL — hotel bookings + customer profiles)
  - Vendor API (FastAPI app returning JSON flight and experience bookings)
  - CRM SFTP (daily JSON ticket files via SFTP)

## Architecture

```
 simulation (cron daily) ──▶ mock sources ──▶ Dagster (schedule) ──▶ MinIO Parquet ──▶ dbt silver ──▶ dbt gold ──▶ Streamlit
    world state         • App OLTP (Postgres)         (landing)           cleanse           (ClickHouse)    (LangChain AI layer)
    Faker               • Vendor API (FastAPI/JSON)
    SQLite              • CRM SFTP (JSON files)
```

### Zones

1. **Landing (Bronze)** — Dagster op extracts each source straight from memory into Parquet in MinIO. No local intermediate files.
2. **Silver** — dbt models standardize Indonesian phones (to `+62...`), lowercase emails, normalize dates/money (IDR — drop phantom cents, fix `Rp`/`.`-thousand-separator), handle nulls/sentinels (`TIDAK ADA`, `tidak diketahui`, `000-000-0000`), drop near-dupes.
3. **Gold** — dbt dimensional models in ClickHouse: `fact_bookings`, `dim_customer` (resolved identities).
4. **Serving** — Streamlit dashboard (labels Bahasa Indonesia or bilingual); entity resolution (merge app customer_id customer ↔ vendor email-only customer ↔ CRM email+phone customer), CLV in IDR, loyalty tiers.
5. **AI** — LangChain agent over ClickHouse for natural-language querying, anomaly explanation, and proactive recommendations.

## Repo Layout

```
agentic-c360/
  plan.md
  AGENTS.md
  STORY.md
  README.md
  docker-compose.yml            # Postgres (app OLTP), FastAPI vendor API
  docker-compose.pipeline.yml   # MinIO, ClickHouse, Dagster (planned)
  .env.example
  Makefile
  simulation/                   # imitates real-world sources; standalone cron/script
    config.yaml                 # SEED, daily volume (0–5k), error/dupe/drift knobs
    world/                      # persistent world state (SQLite)
    lib/                        # Shared simulation library
    gen/                        # Faker-based daily generator
    sources/
      app_oltp/                 # PostgreSQL seed + daily inserter (customers, hotel_bookings)
      vendor_api/               # FastAPI app serving JSON flight/experience bookings
      crm_s3/                   # SFTP JSON writer (daily ticket exports)
    scripts/
      backfill.py               # --days N to backfill a long history
      run_day.py                # generate one travel day (--date YYYY-MM-DD)
      reset.sh                  # wipe world state + generated artifacts
  dagster_pipeline/             # land (extract → MinIO Parquet) + orchestration schedules
  dbt/                          # silver (cleanse) + gold (dims/facts) SQL models
  streamlit_app/                # Customer 360 dashboard
  ops/                          # dbt profiles, ClickHouse init SQL, etc.
```

## Simulation Design: Imitating Real-World Messy Sources

### Three Mock Source Systems

#### 1. App OLTP (PostgreSQL)

Internal WanderFuel app database. The **only** source with full customer identity.

- **Table `customers`**: customer_id (PK), email, phone, full_name, address, city, province, postal_code, created_at, updated_at
- **Table `hotel_bookings`**: booking_id (PK), customer_id (FK → customers), hotel_name, hotel_city, check_in_date, check_out_date, room_type, guests, amount_idr, payment_method, booking_status, booking_ts
- Dates in ISO format (`YYYY-MM-DD`)
- Payment methods: QRIS, GoPay, OVO, DANA, ShopeePay, LinkAja, COD, Bank Transfer (BCA/Mandiri/BRI/BNI)
- Hotels span Indonesian tourist destinations: Kuta, Seminyak, Ubud, Canggu (Bali), Yogyakarta, Bandung, Lombok, Labuan Bajo, Jakarta, Surabaya, Medan, Makassar, Manado
- Schema drift: 2022 schema lacked `loyalty_tier` and `preferred_airline` columns; 2024+ includes them
- Encoding: UTF-8

#### 2. Vendor API (FastAPI, SQLite-backed)

External vendor partner supplying flights and experiences inventory. No customer_id.

- **Endpoint `GET /flights?since=...`** returns `flight_bookings`: booking_id (PK), email, airline, flight_number, origin (IATA), destination (IATA), departure_ts, arrival_ts, passenger_name, seat_class (economy/business/first), amount_idr, payment_method, booking_status, booking_ts
- **Endpoint `GET /experiences?since=...`** returns `experience_bookings`: booking_id (PK), email, experience_name, city, activity_date, participants, amount_idr, payment_method, booking_status, booking_ts
- JSON, ISO timestamps, IDR amounts
- Airlines: Garuda Indonesia (GA), Lion Air (JT), Citilink (QG), Batik Air (ID), AirAsia Indonesia (QZ), Sriwijaya Air (SJ), Pelita Air (IP), Wings Air (IW)
- Domestic routes: CGK-DPS, SUB-CGK, DPS-LOP, KNO-CGK, UPG-DPS, BPN-SUB, CGK-JOG, DPS-LBJ, CGK-PDG, SRG-CGK
- Regional/international routes: CGK-SIN, DPS-KUL, CGK-NRT, DPS-PER, CGK-KUL
- Experiences: cooking classes, dive trips, volcano treks, temple tours, snorkelling, surfing lessons, spa packages, cultural workshops
- Backed by SQLite store the generator increments daily

#### 3. CRM SFTP (JSON Files via SFTP)

Third-party CRM vendor drops daily ticket export files with support interactions.

- File pattern: `tickets/YYYY/MM/DD/tickets_YYYYMMDD.json`
- Each file contains an array of ticket objects: ticket_id, customer_email, customer_phone, subject, body, status (open/in_progress/resolved/closed), priority (low/medium/high/critical), created_at, resolved_at
- Has **both email and phone** — this is the identity bridge
- Ticket bodies in **Bahasa Indonesia**: "penerbangan ditunda 3 jam", "kamar hotel bau rokok", "refund pengalaman menyelam dibatalkan karena cuaca", "ubah tanggal check-in jadi 15 Agustus", "bagasi hilang penerbangan CGK-DPS"
- Support-ticket email often differs from booking email — personal vs work email, typo variants, `+` aliases
- Date drift: occasionally uses Indonesian month abbreviations (`15 Agt 2024`, `3 Jan 2025`)
- Encoding: UTF-8 with occasional ISO-8859-1 mojibake on old-romanization characters

### Daily Generator

A single Faker-based Python generator with persistent world state, defaulting to the `id_ID` locale (all names, phones, addresses, emails generated as Indonesian):

- World state in SQLite (customers, hotels, flight routes, airlines, experience catalogues, Indonesian cities/provinces, holiday calendar). Reproducible via seed.
- Each run simulates one travel day (`run_day.py`), or N days (`backfill.py --days N`):
  - ~40% of booking volume is hotels (via app OLTP) — mix of existing returning customers and new sign-ups
  - ~30% is flights (via vendor API) — domestic routes dominant, some international
  - ~20% is experiences (via vendor API) — city tours, adventure activities, cultural workshops
  - ~10% is CRM tickets — refund requests, rescheduling, complaints, general inquiries
  - ~70% of bookings from existing customers; ~30% from new customers
  - Identity fragmentation: some customers booked hotels under one email, flights under another, and opened CRM tickets under a third email+phone combination
  - Holiday-mode days amplify volume and shift route mix: Lebaran (mudik), Natal/Tahun Baru (holiday travel), Imlek (getaways), school holidays (family bookings)
  - Small slice of refunds, cancellations, rebookings, and near-duplicate resubmissions
- Writes the day's output to all three mock sources in one run.

### Local Context (Indonesia) — All Generated Data is Indonesian

The whole point of this project is realistic Indonesian travel data. Use the `id_ID` Faker locale as the default and bias everything toward local conventions; the messiness below is injected on top of a realistic Indonesian baseline.

- **Names** (use `Faker("id_ID").name()`): Indonesian given + family name patterns — e.g. `Budi Santoso`, `Siti Nurhaliza`, `Muhammad Rizki`, `Wayan Sutedja` (Balinese birth-order first names: Wayan/Made/Nyoman/Ketut), `Eka Wijaya`, `Dewi Lestari`. Single-name customers still exist and are a real source of identity confusion. Honorifics (`Bpk.`/`Ibu`/`Sdr.`) sometimes appear, sometimes don't.
- **Phones**: Indonesian mobile numbering — `+62 812-3456-7890`, `0812-3456-7890`, `0852-1234-5678` (Telkomsel/Indosat/XL/Three/Smartfren prefixes), landlines `021-1234567` (Jakarta), `0361` (Denpasar/Bali), `0274` (Yogyakarta). Messiness: missing `0`/`+62`, mixed `08` vs `62`, dashed vs dotted vs spaces, leading zero stripped, WhatsApp-only contacts captured as mobile.
- **Emails**: indonesian-name-based — `budi.santoso@gmail.com`, `siti.nurhaliza88@yahoo.co.id`, `wayan.sutedja@outlook.com`, travel-agency accounts `booking@cv-wisata.co.id`. Messiness: mixed case, domain typos (`gnail.com`, `gmaill.com`), trailing whitespace, gmail `+` aliases, `.co.id` vs `.com`, personal vs work email across sources.
- **Addresses**: full Indonesian address structure — `Jl. Merdeka No. 17, RT 03/RW 02, Kel. Menteng, Kec. Menteng, Jakarta Pusat, DKI Jakarta, 10110`. Travel-relevant provinces/cities: DKI Jakarta (business hub + departure), Bandung/Jabar (weekend getaway), Surabaya/Jatim (business + departure), Denpasar/Bali (top destination), Yogyakarta/DIY (cultural tourism), Medan/Sumut (departure), Makassar/Sulsel (eastern hub), Lombok/NTB (destination), Labuan Bajo/NTT (destination), Manado/Sulut (diving destination). Messiness: RT/RW sometimes joined, kelurahan vs kel omitted, kabupaten vs kota confusion, missing kode pos, mixed-case.
- **Money / currency**: IDR — Rupiah amounts. Hotel nights Rp 250.000–5.000.000, domestic flights Rp 400.000–3.500.000, international flights Rp 2.000.000–15.000.000, experiences Rp 100.000–3.000.000. Typically rounded to hundreds/thousands, no real cents. Source-specific messiness: comma decimal separators (`Rp 9.999,50` in one source), `Rp` prefix vs no prefix, sometimes written as `IDR 1500000`, one source keeps phantom cents (`1500000.00`).
- **Dates**: ISO `2024-08-15T10:30:00` in vendor API, `DD/MM/YYYY` in app OLTP exports, `YYYY-MM-DD HH24:MI:SS` in Postgres. Also locale strings like `15 Agt 2024` (Indonesian month abbreviations: Jan/Feb/Mar/Apr/Mei/Jun/Jul/Agt/Sep/Okt/Nov/Des) occasionally leaking from CRM exports.
- **Language**: support ticket bodies in **Bahasa Indonesia** (`penerbangan ditunda`, `refund hotel`, `ubah jadwal`, `bagasi hilang`, `kamar tidak sesuai`). Dashboard labels in Bahasa or bilingual since the audience is the local industry.
- **Booking behaviour & payment conventions**:
  - Payment methods: QRIS, GoPay, OVO, DANA, ShopeePay, LinkAja, COD, Bank Transfer (BCA/Mandiri/BRI/BNI).
  - COD still common for hotel walk-in bookings in smaller cities.
  - Mobile-first: vast majority of bookings happen via the WanderFuel app.
  - Seasonality: Lebaran / Eid al-Fitr (mudik travel peak — flights, hotels en route), Natal (Christmas holiday bookings), Imlek (Chinese New Year getaways, especially to Bali/Singapore), Tahun Baru (New Year), school holidays (Juni-Juli, Desember — family bookings spike 3-5x). Generator knob `holiday_mode` to amplify these days.
- **Nulls/sentinels** (Indonesian-flavored): `null`, `''`, `N/A`, `TIDAK ADA`, `tidak diketahui`, `000-000-0000` (phone placeholder), `unknown`, `-1`, `0`-as-null on amount columns.
- **Other deliberate messiness**:
  - Schema drift: 2022 app OLTP schema lacked `loyalty_tier` and `preferred_airline`; 2024+ includes them.
  - Dupes & late events: Rp 1 re-submission diffs (`Rp 1.500.000` vs `Rp 1.499.999`), vendor API amendments for prior days arriving late.
  - Postcodes that don't match the listed city (deliberate, tests cleansing logic).
  - Mix of common misspellings of name (`Budi` vs `Boedi` old-spelling, `Yusuf` vs `Yoesoef`).
  - Identity fragmentation (core puzzle): same human appears as a customer_id+email+phone row in app OLTP, an email-only row in vendor API bookings, and an email+phone CRM ticket — potentially with a different email in each source. All with Indonesian names that may be spelled/cased differently across systems.

### Generator Knobs (`simulation/config.yaml`)

- `SEED` — deterministic reproducibility
- `locale` — default `id_ID` (Indonesian names, addresses, phones, currency format)
- `currency` — default `IDR`, amounts rounded to hundreds/thousands, formatted `Rp N.NNN.NNN`
- `daily_volume` — 0–5,000 rows/day total across all three sources (configurable; random per-day split across sources, supports a backfill ramp)
- `hotel_cap` — max hotel_bookings per day (~40% of total)
- `flight_cap` — max flight_bookings per day (~30%)
- `experience_cap` — max experience_bookings per day (~20%)
- `crm_cap` — max tickets per day (~10%)
- `error_rate`, `dupe_rate`, `drift_year`, `messiness_intensity`
- `holiday_mode` — amplify Lebaran/Natal/Imlek/Tahun Baru/school-holiday volume spikes; resolves against an Indonesian national-libur calendar
- `--date YYYY-MM-DD` and `--days N` flags; `reset` to wipe state + artifacts

## Data Model

### Source Tables

**App OLTP (PostgreSQL)**

```
customers
  customer_id        TEXT PK
  email              TEXT
  phone              TEXT
  full_name          TEXT
  address            TEXT
  city               TEXT
  province           TEXT
  postal_code        TEXT
  loyalty_tier       TEXT      -- NULL for 2022 schema (schema drift)
  preferred_airline  TEXT      -- NULL for 2022 schema
  created_at         TIMESTAMP
  updated_at         TIMESTAMP

hotel_bookings
  booking_id         TEXT PK
  customer_id        TEXT FK → customers
  hotel_name         TEXT
  hotel_city         TEXT
  check_in_date      DATE
  check_out_date     DATE
  room_type          TEXT
  guests             INTEGER
  amount_idr         DECIMAL
  payment_method     TEXT
  booking_status     TEXT      -- confirmed/cancelled/completed/no_show
  booking_ts         TIMESTAMP
```

**Vendor API (FastAPI JSON → Parquet)**

```
flight_bookings
  booking_id         TEXT PK
  email              TEXT
  airline            TEXT
  flight_number      TEXT
  origin             TEXT      -- IATA code
  destination        TEXT      -- IATA code
  departure_ts       TIMESTAMP
  arrival_ts         TIMESTAMP
  passenger_name     TEXT
  seat_class         TEXT      -- economy/business/first
  amount_idr         DECIMAL
  payment_method     TEXT
  booking_status     TEXT      -- confirmed/cancelled/completed/no_show
  booking_ts         TIMESTAMP

experience_bookings
  booking_id         TEXT PK
  email              TEXT
  experience_name    TEXT
  city               TEXT
  activity_date      DATE
  participants       INTEGER
  amount_idr         DECIMAL
  payment_method     TEXT
  booking_status     TEXT      -- confirmed/cancelled/completed/no_show
  booking_ts         TIMESTAMP
```

**CRM SFTP (JSON → Parquet)**

```
tickets
  ticket_id          TEXT PK
  customer_email     TEXT
  customer_phone     TEXT
  subject            TEXT
  body               TEXT      -- Bahasa Indonesia
  status             TEXT      -- open/in_progress/resolved/closed
  priority           TEXT      -- low/medium/high/critical
  created_at         TIMESTAMP
  resolved_at        TIMESTAMP
```

### Gold Tables (ClickHouse)

**`fact_bookings`**: booking_id, resolved_customer_id, source (app/vendor), booking_type (hotel/flight/experience), provider (hotel_name/airline/experience_name), city, amount_idr, currency (IDR), payment_method, booking_ts, status

**`dim_customer`**: resolved_customer_id, phones[] (normalized to `+62...`), emails[] (normalized), name_std, address_city (kelurahan/kecamatan/kota/provinsi zip), first_seen, last_seen, identity_confidence, clv_idr, loyalty_tier

### Entity Resolution Logic

**Identity keys per source:**

| Source | Has customer_id | Has email | Has phone |
|---|---|---|---|
| App OLTP (Postgres) | Yes | Yes | Yes |
| Vendor API (FastAPI) | No | Yes | No |
| CRM SFTP | No | Yes | Yes |

**Resolution rules:**

- App OLTP provides the anchor: every `customer_id` has a known email and phone.
- Vendor API bookings are resolved by matching `email` to known app OLTP customers.
- CRM tickets are resolved by matching either `email` or `phone` (normalized `+62...`) to known customers.
- If a vendor API email or CRM email doesn't match any known customer directly, but the CRM ticket for that email also has a phone that matches a known customer → link via phone bridge.
- Same email or same normalized phone across sources ⇒ same customer, with a confidence score.
- Unresolved customers get a placeholder `resolved_customer_id` (UUID); they may be resolved later when new identity data arrives.

### Loyalty Tiers

- **Gold**: CLV ≥ Rp 10.000.000
- **Silver**: CLV Rp 2.000.000 – Rp 9.999.999
- **Churn-Risk**: CLV < Rp 2.000.000 or dormant > 90 days

All tiers are IDR-banded. Never convert to USD/EUR anywhere in the pipeline.

## Roadmap

| Phase | Deliverable |
|---|---|
| 0 | Infra — docker-compose for MinIO, ClickHouse, Postgres, Dagster, vendor API. `.env.example`. |
| 1 | Simulation — world state, Faker generator, three mock sources, backfill script. Verify a year of messy travel history can be generated and reset. |
| 2 | Landing (Bronze) — Dagster ops extracting each source into MinIO Parquet (no local files). |
| 3 | Silver — dbt models: phone/email standardization, date/money normalization, null/sentinel handling, dedupe. |
| 4 | Gold — dbt `fact_bookings` + `dim_customer` with entity resolution in ClickHouse. |
| 5 | Serving — Streamlit Customer 360; CLV + loyalty tiers (Gold / Silver / Churn-Risk). |
| 6 | AI — LangChain agent over ClickHouse for natural-language query, anomaly explanation, proactive recommendations. |

## Operational Constraints

- The simulation/generator is **standalone** (cron/script). Dagster only orchestrates land→silver→gold→serve. Putting the generator inside Dagster is a design error.
- Backfill a long history up front with `backfill.py --days 365`; then increment daily.
- Never write intermediate local files during Dagster landing — write Parquet straight to MinIO from memory.
- Daily volume 0–5,000 rows is comfortable for Pandas in-memory and ClickHouse; even at the upper end, row-group sizing is straightforward.
- Keep money in IDR end-to-end; never silently convert to USD/EUR.
