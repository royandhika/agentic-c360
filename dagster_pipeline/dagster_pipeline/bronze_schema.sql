-- Bronze landing schema for WanderFuel.
-- All bronze tables live in the `wanderfuel` database and are written to
-- directly by Dagster landing assets (replacing the previous MinIO-Parquet
-- bronze layer). Each table carries an `ingest_date Date` column matching
-- the Dagster daily partition key, used as the ClickHouse table partition
-- and as the silver-layer partition filter.
--
-- Engine choice: MergeTree (not ReplacingMergeTree). Bronze is an append-by-
-- partition landing zone; landers TRUNCATE the matching `ingest_date`
-- partition before inserting so re-materializations are idempotent. Silver
-- dbt models handle dedup via row_number() оконными функциями.

CREATE DATABASE IF NOT EXISTS wanderfuel;

-- ── app_oltp.customers ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wanderfuel.bronze_customers (
    customer_id      String,
    email            String,
    phone            String,
    full_name        Nullable(String),
    address          Nullable(String),
    city             Nullable(String),
    province         Nullable(String),
    postal_code      Nullable(String),
    loyalty_tier     Nullable(String),
    preferred_airline Nullable(String),
    created_at       DateTime,
    updated_at       DateTime,
    ingest_date      Date
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ingest_date)
ORDER BY (customer_id, updated_at);

-- ── app_oltp.hotel_bookings ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wanderfuel.bronze_hotel_bookings (
    booking_id       String,
    customer_id      String,
    hotel_name       String,
    hotel_city       String,
    check_in_date    Date,
    check_out_date   Date,
    room_type        String,
    guests           Int64,
    amount_idr       Int64,
    payment_method   String,
    booking_status   String,
    booking_ts       DateTime,
    ingest_date      Date
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ingest_date)
ORDER BY (booking_id, booking_ts);

-- ── vendor_api.flight_bookings ──────────────────────────────────────
-- Vendor API returns timestamps as ISO-8601 strings with +07:00 tz; the
-- silver layer parses them with parseDateTimeBestEffortOrNull, so bronze
-- keeps them as String to preserve the original representation exactly.
CREATE TABLE IF NOT EXISTS wanderfuel.bronze_flights (
    booking_ref      String,
    email            String,
    airline          String,
    flight_number    String,
    origin           String,
    destination      String,
    departure_ts     String,
    arrival_ts       String,
    passenger_name   String,
    seat_class       String,
    amount_idr       Int64,
    payment_method   String,
    booking_status   String,
    booking_ts       String,
    ingest_date      Date
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ingest_date)
ORDER BY (booking_ref, booking_ts);

-- ── vendor_api.experience_bookings ──────────────────────────────────
CREATE TABLE IF NOT EXISTS wanderfuel.bronze_experiences (
    booking_ref      String,
    email            String,
    experience_name  String,
    city             String,
    category         Nullable(String),
    activity_date    String,
    participants     Int64,
    amount_idr       Int64,
    payment_method   String,
    booking_status   String,
    booking_ts       String,
    ingest_date      Date
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ingest_date)
ORDER BY (booking_ref, booking_ts);

-- ── crm_sftp.tickets ─────────────────────────────────────────────────
-- resolved_at is null for open/in_progress tickets -> Nullable.
CREATE TABLE IF NOT EXISTS wanderfuel.bronze_tickets (
    ticket_id        String,
    customer_email   String,
    customer_phone   String,
    customer_name    String,
    subject          String,
    body             String,
    status           String,
    priority         String,
    channel          String,
    created_at       String,
    resolved_at      Nullable(String),
    category         String,
    agent_name       String,
    ingest_date      Date
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ingest_date)
ORDER BY (ticket_id, created_at);