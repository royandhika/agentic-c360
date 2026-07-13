# AGENTS.md

Agent-relevant conventions, gotchas, and operational principles. Read `plan.md` first — it is the architecture source of truth.

## Operational principles

- **Delegate whenever possible.** Use subagents (`task` tool with explore/general types) for file searches, code exploration, and multi-step tasks. Run independent subagent calls in parallel.
- **Verify against existing code, not memory.** Do not invent commands, tool versions, or directory structure. Before acting, check `plan.md`, then confirm against the actual filesystem.

## Repo status

Partially built: `simulation/` (Phase 1) and `dagster_pipeline/` (Phase 2) have code; `plan.md` is the specification for the remaining subsystems (`dbt/`, `streamlit_app/`). Where code exists, it is the source of truth for *what*; `plan.md` remains the source of truth for *why*.

## Two systems, don't conflate them

- **Simulation/generator** is **standalone** (cron / `simulation/scripts/`). Dagster does NOT run it.
- **Dagster** orchestrates only land→silver→gold→serve. Putting the generator inside Dagster is a design error.

## Everything is Indonesian — don't generate US/EU data

- Use Faker locale `id_ID` as the default. Names, phones, emails, addresses, currency, and behaviour all reflect Indonesian travel.
- **Phones**: Indonesian format `+62 812-...` / `0812-...`. Normalize to `+62...` in Silver. Mobile prefixes 0812–0899 (Telkomsel/Indosat/XL/Three/Smartfren); landlines 021 Jakarta / 022 Bandung / 031 Surabaya / 0361 Denpasar / 0274 Yogyakarta.
- **Emails**: Indonesian-name-based (`budi.santoso@gmail.com`, `tiket-...@...co.id`). Same person often has a personal email and a separate travel/work email.
- **Addresses**: full Indonesian structure — `Jl. ... No. .., RT 03/RW 02, Kel. .., Kec. .., Kota/Kab. .., Provinsi .., Kode Pos`. RT/RW sometimes joined, sometimes split; kelurahan/kode pos sometimes mismatched (deliberate).
- **Names**: include Balinese birth-order names (Wayan/Made/Nyoman/Ketut), Muslim names (Muhammad/Siti/Ahmad), honorifics (Bpk./Ibu/Sdr. sometimes present, sometimes not). Single-name elders exist — a real identity-resolution edge case.
- **Currency**: IDR only. Amounts rounded to hundreds/thousands; no real cents. Watch for `Rp 1.500.000` (dot-thousand-separator) vs `1.499.999,50` (comma-decimal) drift across sources — both are intentional.
- **Language**: CRM/support tickets in Bahasa Indonesia (`penerbangan ditunda`, `refund hotel`, `ubah jadwal`, `bagasi hilang`). Dashboard labels in Bahasa or bilingual.
- **Travel patterns**: domestic flights dominant (CGK-DPS, SUB-CGK, KNO-CGK, UPG-DPS, CGK-JOG) with some regional/international (CGK-SIN, DPS-KUL). Hotels in tourist destinations: Bali (Kuta, Seminyak, Ubud, Canggu), Yogyakarta, Bandung, Lombok, Labuan Bajo, Jakarta, Surabaya. Experiences: cooking classes, dive trips, volcano treks, temple tours, snorkelling, surfing lessons.
- **Payment methods**: QRIS / GoPay / OVO / DANA / ShopeePay / LinkAja / COD / Bank Transfer (BCA/Mandiri/BRI/BNI). COD still common for walk-in hotel bookings in smaller cities.
- **Seasonal spikes**: Lebaran (mudik travel peak), Natal / Tahun Baru, Imlek, school holidays (Juni-Juli, Desember) → `holiday_mode` knob.

## Source-system identity keys (central to entity resolution)

- **App OLTP (Postgres)**: customer_id + email + phone. The only source with full identity. `customers` table links to `hotel_bookings` via customer_id FK. UTF-8 encoding.
- **Vendor API (FastAPI, SQLite-backed)**: email only, no phone, no customer_id. Two endpoints: `/flights` returns `flight_bookings`, `/experiences` returns `experience_bookings`. JSON, ISO dates, IDR.
- **CRM SFTP (JSON files)**: email + phone. Daily ticket exports with support interactions in Bahasa Indonesia. Support-ticket emails sometimes differ from the booking email (personal vs work, typos, aliases). This is the identity bridge.
- Schema drift across app OLTP years (e.g. 2022 lacks `loyalty_tier` and `preferred_airline`) is intentional.
- Indonesian date formats drift across sources: ISO in API, `DD/MM/YYYY` in app OLTP exports, `YYYY-MM-DD HH24:MI:SS` in Postgres, `15 Agt 2024` (id month abbreviations: Jan/Feb/Mar/Apr/Mei/Jun/Jul/Agt/Sep/Okt/Nov/Des) occasionally leaking from CRM exports.

