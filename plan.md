# agentic-c360 — Architecture & Specification

> This document is the primary specification for a greenfield project. It defines *why* and *how* before all code exists. Once code lands, the code becomes the source of truth for *what*; this document remains the source of truth for *why*.

An end-to-end data pipeline that ingests intentionally messy, heterogeneous retail data from three simulated source systems, lands it in MinIO as Parquet, cleanses it (Silver), builds dimensional models in ClickHouse (Gold), and serves a Customer 360 view through Streamlit — with entity resolution, CLV, and loyalty-tier segmentation. The endgame is an agentic/AI analytics layer over ClickHouse.

All generated source data reflects **Indonesian retail reality** — Indonesian names, phone numbers (`+62`/`08` formats), emails, full RT/RW/kelurahan/kecamatan/kota/provinsi addresses, IDR currency, QRIS/COD/e-wallet/Bank-transfer payment methods, Bahasa Indonesia support tickets, and Lebaran/Natal/Imlek seasonal spikes.

## Problem statement
A retail brand started brick-and-mortar, expanded online, and uses a third-party customer support platform. The same human appears in different systems under different identifiers:
- Legacy POS: identified by **phone** only
- E-commerce: identified by **email** only
- CRM/Support: email + phone, but the support-ticket email sometimes differs from the e-commerce account email

Resolving these identities is the central analytical challenge.

## Stack
- **Orchestration:** Dagster
- **Transformation:** dbt (SQL, Silver + Gold) + Pandas (in-memory landing writes)
- **Landing zone:** MinIO (S3-compatible), Parquet, **no intermediate local files**
- **Warehouse:** ClickHouse
- **Visualization / Customer 360:** Streamlit
- **AI / agentic layer:** LLM-powered query, explain, and alert engine over ClickHouse
- **Source systems:**
  - E-commerce API (FastAPI app returning JSON orders)
  - Legacy POS (daily CSV files)
  - CRM/Support (local Postgres, extracted via Sling)

## Architecture

```
simulation (cron daily) ──▶ mock sources ──▶ Dagster (schedule) ──▶ MinIO Parquet ──▶ dbt silver ──▶ dbt gold ──▶ Streamlit
   world state         • FastAPI ecom (JSON)        (landing)           cleanse           (ClickHouse)    (agentic/AI layer)
   Faker               • CSV writer (POS)     • Sling for CRM
   SQLite/DuckDB       • Postgres  (CRM)
```

### Zones
1. **Landing (Bronze)** — Dagster op extracts each source straight from memory into Parquet in MinIO. No local intermediate files.
2. **Silver** — dbt models standardize Indonesian phones (to `+62...`), lowercase emails, normalize dates/money (IDR — drop phantom cents, fix `Rp`/`.`-thousand-separator), handle nulls/sentinels (`TIDAK ADA`, `tidak diketahui`, `000-000-0000`), drop near-dupes.
3. **Gold** — dbt dimensional models in ClickHouse: `fact_transactions`, `dim_customer` (resolved identities).
4. **Serving** — Streamlit dashboard (labels Bahasa Indonesia or bilingual); entity resolution (merge in-store phone customer ↔ online email customer), CLV in IDR, loyalty tiers.

## Repo layout
```
agentic-c360/
  plan.md
  AGENTS.md
  docker-compose.yml            # MinIO, ClickHouse, Postgres, Dagster, ecom mock API
  .env.example
  simulation/                   # imitates real-world sources; standalone cron/script
    config.yaml                 # SEED, daily volume (0–5k), error/dupe/drift knobs
    world/                       # persistent world state (SQLite or DuckDB)
    gen/                         # Faker-based daily generator
    sources/
      ecommerce_api/             # FastAPI app serving JSON orders from in-memory/SQLite store
      pos_csv/                   # daily CSV writer → sources/inbox/pos/sales_YYYYMMDD.csv
      crm_postgres/              # Postgres seed + daily inserter
    scripts/
      backfill.py                # --days N to backfill a long history
      run_day.py                 # generate one retail day (--date YYYY-MM-DD)
      reset.sh                   # wipe world state + generated artifacts
  dagster_pipeline/              # land (extract → MinIO Parquet) + orchestration schedules
  dbt/                           # silver (cleanse) + gold (dims/facts) SQL models
  streamlit_app/                 # Customer 360 dashboard
  ops/                           # dbt profiles, clickhouse init SQL, etc.
```

## Simulation design: imitating real-world messy sources

### Three mock source systems mimicking real interfaces
1. **E-commerce API** — FastAPI app exposing `GET /orders?since=…`. Paginated, ISO timestamps, nested order→line_items, status (paid/shipped/refunded), payment method (QRIS/GoPay/OVO/Bank Transfer/COD), customer keyed by **email**. All amounts in IDR. Backed by an in-memory/SQLite store the generator increments daily.
2. **Legacy POS** — daily CSV dropped at `simulation/sources/inbox/pos/sales_YYYYMMDD.csv`. Encoding `ISO-8859-1` (so accented Indonesian letters like `é` / `ü` in older romanizations mojibake when read as UTF-8), column drift across years (pre-2023 lacked `store_id`), customer keyed by **phone only** (Indonesian mobile / landline formats), store names like `Toko ..., CV ..., UD ...`, occasional bad delimiters / trailing blank rows.
3. **CRM/Support** — seeded local Postgres tables `customers`, `tickets`, `interactions` (ticket bodies in Bahasa Indonesia), extracted into MinIO by **Sling**. Support-ticket emails sometimes differ from the customer's e-commerce email.

