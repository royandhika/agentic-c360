# AGENTS.md

Agent-relevant conventions, gotchas, and operational principles. Read `plan.md` first — it is the architecture source of truth.

## Operational principles

- **Delegate whenever possible.** Use subagents (`task` tool with explore/general types) for file searches, code exploration, and multi-step tasks. Run independent subagent calls in parallel.
- **Verify against existing code, not memory.** Do not invent commands, tool versions, or directory structure. Before acting, check `plan.md`, then confirm against the actual filesystem.

## Repo status

Greenfield: `plan.md` is the primary specification until code lands in all four subsystems (`simulation/`, `dagster_pipeline/`, `dbt/`, `streamlit_app/`). Once code exists, the code is the source of truth for *what*; `plan.md` remains the source of truth for *why*.

## Two systems, don't conflate them
- **Simulation/generator** is **standalone** (cron / `simulation/scripts/`). Dagster does NOT run it.
- **Dagster** orchestrates only land→silver→gold→serve. Putting the generator inside Dagster is a design error.

## Everything is Indonesian — don't generate US/EU data
- Use Faker locale `id_ID` as the default. Names, phones, emails, addresses, currency, and behaviour all reflect Indonesian retail.
- **Phones**: Indonesian format `+62 812-...` / `0812-...`. Normalize to `+62...` in Silver. Mobile prefixes 0812–0899 (Telkomsel/Indosat/XL/Three/Smartfren); landlines 021 Jakarta / 022 Bandung / 031 Surabaya.
- **Emails**: Indonesian-name-based (`budi.santoso@gmail.com`, `toko-...@...co.id`). Same person often has a personal email and a separate business/support email.
- **Addresses**: full Indonesian structure — `Jl. ... No. .., RT 03/RW 02, Kel. .., Kec. .., Kota/Kab. .., Provinsi .., Kode Pos`. RT/RW sometimes joined, sometimes split; kelurahan/kode pos sometimes mismatched (deliberate).
- **Names**: include Balinese birth-order names (Wayan/Made/Nyoman/Ketut), Muslim names (Muhammad/Siti/Ahmad), honorifics (Bpk./Ibu/Sdr. sometimes present, sometimes not). Single-name elders exist — a real identity-resolution edge case.
- **Currency**: IDR only. Amounts rounded to hundreds/thousands; no real cents. Watch for `Rp 1.500.000` (dot-thousand-separator) vs `1.499.999,50` (comma-decimal) drift across sources — both are intentional.
- **Language**: CRM/support tickets in Bahasa Indonesia (`toko`, `pengembalian dana`, `ongkir`, `ganti rugi`). Dashboard labels in Bahasa or bilingual.
- **Behaviour**: payment methods = QRIS / COD / GoPay / OVO / DANA / ShopeePay / LinkAja / Bank Transfer (BCA/Mandiri/BRI/BNI). Store names use `Toko ...`, `CV ...`, `UD ...`. Seasonal spikes for Lebaran / Natal / Imlek / Tahun Baru (`holiday_mode` knob). "Jajan"-style small-ticket POS transactions are normal.

## Source-system identity keys (central to entity resolution)
- Legacy POS: **phone only**, no email. CSV is `ISO-8859-1` encoded on purpose → mojibake on accented/old-romanization letters (`José`→`Ã©`, `Yoesoef`) if read as UTF-8. This is intentional messiness, not a bug.
- E-commerce API: **email only**, ISO JSON, IDR amounts.
- CRM/Support (Postgres via Sling): both email + phone, ticket bodies in Bahasa, support-ticket emails sometimes differ from the e-commerce account email.
- Schema drift across POS CSV years (e.g. 2022 lacks `store_id`) is intentional.
- Indonesian date formats drift across sources: ISO in API, `DD/MM/YYYY` in POS, `YYYY-MM-DD HH24:MI:SS` in Postgres, `15 Agt 2024` (id month abbreviations: Jan/Feb/Mar/Apr/Mei/Jun/Jul/Agt/Sep/Okt/Nov/Des) occasionally leaking from CRM exports.

## Hard constraints
- Never write intermediate local files during Dagster landing — write Parquet straight to MinIO from memory.
- Daily volume target: 0–5,000 rows/day (total across all three sources, random per-day split). Pandas-in-memory + ClickHouse are comfortable in this range.
- Keep money in IDR end-to-end; never silently convert to USD/EUR anywhere in the pipeline. Loyalty tiers are IDR-banded (e.g. Gold ≥ Rp 10jt LTV, Silver Rp 2–10 jt, Churn-Risk < Rp 2 jt or dormant > 90 days).

## Common commands (once code exists — verify before trusting)
- Backfill a long history: `python simulation/scripts/backfill.py --days 365`
- Generate one retail day: `python simulation/scripts/run_day.py --date YYYY-MM-DD`
- Wipe simulation state + generated artifacts: `simulation/scripts/reset.sh`
- Infra up: `docker compose up -d`

## Infra topology (docker-compose, local)
MinIO, ClickHouse, Postgres (for CRM), Dagster daemon/webserver, plus the FastAPI mock e-commerce API.

## Where things live
- `simulation/` — generator + three mock sources (cron-driven), all Indonesian data via `id_ID`
- `dagster_pipeline/` — land→silver→gold→serve orchestration
- `dbt/` — silver (cleanse) + gold (dims/facts) SQL
- `streamlit_app/` — Customer 360 dashboard (Bahasa/bilingual labels)
- `plan.md` — full architecture; read it before non-trivial work