## Identity resolution logic

The entity resolution pipeline resolves identities bottom-up:

1. **App OLTP is the anchor** — every `customer_id` has a verified email and phone.
2. **Vendor API bookings** resolve by matching `email` to known app OLTP customers.
3. **CRM tickets** resolve by matching `email` or normalized `phone` to known customers.
4. **Phone bridge**: if a vendor API email doesn't match directly, but a CRM ticket shares that email and also has a phone that matches a known customer → link via phone.
5. Same normalized email or same normalized phone → same `resolved_customer_id` with a confidence score.

Never assume email alone is sufficient for identity. The same human routinely uses different emails across app, vendor, and CRM.

## Hard constraints

- Never write intermediate local files during Dagster landing — write Parquet straight to MinIO from memory.
- Daily volume target: 0–5,000 rows/day (total across all three sources, random per-day split). Pandas-in-memory + ClickHouse are comfortable in this range.
- Keep money in IDR end-to-end; never silently convert to USD/EUR anywhere in the pipeline. Loyalty tiers are IDR-banded (e.g. Gold ≥ Rp 10jt LTV, Silver Rp 2–10 jt, Churn-Risk < Rp 2 jt or dormant > 90 days).
- ALL credentials, secrets, API keys, and passwords MUST live in `.env`. Never hardcode any credential anywhere in the codebase.
- MinIO and ClickHouse credentials are in `.env`; the pipeline containers read them at runtime via environment variables.

## Common commands (once code exists — verify before trusting)

- Backfill a long history: `python simulation/scripts/backfill.py --days 365`
- Generate one travel day: `python simulation/scripts/run_day.py --date YYYY-MM-DD`
- Wipe simulation state + generated artifacts: `simulation/scripts/reset.sh`
- Start generator: `make generator-up`
- Start pipeline infra: `make orchestrator-up`
- Stop pipeline infra: `make orchestrator-down`

## Infra topology (docker-compose, local)

MinIO (bronze Parquet landing), ClickHouse (warehouse), Postgres (app OLTP), Dagster daemon + webserver, plus the FastAPI mock vendor API.

## Where things live

- `simulation/` — generator + three mock sources (cron-driven), all Indonesian data via `id_ID`
- `dagster_pipeline/` — land→silver→gold→serve orchestration
- `dbt/` — silver (cleanse) + gold (dims/facts) SQL
- `streamlit_app/` — Customer 360 dashboard (Bahasa/bilingual labels)
- `plan.md` — full architecture; read it before non-trivial work
- `STORY.md` — project backstory and context for any agent or contributor

## Dagster pipeline conventions (Phase 2)

### Resource pattern
- **Always `EnvVar`**, never `os.getenv()` in resources or definitions. `EnvVar.int()` for ints.
- `ConfigurableResource` subclasses in `dagster_pipeline/dagster_pipeline/resources.py`. Register **bare** in `definitions.py`: `PostgresResource()`.
- Resources inject by **type annotation** on asset function params (not string keys).

### Asset module pattern (`assets/app_oltp.py`, `assets/vendor_api.py`, `assets/crm_sftp.py`)
- **1 source → 1 module**, asset + checks colocated.
- Shared helpers: `_helpers.py` with `_DTYPE_MAP`+`_map_dtype()` (pandas→dagster types), `_build_path(bucket, date)`, `_read_parquet(minio, path)`, `_write_parquet(minio, df, path)`.
- **`key_prefix=["bronze"]`**, **`group_name="landing"`**, **`kinds=["parquet","s3"]`** for all bronze assets.
- **`DailyPartitionsDefinition(start_date="2026-01-01")`** on all landing assets.
- **No `metadata=` on decorator** — column schema goes in `MaterializeResult` at runtime from `df.dtypes`.
- Metadata keys: `dagster/column_schema`, `dagster/row_count`, `path`, `batch_date`.
- Parquet path: `s3://{bucket}/{source}/{table}/year=YYYY/month=MM/day=DD/{table}_YYYYMMDD.parquet`

### Asset checks (3 per asset, colocated)
| Check | Validates |
|-------|-----------|
| `{asset}_not_empty` | row count > 0 |
| `{asset}_no_null_pks` | primary key column(s) no nulls |
| `{asset}_unique_pks` | primary key column(s) no duplicates |

Checks read the parquet back from MinIO via `_build_path`+`_read_parquet`, use `AssetCheckExecutionContext` + `context.partition_key`.

### Definitions
- `load_assets_from_package_module(assets)` + `load_asset_checks_from_package_module(assets)`
- Resources wired via `dg.Definitions(resources={"postgres": PostgresResource(), "minio": MinIOResource(), "vendor_api": VendorApiResource(), "crm_sftp": SFTPSourceResource()})`