### Daily generator
A single Faker-based Python generator with persistent world state, defaulting to the `id_ID` locale (all names, phones, addresses, emails generated as Indonesian):
- World state in SQLite or DuckDB (customers, products, store inventory, Indonesian provinces/cities, IDR price tiers, Lebaran/Imlek holiday calendar). Reproducible.
- Each run simulates one retail day (`run_day.py`), or N days (`backfill.py --days N`):
  - ~70% of orders from existing customers (mostly online, email-identified)
  - ~30% new walk-in customers (phone-only POS rows, often COD or cash)
  - Some in-store phone customers later place online orders with a **new email** (≡ identity fragmentation)
  - Small slice of refunds / cancels / near-duplicate re-scans (Rp 1 diffs)
  - Holiday-mode days amplify volume and product mix around Lebaran/Natal/Imlek/Tahun Baru
- Writes the day's output to all three mock sources in one run.

### Local context (Indonesia) — all generated data is Indonesian
The whole point of this project is realistic Indonesian retail data. Use the `id_ID` Faker locale as the default and bias everything toward local conventions; the messiness below is injected on top of a realistic Indonesian baseline.

- **Names** (use `Faker("id_ID").name()`): Indonesian given + family name patterns — e.g. `Budi Santoso`, `Siti Nurhaliza`, `Muhammad Rizki`, `Wayan Sutedja` (Balinese birth-order first names: Wayan/Made/Nyoman/Ketut), `Eka Wijaya`, `Dewi Lestari`. Single-name customers still exist (older / rural generations) and are a real source of identity confusion. Honorifics (`Bpk.`/`Ibu`/`Sdr.`) sometimes appear, sometimes don't.
- **Phones**: Indonesian mobile numbering — `+62 812-3456-7890`, `0812-3456-7890`, `0852-1234-5678` (Telkomsel/Indosat/XL/Three/Smartfren prefixes), landlines `021-1234567` (Jakarta) / `022` Bandung / `031` Surabaya. Messiness: missing `0`/`+62`, mixed `08` vs `62`, dashed vs dotted vs spaces, leading zero stripped (`812...`), WhatsApp-only contacts captured as mobile.
- **Emails**: indonesian-name-based — `budi.santoso@gmail.com`, `siti.nurhaliza88@yahoo.co.id`, `rizki.toko@outlook.com`, business accounts `admin@toko-sejahtera.co.id`. Messiness: mixed case, domain typos (`gnail.com`, `gmaill.com`, `yaho.com`), trailing whitespace, gmail `+` aliases, `.co.id` vs `.com`, personal vs business email across sources, work email like `budi@cv-makmur.com` that doesn't match their personal `budi.santoso@...`.
- **Addresses**: full Indonesian address structure — `Jl. Merdeka No. 17, RT 03/RW 02, Kel. Menteng, Kec. Menteng, Jakarta Pusat, DKI Jakarta, 10110`. Provinces/cities: DKI Jakarta, Bandung (Jabar), Surabaya (Jatim), Medan (Sumut), Makassar (Sulsel), Denpasar (Bali), Yogyakarta (DIY), Semarang (Jateng), Palembang (Sumsel), Balikpapan (Kaltim). Messiness: RT/RW sometimes joined `RT/RW 03/02`, sometimes split, kelurahan vs kel omitted, kabupaten vs kota confusion, missing kode pos, village names instead of kelurahan, mixed-case (`JL. MERDEKA` ALL CAPS).
- **Money / currency**: IDR — Rupiah amounts typically rounded to hundreds/thousands, no cents (e.g. `Rp 1.500.000` with `.` as thousand separator per id_ID locale). Source-specific messiness: comma decimal separators (`Rp 9.999,50` in one source), `Rp` prefix vs no prefix, sometimes written as `IDR 1500000`, one source keeps cents (`1500000.00`) that aren't real on the ground.
- **Dates**: ISO `2024-08-15T10:30:00` in e-com API, but `DD/MM/YYYY` (common Indonesian form) in POS CSV, `YYYY-MM-DD HH24:MI:SS` in Postgres. Also locale strings like `15 Agt 2024` (Indonesian month abbreviations: Jan/Feb/Mar/Apr/Mei/Jun/Jul/Agt/Sep/Okt/Nov/Des) occasionally leaking from CRM exports.
- **Language**: support ticket bodies and CRM interactions in **Bahasa Indonesia** (`toko online`, `pengembalian dana`, `kerusakan barang`, `ganti rugi`, `dt-05-rt-10` abbreviations). Customer-facing labels (`toko`, `produk`, `ongkir`, `grand total`, `metode bayar`) are id-ID too. Keep dashboard labels in Bahasa (or bilingual) since the audience is the local industry.
- **Customer behaviour / channel conventions**:
  - Payment methods: COD (still very common, esp. outside Jabodetabek), bank transfer (BCA/Mandiri/BRI/BNI), QRIS, e-wallets (GoPay/OVO/DANA/ShopeePay/LinkAja).
  - Marketplace slang in POS store names: `Toko ...`, `CV ...`, `UD ...` (usaha dagang), `Warung ...`.
  - Seasonality: Lebaran / Eid al-Fitr (peak — `kue lebaran`, `baju kurung`, `sarung`, `mukena`), Natal (Christmas), Imlek (Chinese New Year), Tahun Baru, Waisak; date overrides (`hari libur nasional`) drive volume spikes. Generator knob `holiday_mode` to amplify these days.
  - "Jajan" / snack-buying pattern: many small-ticket transactions typical in POS.
  - Free-ongkir / cashback / flash-sale sensitivity shapes promotional demand.
- **Nulls/sentinels** (Indonesian-flavored): `null`, `''`, `N/A`, `TIDAK ADA`, `tidak diketahui`, `000-000-0000` (phone placeholder), `unknown`, `-1`, `0`-as-null on amount columns.
- **Other deliberate messiness**:
  - Schema drift: 2022 POS CSV lacks `store_id`; 2024+ has it.
  - Dupes & late events: Rp 1 re-scan diffs (`Rp 1.500.000` vs `Rp 1.499.999`), POS appends for prior days arriving late.
  - Postcodes that don't match the listed kelurahan (deliberate, tests cleansing logic).
  - Mix of common misspellings of name (`Budi` vs `Boedi` old-spelling, `Yusuf` vs `Yoesoef`).
  - Identity fragmentation (core puzzle): same human appears as a phone-only POS row, an email-only e-commerce row, an email+phone CRM row, and a slightly different support-ticket email — all with Indonesian names that may be spelled/cased differently across systems.

### Generator knobs (`simulation/config.yaml`)
- `SEED` — deterministic reproducibility
- `locale` — default `id_ID` (Indonesian names, addresses, phones, currency format)
- `currency` — default `IDR`, amounts rounded to hundreds/thousands, formatted `Rp N.NNN.NNN`
- `daily_volume` — 0–5,000 rows/day total across all three sources (configurable; random per-day split across sources, supports a backfill ramp)
- `error_rate`, `dupe_rate`, `drift_year`, `messiness_intensity`
- `holiday_mode` — amplify Lebaran/Natal/Imlek/Tahun Baru volume spikes; resolves against an Indonesian national-libur calendar
- `--date YYYY-MM-DD` and `--days N` flags; `reset` to wipe state + artifacts

## Data model (Gold, ClickHouse)
- `fact_transactions`: transaction_id, resolved_customer_id, source, channel, product, qty, amount_idr, currency (IDR), payment_method (QRIS/COD/GoPay/OVO/Bank Transfer), txn_ts, status
- `dim_customer`: resolved_customer_id, phones[], emails[], name_std, address_city (kelurahan/kecamatan/kota/provinsi zip), first_seen, last_seen, identity_confidence, clv_idr, loyalty_tier
- Entity resolution keys: phone (normalized Indonesian format `+62...`) and email (normalized); same phone or same email across sources ⇒ same customer, with a confidence score.
- Loyalty tiers in IDR bands (e.g. Gold ≥ Rp 10jt LTV, Silver Rp 2–10 jt, Churn-Risk < Rp 2 jt or dormant > 90 days).

## Roadmap (phased)
0. **Infra** — `docker-compose.yml` for MinIO, ClickHouse, Postgres, Dagster + ecom mock API. `.env.example`.
1. **Simulation** — world state, Faker generator, three mock sources, backfill script. Verify a year of messy history can be generated and reset.
2. **Landing (Bronze)** — Dagster ops extracting each source into MinIO Parquet (no local files); Sling for Postgres CRM.
3. **Silver** — dbt models: phone/email standardization, date/money normalization, null/sentinel handling, dedupe.
4. **Gold** — dbt `fact_transactions` + `dim_customer` with entity resolution in ClickHouse.
5. **Serving** — Streamlit Customer 360; CLV + loyalty tiers (Gold / Silver / Churn-Risk).
6. **Daily run** — cron for `run_day.py`; Dagster schedule for land→serve.

## Operational constraints
- The simulation/generator is **standalone** (cron/script). Dagster only orchestrates land→silver→gold→serve.
- Backfill a long history up front with `backfill.py --days 365`; then increment daily.
- Never write intermediate local files during Dagster landing — write Parquet straight to MinIO from memory.
- Daily volume 0–5k is comfortable for Pandas in-memory and ClickHouse; even at the upper end, row-group sizing is straightforward.