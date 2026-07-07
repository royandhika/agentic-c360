# Source System Specifications
Technical specification for Bronze extraction and Silver cleansing — data team reference.

This document defines the schemas, encodings, cadences, and deliberate error modes of each simulated source system. The Dagster Bronze layer must consume data that matches these contracts exactly. The Silver cleansing layer must tolerate all documented quirks.

The simulation produces three source streams daily. Schemas below.

**Sources at a glance**

| # | Source | Platform / Interface | Cadence | Format | Encoding | Identity Key | ~Daily Volume |
|---|--------|----------------------|---------|--------|----------|--------------|---------------|
| 1 | E-commerce orders | FastAPI HTTP API (`GET /orders?since=`) | Streaming / on-demand pull | JSON (paginated) | UTF-8 | **email** | ~0–3,500 rows |
| 2 | Legacy POS sales | Daily CSV file in `sources/inbox/pos/` | Daily drop, ~02:00 WIB next day | CSV | **ISO-8859-1** (mojibake-by-design) | **phone** | ~0–1,500 rows |
| 3 | CRM/Support | Postgres tables, extracted via Sling | Daily CDC snapshot | Postgres rows → Parquet via Sling | UTF-8 | **email + phone** | ~0–250 rows |

Daily volume is configurable (`simulation/config.yaml` `daily_volume`, 0–5k total across sources, random per day). Holiday-mode can take any source to 100% of its cap (Lebaran 3x, others 1.5-2.5x).

---

## 1. E-commerce API (online orders)

**Endpoint:** `GET /orders?since={ISO8601}&limit={n}&offset={n}` — paginated JSON.
**Headers:** `Content-Type: application/json; charset=utf-8`.
**Auth:** static bearer token (for realism; mocked).
**Latency:** adds ~50–200ms random delay to mimic a real API.
**Paginated:** 100 orders per page; `next` cursor returned in payload until exhausted.

### Payload shape (JSON array of order objects)

```json
{
  "order_id": "ORD-20240815-000123",
  "order_ts": "2024-08-15T10:30:12+07:00",
  "channel": "web",
  "status": "paid",
  "payment_method": "QRIS",
  "currency": "IDR",
  "grand_total_idr": 1580000,
  "shipping_fee_idr": 25000,
  "discount_idr": 0,
  "customer": {
    "email": "Budi.Santoso@gmail.com",
    "phone": "+62 812-3456-7890",
    "name": "Budi Santoso",
    "ouvert_address": "Jl. Merdeka No. 17, RT 03/RW 02, Kel. Menteng, Kec. Menteng, Jakarta Pusat, DKI Jakarta, 10110"
  },
  "line_items": [
    {"sku": "KOP-ARAB-250", "name": "Kopi Arabika 250g", "qty": 2, "unit_price_idr": 780000},
    {"sku": "GULA-AREN-500", "name": "Gula Aren 500g", "qty": 1, "unit_price_idr": 25000}
  ]
}
```

### Schema

| Column | Type | Notes |
|---|---|---|
| order_id | string | `ORD-YYYYMMDD-NNNNNN`, globally unique |
| order_ts | ISO8601 string | `+07:00` (WIB) offset always present |
| channel | string enum | `web`, `android`, `ios`, `marketplace` |
| status | string enum | `paid`, `shipped`, `delivered`, `cancelled`, `refunded` |
| payment_method | string enum | `QRIS`, `GoPay`, `OVO`, `DANA`, `ShopeePay`, `LinkAja`, `BCA`, `Mandiri`, `BNI`, `BRI`, `COD` |
| currency | string | Always `IDR` |
| grand_total_idr | integer | Rupiah, no cents (rounded to nearest 100) |
| shipping_fee_idr | integer | Can be 0 (free-ongkir promo) |
| discount_idr | integer | Can be 0 |
| customer.email | string | **Identity key**. Mixed case possible (e.g. `Budi.Santoso@gmail.com`); Silver lowercases |
| customer.phone | string | E.164-ish `+62 812-...`; sometimes missing/null if customer opted out |
| customer.name | string | Indonesian name (`Budi Santoso`, `Siti Nurhaliza`, `Wayan Sutedja`) |
| customer.address | string | Full Indonesian address (see "Local context") |
| line_items[].sku | string | SKU code, stable across orders |
| line_items[].name | string | Indonesian product name |
| line_items[].qty | integer | ≥ 1 |
| line_items[].unit_price_idr | integer | At time of order; price is point-in-time, ref pricing is not enforced here |

