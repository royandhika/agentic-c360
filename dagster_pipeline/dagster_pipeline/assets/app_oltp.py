import dagster as dg
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dagster_pipeline.resources import MinIOResource, PostgresResource
from dagster_pipeline.assets._helpers import (
    _build_path,
    _map_dtype,
    _read_parquet,
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")


@dg.asset(
    key_prefix=["bronze"],
    description=(
        "Daily snapshot of the customers table from app OLTP (Postgres), landed to MinIO as Parquet. "
        "Contains complete customer identity data — name, email, phone, address, "
        "loyalty_tier, preferred_airline. "
        "Full-snapshot partitioning provides an audit trail per day and enables "
        "point-in-time recovery of customer state."
    ),
    group_name="landing",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["parquet", "s3"],
    partitions_def=daily_partitions,
)
def customers(
    context: dg.AssetExecutionContext,
    postgres: PostgresResource,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    context.log.info(f"Landing customers snapshot for {batch_date}")

    conn = postgres.get_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()

    column_schema = dg.TableSchema(
        columns=[
            dg.TableColumn(name=col, type=_map_dtype(dtype))
            for col, dtype in df.dtypes.items()
        ]
    )

    path = _build_path(minio.bucket, "app_oltp", "customers", batch_date)

    s3 = minio.get_s3()
    table = pa.Table.from_pandas(df)
    with s3.open(path, "wb") as f:
        pq.write_table(table, f)

    rows = len(df)
    context.log.info(f"Wrote {rows} rows to {path}")

    return dg.MaterializeResult(
        metadata={
            "dagster/column_schema": dg.MetadataValue.table_schema(column_schema),
            "dagster/row_count": dg.MetadataValue.int(rows),
            "path": dg.MetadataValue.text(path),
            "batch_date": dg.MetadataValue.text(batch_date),
        }
    )


@dg.asset_check(
    asset=customers,
    description="Verify the landed customers snapshot contains at least one row",
)
def customers_not_empty(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "app_oltp", "customers", batch_date)
    df = _read_parquet(minio, path)
    row_count = len(df)

    passed = row_count > 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "dagster/row_count": dg.MetadataValue.int(row_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset_check(
    asset=customers,
    description="Verify customer_id has no null values",
)
def customers_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "app_oltp", "customers", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "customer_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(f"Column '{pk_col}' not found in partition data (empty result set)"),
                "partition": dg.MetadataValue.text(batch_date),
            },
        )

    null_count = int(df[pk_col].isna().sum())
    passed = null_count == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "null_customer_ids": dg.MetadataValue.int(null_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset_check(
    asset=customers,
    description="Verify customer_id has no duplicate values",
)
def customers_unique_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "app_oltp", "customers", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "customer_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(f"Column '{pk_col}' not found in partition data (empty result set)"),
                "partition": dg.MetadataValue.text(batch_date),
            },
        )

    dup_count = int(df[pk_col].duplicated().sum())
    passed = dup_count == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "duplicate_customer_ids": dg.MetadataValue.int(dup_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset(
    key_prefix=["bronze"],
    description=(
        "Daily snapshot of the hotel_bookings table from app OLTP (Postgres), landed to MinIO as Parquet. "
        "Contains hotel reservation data linked to customers via customer_id FK."
    ),
    group_name="landing",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["parquet", "s3"],
    partitions_def=daily_partitions,
)
def hotel_bookings(
    context: dg.AssetExecutionContext,
    postgres: PostgresResource,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    context.log.info(f"Landing hotel_bookings snapshot for {batch_date}")

    conn = postgres.get_connection()
    df = pd.read_sql_query("SELECT * FROM hotel_bookings", conn)
    conn.close()

    column_schema = dg.TableSchema(
        columns=[
            dg.TableColumn(name=col, type=_map_dtype(dtype))
            for col, dtype in df.dtypes.items()
        ]
    )

    path = _build_path(minio.bucket, "app_oltp", "hotel_bookings", batch_date)

    s3 = minio.get_s3()
    table = pa.Table.from_pandas(df)
    with s3.open(path, "wb") as f:
        pq.write_table(table, f)

    rows = len(df)
    context.log.info(f"Wrote {rows} rows to {path}")

    return dg.MaterializeResult(
        metadata={
            "dagster/column_schema": dg.MetadataValue.table_schema(column_schema),
            "dagster/row_count": dg.MetadataValue.int(rows),
            "path": dg.MetadataValue.text(path),
            "batch_date": dg.MetadataValue.text(batch_date),
        }
    )


@dg.asset_check(
    asset=hotel_bookings,
    description="Verify the landed hotel_bookings snapshot contains at least one row",
)
def hotel_bookings_not_empty(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "app_oltp", "hotel_bookings", batch_date)
    df = _read_parquet(minio, path)
    row_count = len(df)

    passed = row_count > 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "dagster/row_count": dg.MetadataValue.int(row_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset_check(
    asset=hotel_bookings,
    description="Verify booking_id has no null values",
)
def hotel_bookings_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "app_oltp", "hotel_bookings", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "booking_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(f"Column '{pk_col}' not found in partition data (empty result set)"),
                "partition": dg.MetadataValue.text(batch_date),
            },
        )

    null_count = int(df[pk_col].isna().sum())
    passed = null_count == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "null_booking_ids": dg.MetadataValue.int(null_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset_check(
    asset=hotel_bookings,
    description="Verify booking_id has no duplicate values",
)
def hotel_bookings_unique_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "app_oltp", "hotel_bookings", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "booking_id"
    if pk_col not in df.columns:
        return dg.AssetCheckResult(
            passed=False,
            metadata={
                "error": dg.MetadataValue.text(f"Column '{pk_col}' not found in partition data (empty result set)"),
                "partition": dg.MetadataValue.text(batch_date),
            },
        )

    dup_count = int(df[pk_col].duplicated().sum())
    passed = dup_count == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "duplicate_booking_ids": dg.MetadataValue.int(dup_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )
