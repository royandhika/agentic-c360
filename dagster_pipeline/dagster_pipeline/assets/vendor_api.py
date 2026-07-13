import dagster as dg
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dagster_pipeline.resources import MinIOResource, VendorApiResource
from dagster_pipeline.assets._helpers import (
    _build_path,
    _map_dtype,
    _read_parquet,
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")


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
    key_prefix=["bronze"],
    description=(
        "Daily snapshot of flight bookings from the Vendor API, landed to MinIO as Parquet. "
        "Contains flight reservation data indexed by booking_ref and email."
    ),
    group_name="landing",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["parquet", "s3"],
    partitions_def=daily_partitions,
)
def flights(
    context: dg.AssetExecutionContext,
    vendor_api: VendorApiResource,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    context.log.info(f"Landing flights for {batch_date}")

    since = f"{batch_date}T00:00:00"
    until = f"{batch_date}T23:59:59"

    data = _fetch_paginated(vendor_api, "flights", since, until)
    df = pd.DataFrame(data)

    column_schema = None
    if len(df) > 0:
        column_schema = dg.TableSchema(
            columns=[
                dg.TableColumn(name=col, type=_map_dtype(dtype))
                for col, dtype in df.dtypes.items()
            ]
        )

    path = _build_path(minio.bucket, "vendor_api", "flights", batch_date)

    s3 = minio.get_s3()
    table = pa.Table.from_pandas(df)
    with s3.open(path, "wb") as f:
        pq.write_table(table, f)

    rows = len(df)
    context.log.info(f"Wrote {rows} rows to {path}")

    metadata = {
        "dagster/row_count": dg.MetadataValue.int(rows),
        "path": dg.MetadataValue.text(path),
        "batch_date": dg.MetadataValue.text(batch_date),
    }
    if column_schema:
        metadata["dagster/column_schema"] = dg.MetadataValue.table_schema(column_schema)

    return dg.MaterializeResult(metadata=metadata)


@dg.asset_check(
    asset=flights,
    description="Verify the landed flights snapshot contains at least one row",
)
def flights_not_empty(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "vendor_api", "flights", batch_date)
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
    asset=flights,
    description="Verify booking_ref has no null values",
)
def flights_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "vendor_api", "flights", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "booking_ref"
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
            "null_booking_refs": dg.MetadataValue.int(null_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset_check(
    asset=flights,
    description="Verify booking_ref has no duplicate values",
)
def flights_unique_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "vendor_api", "flights", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "booking_ref"
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
            "duplicate_booking_refs": dg.MetadataValue.int(dup_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset(
    key_prefix=["bronze"],
    description=(
        "Daily snapshot of experience bookings from the Vendor API, landed to MinIO as Parquet. "
        "Contains experience/tour reservation data indexed by booking_ref and email."
    ),
    group_name="landing",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["parquet", "s3"],
    partitions_def=daily_partitions,
)
def experiences(
    context: dg.AssetExecutionContext,
    vendor_api: VendorApiResource,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    context.log.info(f"Landing experiences for {batch_date}")

    since = f"{batch_date}T00:00:00"
    until = f"{batch_date}T23:59:59"

    data = _fetch_paginated(vendor_api, "experiences", since, until)
    df = pd.DataFrame(data)

    column_schema = None
    if len(df) > 0:
        column_schema = dg.TableSchema(
            columns=[
                dg.TableColumn(name=col, type=_map_dtype(dtype))
                for col, dtype in df.dtypes.items()
            ]
        )

    path = _build_path(minio.bucket, "vendor_api", "experiences", batch_date)

    s3 = minio.get_s3()
    table = pa.Table.from_pandas(df)
    with s3.open(path, "wb") as f:
        pq.write_table(table, f)

    rows = len(df)
    context.log.info(f"Wrote {rows} rows to {path}")

    metadata = {
        "dagster/row_count": dg.MetadataValue.int(rows),
        "path": dg.MetadataValue.text(path),
        "batch_date": dg.MetadataValue.text(batch_date),
    }
    if column_schema:
        metadata["dagster/column_schema"] = dg.MetadataValue.table_schema(column_schema)

    return dg.MaterializeResult(metadata=metadata)


@dg.asset_check(
    asset=experiences,
    description="Verify the landed experiences snapshot contains at least one row",
)
def experiences_not_empty(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "vendor_api", "experiences", batch_date)
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
    asset=experiences,
    description="Verify booking_ref has no null values",
)
def experiences_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "vendor_api", "experiences", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "booking_ref"
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
            "null_booking_refs": dg.MetadataValue.int(null_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset_check(
    asset=experiences,
    description="Verify booking_ref has no duplicate values",
)
def experiences_unique_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "vendor_api", "experiences", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "booking_ref"
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
            "duplicate_booking_refs": dg.MetadataValue.int(dup_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )
