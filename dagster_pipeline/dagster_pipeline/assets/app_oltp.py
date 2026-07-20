import dagster as dg
import pandas as pd

from dagster_pipeline.resources import ClickHouseResource, PostgresResource
from dagster_pipeline.assets._helpers import (
    _column_schema,
    _ensure_bronze_schema,
    _insert_bronze,
    _iter_partition_windows,
    _read_bronze,
    _truncate_partition,
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")

_SINGLE_RUN = dg.BackfillPolicy.single_run()


@dg.asset(
    name="bronze_customers",
    description=(
        "Daily CDC slice of the customers table from app OLTP (Postgres), "
        "landed directly into ClickHouse bronze_customers. Captures only rows "
        "whose updated_at falls within the partition day (new customers and "
        "customers touched by an upsert that day). Contains complete identity "
        "data — name, email, phone, address, loyalty_tier, preferred_airline."
    ),
    group_name="bronze",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["table", "clickhouse"],
    partitions_def=daily_partitions,
    backfill_policy=_SINGLE_RUN,
)
def bronze_customers(
    context: dg.AssetExecutionContext,
    postgres: PostgresResource,
    clickhouse: ClickHouseResource,
):
    _ensure_bronze_schema(clickhouse)

    total_rows = 0
    schema_df = None
    for batch_date, window in _iter_partition_windows(context, daily_partitions):
        context.log.info(
            f"Landing customers CDC slice for {batch_date} ({window.start}..{window.end})"
        )
        _truncate_partition(clickhouse, "bronze_customers", batch_date)

        query = (
            "SELECT customer_id, email, phone, full_name, address, city, province, "
            "postal_code, loyalty_tier, preferred_airline, created_at, updated_at "
            "FROM customers "
            "WHERE updated_at >= %(start)s AND updated_at < %(end)s"
        )
        conn = postgres.get_connection()
        try:
            df = pd.read_sql_query(
                query, conn, params={"start": window.start, "end": window.end}
            )
        finally:
            conn.close()

        rows = _insert_bronze(clickhouse, "bronze_customers", df, batch_date)
        total_rows += rows
        if not df.empty and schema_df is None:
            schema_df = df
        context.log.info(f"Landed {rows} customer rows for {batch_date}")

    keys = context.partition_keys
    return dg.MaterializeResult(
        metadata={
            "dagster/column_schema": _column_schema(schema_df if schema_df is not None else pd.DataFrame()),
            "dagster/row_count": dg.MetadataValue.int(total_rows),
            "table": dg.MetadataValue.text("wanderfuel.bronze_customers"),
            "partitions": dg.MetadataValue.json(keys),
        }
    )


@dg.asset_check(
    asset=bronze_customers,
    description="Verify the landed customers slice contains at least one row",
)
def bronze_customers_not_empty(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_customers", keys)
    row_count = len(df)
    return dg.AssetCheckResult(
        passed=row_count > 0,
        metadata={
            "dagster/row_count": dg.MetadataValue.int(row_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_customers,
    description="Verify customer_id has no null values",
)
def bronze_customers_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_customers", keys)

    pk_col = "customer_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(
                    f"Column '{pk_col}' not found in partitions {keys} (empty result set)"
                ),
                "partitions": dg.MetadataValue.json(keys),
            },
        )

    null_count = int(df[pk_col].isna().sum())
    return dg.AssetCheckResult(
        passed=null_count == 0,
        metadata={
            "null_customer_ids": dg.MetadataValue.int(null_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_customers,
    description="Verify customer_id has no duplicate values within each partition",
)
def bronze_customers_unique_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_customers", keys)

    pk_col = "customer_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(
                    f"Column '{pk_col}' not found in partitions {keys} (empty result set)"
                ),
                "partitions": dg.MetadataValue.json(keys),
            },
        )

    # Duplicates per partition — same customer may legitimately appear on
    # multiple days (CDC slice per partition), so check within each
    # ingest_date partition.
    dup_count = 0
    if "ingest_date" in df.columns:
        for _, group in df.groupby("ingest_date"):
            dup_count += int(group[pk_col].duplicated().sum())
    else:
        dup_count = int(df[pk_col].duplicated().sum())

    return dg.AssetCheckResult(
        passed=dup_count == 0,
        metadata={
            "duplicate_customer_ids": dg.MetadataValue.int(dup_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset(
    name="bronze_hotel_bookings",
    description=(
        "Daily slice of the hotel_bookings table from app OLTP (Postgres), "
        "landed directly into ClickHouse bronze_hotel_bookings. Contains only "
        "bookings whose booking_ts falls within the partition day, linked to "
        "customers via customer_id FK."
    ),
    group_name="bronze",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["table", "clickhouse"],
    partitions_def=daily_partitions,
    backfill_policy=_SINGLE_RUN,
)
def bronze_hotel_bookings(
    context: dg.AssetExecutionContext,
    postgres: PostgresResource,
    clickhouse: ClickHouseResource,
):
    _ensure_bronze_schema(clickhouse)

    total_rows = 0
    schema_df = None
    for batch_date, window in _iter_partition_windows(context, daily_partitions):
        context.log.info(
            f"Landing hotel_bookings for {batch_date} ({window.start}..{window.end})"
        )
        _truncate_partition(clickhouse, "bronze_hotel_bookings", batch_date)

        query = (
            "SELECT booking_id, customer_id, hotel_name, hotel_city, check_in_date, "
            "check_out_date, room_type, guests, amount_idr, payment_method, "
            "booking_status, booking_ts "
            "FROM hotel_bookings "
            "WHERE booking_ts >= %(start)s AND booking_ts < %(end)s"
        )
        conn = postgres.get_connection()
        try:
            df = pd.read_sql_query(
                query, conn, params={"start": window.start, "end": window.end}
            )
        finally:
            conn.close()

        rows = _insert_bronze(clickhouse, "bronze_hotel_bookings", df, batch_date)
        total_rows += rows
        if not df.empty and schema_df is None:
            schema_df = df
        context.log.info(f"Landed {rows} hotel booking rows for {batch_date}")

    return dg.MaterializeResult(
        metadata={
            "dagster/column_schema": _column_schema(schema_df if schema_df is not None else pd.DataFrame()),
            "dagster/row_count": dg.MetadataValue.int(total_rows),
            "table": dg.MetadataValue.text("wanderfuel.bronze_hotel_bookings"),
            "partitions": dg.MetadataValue.json(context.partition_keys),
        }
    )


@dg.asset_check(
    asset=bronze_hotel_bookings,
    description="Verify the landed hotel_bookings slice contains at least one row",
)
def bronze_hotel_bookings_not_empty(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_hotel_bookings", keys)
    row_count = len(df)
    return dg.AssetCheckResult(
        passed=row_count > 0,
        metadata={
            "dagster/row_count": dg.MetadataValue.int(row_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_hotel_bookings,
    description="Verify booking_id has no null values",
)
def bronze_hotel_bookings_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_hotel_bookings", keys)

    pk_col = "booking_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(
                    f"Column '{pk_col}' not found in partitions {keys} (empty result set)"
                ),
                "partitions": dg.MetadataValue.json(keys),
            },
        )

    null_count = int(df[pk_col].isna().sum())
    return dg.AssetCheckResult(
        passed=null_count == 0,
        metadata={
            "null_booking_ids": dg.MetadataValue.int(null_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_hotel_bookings,
    description="Verify booking_id has no duplicate values within each partition",
)
def bronze_hotel_bookings_unique_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_hotel_bookings", keys)

    pk_col = "booking_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(
                    f"Column '{pk_col}' not found in partitions {keys} (empty result set)"
                ),
                "partitions": dg.MetadataValue.json(keys),
            },
        )

    dup_count = 0
    if "ingest_date" in df.columns:
        for _, group in df.groupby("ingest_date"):
            dup_count += int(group[pk_col].duplicated().sum())
    else:
        dup_count = int(df[pk_col].duplicated().sum())

    return dg.AssetCheckResult(
        passed=dup_count == 0,
        metadata={
            "duplicate_booking_ids": dg.MetadataValue.int(dup_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )