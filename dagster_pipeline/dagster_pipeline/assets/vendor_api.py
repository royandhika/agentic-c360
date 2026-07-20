from datetime import timedelta

import dagster as dg
import pandas as pd

from dagster_pipeline.resources import ClickHouseResource, VendorApiResource
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


def _fetch_paginated(api: VendorApiResource, endpoint: str, since: str, until: str) -> list[dict]:
    results = []
    offset = 0
    limit = 10000
    while True:
        params = {"since": since, "until": until, "limit": limit, "offset": offset}
        body = api.get(endpoint, params)
        results.extend(body["data"])
        if offset + limit >= body["total"]:
            break
        offset += limit
    return results


@dg.asset(
    name="bronze_flights",
    description=(
        "Daily slice of flight bookings from the Vendor API, landed directly "
        "into ClickHouse bronze_flights. Fetches bookings whose booking_ts "
        "falls within the partition day via the /flights endpoint's "
        "since/until query params (inclusive bounds with +07:00 offset)."
    ),
    group_name="bronze",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["table", "clickhouse"],
    partitions_def=daily_partitions,
    backfill_policy=_SINGLE_RUN,
)
def bronze_flights(
    context: dg.AssetExecutionContext,
    vendor_api: VendorApiResource,
    clickhouse: ClickHouseResource,
):
    _ensure_bronze_schema(clickhouse)

    total_rows = 0
    schema_df = None
    for batch_date, window in _iter_partition_windows(context, daily_partitions):
        # Vendor API uses inclusive bounds `booking_ts <= until`. Use the
        # final second of the day WITH the +07:00 offset so rows stamped
        # `<day>T23:59:59+07:00` are included.
        until_inclusive = (window.end - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S+07:00")
        since = window.start.strftime("%Y-%m-%dT%H:%M:%S+07:00")
        context.log.info(
            f"Landing flights for {batch_date} ({since}..{until_inclusive})"
        )

        _truncate_partition(clickhouse, "bronze_flights", batch_date)
        data = _fetch_paginated(vendor_api, "flights", since, until_inclusive)
        df = pd.DataFrame(data)

        rows = 0
        if not df.empty:
            rows = _insert_bronze(clickhouse, "bronze_flights", df, batch_date)
            if schema_df is None:
                schema_df = df
        context.log.info(f"Landed {rows} flight rows for {batch_date}")
        total_rows += rows

    metadata = {
        "dagster/row_count": dg.MetadataValue.int(total_rows),
        "table": dg.MetadataValue.text("wanderfuel.bronze_flights"),
        "partitions": dg.MetadataValue.json(context.partition_keys),
    }
    if schema_df is not None:
        metadata["dagster/column_schema"] = _column_schema(schema_df)

    return dg.MaterializeResult(metadata=metadata)


@dg.asset_check(
    asset=bronze_flights,
    description="Verify the landed flights slice contains at least one row",
)
def bronze_flights_not_empty(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_flights", keys)
    row_count = len(df)
    return dg.AssetCheckResult(
        passed=row_count > 0,
        metadata={
            "dagster/row_count": dg.MetadataValue.int(row_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_flights,
    description="Verify booking_ref has no null values",
)
def bronze_flights_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_flights", keys)

    pk_col = "booking_ref"
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
            "null_booking_refs": dg.MetadataValue.int(null_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_flights,
    description="Verify booking_ref has no duplicate values within each partition",
)
def bronze_flights_unique_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_flights", keys)

    pk_col = "booking_ref"
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
            "duplicate_booking_refs": dg.MetadataValue.int(dup_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset(
    name="bronze_experiences",
    description=(
        "Daily slice of experience bookings from the Vendor API, landed "
        "directly into ClickHouse bronze_experiences. Fetches bookings whose "
        "booking_ts falls within the partition day via the /experiences "
        "endpoint's since/until query params."
    ),
    group_name="bronze",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["table", "clickhouse"],
    partitions_def=daily_partitions,
    backfill_policy=_SINGLE_RUN,
)
def bronze_experiences(
    context: dg.AssetExecutionContext,
    vendor_api: VendorApiResource,
    clickhouse: ClickHouseResource,
):
    _ensure_bronze_schema(clickhouse)

    total_rows = 0
    schema_df = None
    for batch_date, window in _iter_partition_windows(context, daily_partitions):
        until_inclusive = (window.end - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S+07:00")
        since = window.start.strftime("%Y-%m-%dT%H:%M:%S+07:00")
        context.log.info(
            f"Landing experiences for {batch_date} ({since}..{until_inclusive})"
        )

        _truncate_partition(clickhouse, "bronze_experiences", batch_date)
        data = _fetch_paginated(vendor_api, "experiences", since, until_inclusive)
        df = pd.DataFrame(data)

        rows = 0
        if not df.empty:
            rows = _insert_bronze(clickhouse, "bronze_experiences", df, batch_date)
            if schema_df is None:
                schema_df = df
        context.log.info(f"Landed {rows} experience rows for {batch_date}")
        total_rows += rows

    metadata = {
        "dagster/row_count": dg.MetadataValue.int(total_rows),
        "table": dg.MetadataValue.text("wanderfuel.bronze_experiences"),
        "partitions": dg.MetadataValue.json(context.partition_keys),
    }
    if schema_df is not None:
        metadata["dagster/column_schema"] = _column_schema(schema_df)

    return dg.MaterializeResult(metadata=metadata)


@dg.asset_check(
    asset=bronze_experiences,
    description="Verify the landed experiences slice contains at least one row",
)
def bronze_experiences_not_empty(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_experiences", keys)
    row_count = len(df)
    return dg.AssetCheckResult(
        passed=row_count > 0,
        metadata={
            "dagster/row_count": dg.MetadataValue.int(row_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_experiences,
    description="Verify booking_ref has no null values",
)
def bronze_experiences_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_experiences", keys)

    pk_col = "booking_ref"
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
            "null_booking_refs": dg.MetadataValue.int(null_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_experiences,
    description="Verify booking_ref has no duplicate values within each partition",
)
def bronze_experiences_unique_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_experiences", keys)

    pk_col = "booking_ref"
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
            "duplicate_booking_refs": dg.MetadataValue.int(dup_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )