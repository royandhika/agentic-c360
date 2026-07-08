# WanderFuel — Project Backstory

## The Startup

WanderFuel is an Indonesian travel companion startup. The mobile app lets travellers book flights, hotels, and curated local experiences — cooking classes in Ubud, sunrise treks up Mount Bromo, diving trips in Raja Ampat. Founded in 2022, WanderFuel has grown to serve hundreds of thousands of users across the archipelago, from weekend-warrior Jakartans booking quick Bandung getaways to international tourists discovering Bali and Lombok.

## The Data Team

I am the Head of Data at WanderFuel. I joined six months ago with a clear mandate: build a data platform. At a board meeting last quarter, the CEO asked a simple question — "who are our most valuable customers?" — and nobody could answer it. Not because the data doesn't exist, but because it lives in three separate systems that have never been connected.

## The Business Problem

WanderFuel's booking data is fragmented across three silos:

1. **Our app database (PostgreSQL)** holds customer profiles (`customer_id`, email, phone, full name) and hotel bookings. This is the only system that knows customer identity — every hotel booking links to a `customer_id`. But it only covers ~40% of our total booking volume.

2. **A vendor partner API** supplies flights and experiences. Carriers like Garuda, Lion Air, and Citilink; experience operators like dive shops and cooking schools. The vendor API is keyed by **email only** — no `customer_id`, no phone. ~50% of our bookings flow through this API, and we have no idea which of these flyers and adventurers are also our hotel guests.

3. **A third-party CRM tool** drops daily JSON ticket exports into an SFTP server. Support interactions — refund requests, flight rescheduling complaints, a traveller who booked the wrong hotel dates. The CRM has both **email and phone**, but the support-ticket email often differs from the booking email. This is our identity bridge, but it is messy.

The same person — call her Ibu Siti Nurhaliza from Surabaya — might book a hotel through our app (identified by `customer_id`), a Garuda flight through the vendor API (identified by `siti.nurhaliza@gmail.com`), and a Mount Bromo sunrise trek (identified by `sitinurh@yahoo.co.id`), then open a CRM ticket because her flight got rescheduled (identified by `siti.nurhaliza@gmail.com` and `+62-812-3456-7890`). These four events are the same human, but our systems don't know it.

## The Vision

The immediate goal is a **Customer 360 dashboard**: one row per resolved customer, showing every booking, total lifetime value in IDR, loyalty tier, and contact history. If Ibu Siti calls support, the agent should see her full travel history in one screen.

The longer-term goal — built on top of the C360 — is an **agent-powered AI analytics layer** using LangChain. An LLM that can answer natural-language questions ("which customers are likely to churn before Lebaran?"), explain anomalies ("why did Makassar hotel bookings drop 40% last week?"), and proactively recommend actions ("these 200 Gold-tier customers haven't booked anything in 60 days — send them a Garuda promo code").

## The Pipeline

```
 3 siloed sources        Dagster orchestration       Analytics & AI
 ┌─────────────┐         ┌──────────────┐         ┌──────────────────┐
 │ App OLTP     │────────▶│  Land (MinIO) │──Parquet▶│  Silver (dbt)    │
 │ (PostgreSQL) │         │              │         │  cleanse/normalize│
 ├─────────────┤         │              │         └────────┬─────────┘
 │ Vendor API   │────────▶│  Bronze zone │                  │
 │ (FastAPI)    │         │              │         ┌────────▼─────────┐
 ├─────────────┤         │              │         │  Gold (dbt)       │
 │ CRM SFTP       │────────▶│              │         │  dims/facts       │
 │ (JSON) │         └──────────────┘         │  entity resolution│
 └─────────────┘                                   └────────┬─────────┘
                                                            │
                                              ┌─────────────▼─────────┐
                                              │  Streamlit C360       │
                                              │  + LangChain AI       │
                                              └───────────────────────┘
```

## Current Phase

We are building the **simulation** — a standalone Python generator that creates realistic, intentionally messy Indonesian travel data across all three source systems. The simulation uses a shared world state (SQLite) to maintain consistency: the same customer appears across all three sources with the identity fragmentation patterns we'll need to resolve in the pipeline.

The simulation is standalone. It runs on cron or via manual scripts. Dagster (coming in Phase 2) orchestrates only the landing→silver→gold→serve pipeline.

