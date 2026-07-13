from datetime import datetime

import dagster as dg
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dagster_pipeline.resources import MinIOResource, SFTPSourceResource
from dagster_pipeline.assets._helpers import (
    _build_path,
    _map_dtype,
    _read_parquet,
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")


@dg.asset(
    key_prefix=["bronze"],
    description=(
        "Daily snapshot of CRM support tickets from SFTP, landed to MinIO as Parquet. "
        "Contains support interactions in Bahasa Indonesia with customer identity data "
        "(email + phone) used as the identity bridge between sources."
    ),
    group_name="landing",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["parquet", "s3"],
    partitions_def=daily_partitions,
)
def tickets(
    context: dg.AssetExecutionContext,
    crm_sftp: SFTPSourceResource,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    context.log.info(f"Landing CRM tickets for {batch_date}")

    dt = datetime.strptime(batch_date, "%Y-%m-%d")
    filename = f"tickets_{dt.strftime('%Y%m%d')}.json"

    data = crm_sftp.read_json(filename)
    df = pd.DataFrame(data)

    column_schema = None
    if len(df) > 0:
        column_schema = dg.TableSchema(
            columns=[
                dg.TableColumn(name=col, type=_map_dtype(dtype))
                for col, dtype in df.dtypes.items()
            ]
        )

    path = _build_path(minio.bucket, "crm", "tickets", batch_date)

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
    asset=tickets,
    description="Verify the landed CRM tickets snapshot contains at least one row",
)
def tickets_not_empty(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "crm", "tickets", batch_date)
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
    asset=tickets,
    description="Verify ticket_id has no null values",
)
def tickets_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "crm", "tickets", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "ticket_id"
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
            "null_ticket_ids": dg.MetadataValue.int(null_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )


@dg.asset_check(
    asset=tickets,
    description="Verify ticket_id has no duplicate values",
)
def tickets_unique_pks(
    context: dg.AssetCheckExecutionContext,
    minio: MinIOResource,
):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, "crm", "tickets", batch_date)
    df = _read_parquet(minio, path)

    pk_col = "ticket_id"
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
            "duplicate_ticket_ids": dg.MetadataValue.int(dup_count),
            "partition": dg.MetadataValue.text(batch_date),
        },
    )