### Quirks (intentional, documented)
- Emails may have mixed case (`John.Doe@Example.COM`), domain typos (`gnail.com`, `gmaill.com`), trailing whitespace, gmail `+` aliases.
- `phone` may be null for ~5% of orders (customer opted out of phone capture).
- `grand_total_idr` occasionally ≠ `sum(line_items.qty * unit_price_idr) + shipping_fee_idr - discount_idr` by ±Rp 100 due to a deliberately injected "rounding bug" (~0.1% of rows).
- Retries/de-dupes: same `order_id` may appear twice within a 24h window if the API is "re-queried" — dedupe by `order_id` in Silver.
- A refunded order keeps its `order_id` but `status` flips from `paid`→`refunded` and a new negative line item may be appended on a later day.

---

## 2. Legacy POS (in-store / brick-and-mortar)

**Delivery:** one CSV per retail day, dropped at `simulation/sources/inbox/pos/sales_YYYYMMDD.csv`.
**Cadence:** generated shortly after 23:59 WIB the same day; occasionally a prior-day file re-arrives 1–3 days late (mimics late store-DC uploads). Filenames use the *business* date, not the arrival date.
**Encoding:** `ISO-8859-1` (Latin-1) — *intentionally*. Accented Indonesian letters / older romanizations (`José`, `Yoesoef`) become mojibake if read as UTF-8. This is deliberate messiness, not a bug.
**Delimiter:** comma, but ~0.5% of rows have an extra unescaped comma inside an address field (no quoting) — Silver must tolerate.
**Header row:** present, but column drift across years (see schema drift below).

### Schema (2024 and onwards)

| Column | Type | Notes |
|---|---|---|
| receipt_no | string | `REC-NNNNNNN`, unique within a store per day |
| txn_date | string | **`DD/MM/YYYY`** (Indonesian POS convention, not ISO) |
| txn_time | string | `HH:MM:SS` (24h WIB, no timezone) |
| store_id | string | Indonesian retail store code (`TKJ-CGR-01`) — **present 2024+** |
| store_name | string | `Toko Sejahtera`, `CV Makmur Jaya`, `UD Karya Abadi`, `Warung Bu Endang` |
| kasir_id | string | Cashier ID |
| customer_phone | string | **Identity key.** `0812-3456-7890`, `+62 812-...`, `021-1234567`, sometimes `81234567890` (missing leading 0). ~3% null ('' or `TIDAK ADA`) for walk-ins who refused to give phone. Phone placeholder `000-000-0000` used too. |
| customer_name | string | Indonesian name; sometimes honorific (`Bpk. Budi Santoso`), sometimes ALL CAPS, single-name elders (`Sukarman`), accents mojibake due to encoding |
| product_code | string | SKU; legacy codes may differ from e-com SKU for the same product (intentional, Silver will map) |
| product_name | string | Indonesian (`Kopi Arabika 250g`, `Gula Aren 500g`) |
| qty | integer | ≥ 1 |
| unit_price_idr | integer | No cents; `Rp` prefix sometimes present (`Rp 78.000`), sometimes not (`78000`) |
| line_total_idr | integer | Sometimes `*`-not-`+`-consistent due to manual key-in errors (~0.1% of rows off by Rp 50-100) |
| payment_method | string | `Cash`, `QRIS`, `Debit BCA`, `Kredit Mandiri`, `GoPay` (e-wallets less common in POS than online) |
| cashier_shift | string | `Pagi` / `Siang` / `Malam` / `Tutup` |
| void_flag | string | `Y` / `N` / `TIDAK ADA` (sentinel-nullable) |

### Schema drift (intentional)
| POS file year | Replaces / differs | Notes |
|---|---|---|
| 2022 and earlier | `store_id` column missing | Silver must default to `UNKNOWN-LEGACY` or infer from `store_name` |
| 2022 and earlier | `payment_method` values include retired `Voucher Fisik`, `Kupon` | Must map in Silver lookup |
| 2023 | adds `store_id` and `kasir_id` columns | |
| 2024+ | adds `cashier_shift`, `void_flag`; adds `QRIS` as a common `payment_method` | |
| All years | `txn_date` uses `DD/MM/YYYY` — never ISO | Don't let dbt infer |

### Quirks (intentional, documented)
- ~0.5% rows have an unescaped comma inside `customer_name`/address → field-shifts-to-the-right on naive CSV parse. Silver must use a separator-tolerant reader (e.g. pandas with `on_bad_lines='warn'` then manual fixups) or split by fixed width.
- ~0.3% rows are duplicate re-scans with a Rp 1–100 diff on `line_total_idr` (cashier re-keyed after customer disputed price). Dedupe by `(receipt_no, product_code, qty)` keeping the latest by `txn_time`.
- Single-name customers exist for older/religious-name-only customers (`Sukarman`, `Wirawan`) — Silver must keep as-is, entity resolution must match on phone.
- Phone variants are rampant: `0812-3456 7890`, `081234567890`, `+62812...`, `812...` (leading 0 stripped). Silver normalizes to `+62...`.
- Late file appending: `sales_20240812.csv` may appear in the `0815` drop. Bronze must re-scan the inbox and pick up by file mtime.

---

## 3. CRM / Support (Postgres → Sling → MinIO)

**Source:** local Postgres database `crm_mock`, extracted via **Sling** into MinIO Parquet. Run by Dagster Bronze daily CDC snapshot.
**Cadence:** snapshot at 01:30 WIB daily (after midnight, mimics nightly CRM sync).
**Encoding:** UTF-8 (Postgres default).

### Tables

#### 3a. `customers`