## Deliberate Messiness

The generator injects realistic data problems that mirror what we actually see in production:

- **Identity fragmentation**: same customer appears as phone+email+customer_id in app OLTP, email-only in vendor API, different email+phone in CRM
- **Encoding drift**: app OLTP uses UTF-8, vendor API uses clean JSON, CRM JSON occasionally leaks ISO-8859-1 (mojibake on old-romanization accented characters like `José` → `JosÃ©`)
- **Phone format variation**: `+62 812-3456-7890`, `0812-3456-7890`, `81234567890`, `+6281234567890` — all the same number
- **Email variation**: personal vs business emails across sources, `+` aliases, domain typos, mixed case
- **Date format drift**: ISO in API, `DD/MM/YYYY` in app OLTP exports, `15 Agt 2024` in CRM exports
- **Schema drift across years**: 2022 app OLTP schema lacked `loyalty_tier`; 2024+ has it
- **Nulls and sentinels**: `TIDAK ADA`, `tidak diketahui`, `000-000-0000`, `-1` amounts
- **Near-duplicates**: booking resubmissions with Rp 1 differences, late-arriving amendments
- **Postal codes that don't match the listed city** (tests cleansing logic)

## Indonesian Travel Data

Everything is Indonesian. The `id_ID` Faker locale produces Indonesian names (including Balinese birth-order names like Wayan/Made/Nyoman/Ketut, Muslim names like Muhammad/Siti/Ahmad, and single-name elders), full addresses (Jalan, RT/RW, Kelurahan, Kecamatan, Kota/Kabupaten, Provinsi, Kode Pos), `+62`/`08` phone numbers, and Indonesian-patterned emails.

Currency is always IDR (Rupiah). Booking amounts range from Rp 250.000 (budget guesthouse one-night stay) to Rp 15.000.000+ (international business-class flights). Payment methods: QRIS, GoPay, OVO, DANA, ShopeePay, LinkAja, COD, and Bank Transfer (BCA, Mandiri, BRI, BNI).

Travel patterns are domestic and regional: CGK-DPS (Jakarta→Bali), SUB-CGK (Surabaya→Jakarta), KNO-CGK (Medan→Jakarta), UPG-DPS (Makassar→Bali), BPN-SUB (Balikpapan→Surabaya), plus international routes like CGK-SIN, DPS-KUL, CGK-NRT. Hotels cluster in tourist destinations: Bali (Kuta, Seminyak, Ubud, Canggu), Yogyakarta, Bandung, Lombok, Labuan Bajo, plus business hotels in Jakarta and Surabaya.

Support tickets are in Bahasa Indonesia: "penerbangan ditunda", "kamar hotel tidak sesuai", "refund pengalaman dibatalkan", "ubah tanggal check-in".

Seasonal spikes: Lebaran (mudik travel surge), Natal dan Tahun Baru (holiday travel), Imlek (Chinese New Year getaways), and school holiday periods (Juni-Juli, Desember) where family bookings spike 3-5x.

## Tech Stack

| Layer | Technology |
|---|---|
| Simulation | Python, Faker (`id_ID`), SQLite (world state) |
| Source Systems | PostgreSQL (app OLTP), FastAPI/SQLite (vendor API), SFTP (CRM) |
| Orchestration | Dagster |
| Landing | MinIO (S3-compatible), Parquet |
| Transformation | dbt (SQL) + Pandas |
| Warehouse | ClickHouse |
| Dashboard | Streamlit (Bahasa/bilingual labels) |
| AI | LangChain + LLM (Phase 5+) |

## Roadmap

| Phase | Milestone |
|---|---|
| 0 | Infrastructure — docker-compose for all services |
| 1 | Simulation — world state, generator, 3 mock sources, backfill |
| 2 | Landing (Bronze) — Dagster extracts to MinIO Parquet |
| 3 | Silver — dbt cleanse: phone/email normalization, date/money, nulls, dedupe |
| 4 | Gold — fact_bookings + dim_customer with entity resolution in ClickHouse |
| 5 | Serving — Streamlit Customer 360 with CLV, loyalty tiers |
| 6 | AI — LangChain query/explain/recommend layer over ClickHouse |
