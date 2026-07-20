from datetime import datetime

import dagster as dg
import pandas as pd

from dagster_pipeline.resources import ClickHouseResource, SFTPSourceResource
from dagster_pipeline.assets._helpers import (
    _column_schema,
    _ensure_bronze_schema,
    _insert_bronze,
    _read_bronze,
    _truncate_partition,
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")

# bronze_tickets stays on the default multi_run BackfillPolicy: each
# partition is materialized in its own run (one SFTP fetch per run). The
# iteration pattern below uses context.partition_keys (a single-element list
# in multi_run mode) so the code reads identically across both policies.


@dg.asset(
    name="bronze_tickets",
    description=(
        "Daily slice of CRM support tickets from SFTP, landed directly into "
        "ClickHouse bronze_tickets. Reads the partition-keyed JSON file "
        "`tickets_<YYYYMMDD>.json` from the CRM SFTP server. Contains support "
        "interactions in Bahasa Indonesia with customer identity data "
        "(email + phone) used as the identity bridge between sources. "
        "Uses the default multi_run backfill policy — each partition is "
        "materialized in its own run."
    ),
    group_name="bronze",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["table", "clickhouse"],
    partitions_def=daily_partitions,
)
def bronze_tickets(
    context: dg.AssetExecutionContext,
    crm_sftp: SFTPSourceResource,
    clickhouse: ClickHouseResource,
):
    _ensure_bronze_schema(clickhouse)

    total_rows = 0
    schema_df = None
    source_files = []
    for batch_date in context.partition_keys:
        context.log.info(f"Landing CRM tickets for {batch_date}")
        _truncate_partition(clickhouse, "bronze_tickets", batch_date)

        dt = datetime.strptime(batch_date, "%Y-%m-%d")
        filename = f"tickets_{dt.strftime('%Y%m%d')}.json"
        source_files.append(filename)

        data = crm_sftp.read_json(filename)
        df = pd.DataFrame(data)

        rows = 0
        if not df.empty:
            rows = _insert_bronze(clickhouse, "bronze_tickets", df, batch_date)
            if schema_df is None:
                schema_df = df
        context.log.info(f"Landed {rows} ticket rows for {batch_date}")
        total_rows += rows

    metadata = {
        "dagster/row_count": dg.MetadataValue.int(total_rows),
        "table": dg.MetadataValue.text("wanderfuel.bronze_tickets"),
        "partitions": dg.MetadataValue.json(context.partition_keys),
        "source_files": dg.MetadataValue.json(source_files),
    }
    if schema_df is not None:
        metadata["dagster/column_schema"] = _column_schema(schema_df)

    return dg.MaterializeResult(metadata=metadata)


@dg.asset_check(
    asset=bronze_tickets,
    description="Verify the landed CRM tickets slice contains at least one row",
)
def bronze_tickets_not_empty(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_tickets", keys)
    row_count = len(df)
    return dg.AssetCheckResult(
        passed=row_count > 0,
        metadata={
            "dagster/row_count": dg.MetadataValue.int(row_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_tickets,
    description="Verify ticket_id has no null values",
)
def bronze_tickets_no_null_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_tickets", keys)

    pk_col = "ticket_id"
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
            "null_ticket_ids": dg.MetadataValue.int(null_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )


@dg.asset_check(
    asset=bronze_tickets,
    description="Verify ticket_id has no duplicate values within each partition",
)
def bronze_tickets_unique_pks(
    context: dg.AssetCheckExecutionContext,
    clickhouse: ClickHouseResource,
):
    keys = list(context.partition_keys)
    df = _read_bronze(clickhouse, "bronze_tickets", keys)

    pk_col = "ticket_id"
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
            "duplicate_ticket_ids": dg.MetadataValue.int(dup_count),
            "partitions": dg.MetadataValue.json(keys),
        },
    )