| Column | Postgres type | Notes |
|---|---|---|
| customer_id | BIGINT PK | CRM's own surrogate ID, NOT the same as the resolved `dim_customer.resolved_customer_id` later |
| email | TEXT | Always present, may differ from the e-commerce account email (customer registered with work email `budi@cv-makmur.com` but shops online as `budi.santoso@gmail.com`) |
| phone | TEXT | Always present; can be mobile or landline |
| full_name | TEXT | From support agent capture; may be honorific (`Bpk. Budi Santoso`), ALL CAPS, single-name (`Sukarman`), or use differing romanization (`Yusuf` vs `Yoesoef`) |
| created_at | TIMESTAMP | `YYYY-MM-DD HH24:MI:SS` timezone-less (assumed WIB) |
| updated_at | TIMESTAMP | |
| preferred_contact | TEXT enum | `email`, `whatsapp`, `phone`, `sms` |
| lifetime_value_idr | BIGINT | CRM-side snapshot — may lag Gold `clv_idr` by days; can be 0/null for new customers |
| address | TEXT | May be freeform (`Jl. Merdeka No. 17 RT3/RW2》) inconsistent with e-com `customer.address` even for the same human |
| city_prov | TEXT | e.g. `Jakarta Pusat, DKI Jakarta` |
| is_vip | BOOLEAN | CRM-managed flag, sometimes disagreeing with IDR-tier logic in Gold |

#### 3b. `tickets` (support cases)

| Column | Postgres type | Notes |
|---|---|---|
| ticket_id | BIGINT PK | |
| customer_id | BIGINT FK | |
| subject | TEXT | In Bahasa Indonesia (`"Paket belum sampai"`, `"Permintaan pengembalian dana"`, `"Barang rusak - ganti rugi"`) |
| body | TEXT | Bahasa, possibly short (`"tolong dicek ya mob"`, `"dt-05-rt-10 jalan kelapa dua"`) |
| status | TEXT enum | `open`, `pending_cust`, `waiting_3rd_party`, `resolved`, `closed`, `escalated` |
| priority | TEXT enum | `low`, `normal`, `high`, `urgent` |
| channel | TEXT enum | `email`, `whatsapp`, `phone`, `web_form`, `instagram`, `twitter` |
| created_at | TIMESTAMP | timezone-less WIB |
| resolved_at | TIMESTAMP NULL | |
| resolution_note | TEXT NULL | Bahasa |
| category | TEXT enum | `shipping`, `refund`, `product_quality`, `payment`, `account`, `other` |
| contact_email_snapshot | TEXT | The email the customer used *on this ticket* — may differ from `customers.email` (they used their spouse's email). Often the source of identity-fragmentation clues. |

#### 3c. `interactions` (per-ticket events)

| Column | Postgres type | Notes |
|---|---|---|
| interaction_id | BIGINT PK | |
| ticket_id | BIGINT FK | |
| agent_id | TEXT | |
| agent_name | TEXT | Indonesian name |
| ts | TIMESTAMP | |
| direction | TEXT enum | `inbound`, `outbound` |
| channel | TEXT enum | `email`, `whatsapp`, `phone`, `chat` |
| note | TEXT | Bahasa; may be cryptic (`"udah dijelaskan"`, `"menunggu respon cust"`) |

### Quirks (intentional, documented)
- `tickets.contact_email_snapshot` deliberately differs from `customers.email` for ~15% of tickets — this is material to the identity-resolution puzzle.
- `customers.lifetime_value_idr` may be 0 or null for new signups; do not use as source-of-truth LTV (compute from `fact_transactions` in Gold).
- Some `customers` rows correspond to phone-only in-store customers retroactively added to CRM after a support call (= the bridge from POS-only to e-com-only profile). Always check both `email` and `phone`, not just email.
- No soft-deletes — closed tickets remain forever.
- Timezone is implicit (WIB, `Asia/Jakarta`); no `+07:00` offset is stored. Bronze/Bronze-to-Silver must stamp timezone on摄取.

---

## Cross-source identity fragmentation (the puzzle)

A single human can leave matching clues across all three sources:

| Source | Identifier captured | Example |
|---|---|---|
| POS | phone only | `+62 812-3456-7890`, name `Budi Santoso` |
| E-commerce | email only | `Budi.Santoso@gmail.com`, address `Jl. Merdeka No. 17,...,10110` |
| CRM | email + phone | email `budi@cv-makmur.com` (work!), phone `+62 812-3456-7890` (= POS phone) |
| CRM ticket | email snapshot | `budi.santoso@gmail.com` (= e-commerce email, lowercased) |

Silver must normalize phone to `+62...`, lowercase email, then Gold's entity-resolution logic merges on shared phone or email with a confidence score. Same phone across systems ⇒ high confidence; ticket email-only match to e-commerce ⇒ medium.

---

## Cadence — daily timeline (WIB)

| Time | Event |
|---|---|
| 00:00 | `run_day.py --date <today>` triggered by cron → writes new rows to ecom SQLite store, drops `sales_YYYYMMDD.csv`, inserts into CRM Postgres |
| 01:30 | Dagster Bronze snapshot run scheduled: pulls ecom orders, scans POS inbox, replica-via-Slings CRM → MinIO Parquet |
| 02:00 | Silver dbt models run (cleanse) → ClickHouse |
| 02:30 | Gold dbt models run (entity resolution + CLV + tiers) → ClickHouse |
| ~09:00 | Streamlit dashboard refreshed; users browse Customer 360 |

All times WIB (Asia/Jakarta). Backfill via `run_day.py --date YYYY-MM-DD` replays the timeline retroactively with a fixed seed.

---

## Operational SLOs (Bronze SLO targets — verify once Dagster extraction is deployed)

- E-com API pagination: ≤ 200ms/page 95th percentile.
- POS CSV files: each ≤ 2 MB (0–1.5k rows × ~20 cols).
- CRM snapshot via Sling: full extract in < 60s; Sling `mode: snapshot` with a watermark on `updated_at`.
- Bronze → Gold elapsed: target < 20 min wall-clock for a 5k-row day.

---

## Cross-references
- `plan.md`
- `AGENTS.md`
- `simulation/src/id_locales.py`