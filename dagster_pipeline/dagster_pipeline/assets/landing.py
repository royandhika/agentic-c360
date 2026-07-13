from datetime import datetime

import dagster as dg
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dagster_pipeline.resources import MinIOResource, PostgresResource

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")

_DTYPE_MAP = {
    "object": "string",
    "str": "string",
    "int64": "integer",
    "Int64": "integer",
    "float64": "float",
    "Float64": "float",
    "datetime64[ns]": "datetime",
    "datetime64[us]": "datetime",
    "datetime64[ns, UTC]": "datetime",
}


def _map_dtype(dtype) -> str:
    return _DTYPE_MAP.get(str(dtype), str(dtype))


def _build_path(bucket: str, batch_date: str) -> str:
    dt = datetime.strptime(batch_date, "%Y-%m-%d")
    return (
        f"s3://{bucket}/app_oltp/customers"
        f"/year={dt.year}/month={dt.month:02d}/day={dt.day:02d}"
        f"/customers_{dt.strftime('%Y%m%d')}.parquet"
    )


def _read_parquet(minio: MinIOResource, path: str) -> pd.DataFrame:
    s3 = minio.get_s3()
    with s3.open(path, "rb") as f:
        table = pq.read_table(f)
    return table.to_pandas()


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

    s3 = minio.get_s3()
    path = _build_path(minio.bucket, batch_date)

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
    path = _build_path(minio.bucket, batch_date)
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
    path = _build_path(minio.bucket, batch_date)
    df = _read_parquet(minio, path)

    null_count = int(df["customer_id"].isna().sum())
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
    path = _build_path(minio.bucket, batch_date)
    df = _read_parquet(minio, path)

    dup_count = int(df["customer_id"].duplicated().sum())
    passed = dup_count == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "duplicate_customer_ids": dg.MetadataValue.int(dup_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )
