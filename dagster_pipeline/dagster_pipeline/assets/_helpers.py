from pathlib import Path

import dagster as dg
import pandas as pd
import pyarrow as pa

from dagster_pipeline.resources import ClickHouseResource

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


# ── ClickHouse bronze helpers ────────────────────────────────────────────

_BRONZE_DB = "wanderfuel"

# Map Dagster bronze asset name -> ClickHouse bronze table.
BRONZE_TABLES: dict[str, str] = {
    "bronze_customers": "bronze_customers",
    "bronze_hotel_bookings": "bronze_hotel_bookings",
    "bronze_flights": "bronze_flights",
    "bronze_experiences": "bronze_experiences",
    "bronze_tickets": "bronze_tickets",
}


def _iter_partition_windows(context, partitions_def) -> list[tuple[str, "dg.TimeWindow"]]:
    """Yield (partition_key, TimeWindow) for every partition in the current run.

    Works uniformly for single-partition runs (`--partition`) and single-run
    partition ranges (`--partition-range` with `BackfillPolicy.single_run()`).
    """
    from dagster import TimeWindow

    windows: list[tuple[str, "dg.TimeWindow"]] = []
    for key in context.partition_keys:
        start = partitions_def.start_time_for_partition_key(key)
        end = partitions_def.end_time_for_partition_key(key)
        windows.append((key, TimeWindow(start, end)))
    return windows


def _split_sql(sql: str) -> list[str]:
    """Split a SQL script into individual statements.

    `clickhouse-connect`'s `command()` rejects multi-statement payloads,
    so we split on `;` outside line comments. Naive but sufficient for
    the schema DDL (no string literals containing `;`).
    """
    statements: list[str] = []
    buffer: list[str] = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        buffer.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(buffer).rstrip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            buffer = []
    tail = "\n".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def _ensure_bronze_schema(clickhouse: ClickHouseResource) -> None:
    """Apply bronze DDL idempotently. Safe to call on every asset run."""
    sql_path = Path(__file__).resolve().parent.parent / "bronze_schema.sql"
    client = clickhouse.get_client()
    try:
        for stmt in _split_sql(sql_path.read_text(encoding="utf-8")):
            client.command(stmt)
    finally:
        client.close()


def _truncate_partition(
    clickhouse: ClickHouseResource,
    asset_name: str,
    batch_date: str,
) -> None:
    """Make the daily landing idempotent: wipe rows for this partition before insert."""
    table = BRONZE_TABLES[asset_name]
    client = clickhouse.get_client()
    try:
        client.command(
            f"ALTER TABLE {_BRONZE_DB}.{table} DELETE WHERE ingest_date = toDate(%(d)s)",
            parameters={"d": batch_date},
        )
    finally:
        client.close()


def _insert_bronze(
    clickhouse: ClickHouseResource,
    asset_name: str,
    df: pd.DataFrame,
    batch_date: str,
) -> int:
    """Insert the day's DataFrame into the corresponding bronze table.

    Tries pyarrow-based insert first (fast, type-preserving); falls back to
    `insert_df` if the arrow path raises on type conversion. Always fills the
    `ingest_date` column. Returns the number of rows inserted.
    """
    table = BRONZE_TABLES[asset_name]

    if "ingest_date" not in df.columns:
        df = df.assign(ingest_date=batch_date)

    if df.empty:
        return 0

    full_table = f"{_BRONZE_DB}.{table}"
    client = clickhouse.get_client()
    try:
        arrow_table = pa.Table.from_pandas(df, preserve_index=False)
        client.insert_arrow(full_table, arrow_table)
    except Exception as arrow_exc:
        try:
            client.insert_df(full_table, df)
        except Exception:
            raise arrow_exc
    finally:
        client.close()
    return len(df)


def _read_bronze(
    clickhouse: ClickHouseResource,
    asset_name: str,
    batch_date: str | list[str] | None = None,
) -> pd.DataFrame:
    """Read back one or more partitions from a bronze ClickHouse table.

    `batch_date` may be a single `"YYYY-MM-DD"` string or a list of such
    strings (for single-run partition ranges). If omitted, the entire
    bronze table is returned (used by checks when partition scope is empty).
    """
    table = BRONZE_TABLES[asset_name]
    client = clickhouse.get_client()
    try:
        if batch_date is None:
            return client.query_df(f"SELECT * FROM {_BRONZE_DB}.{table}")
        if isinstance(batch_date, list):
            if not batch_date:
                return client.query_df(
                    f"SELECT * FROM {_BRONZE_DB}.{table} WHERE ingest_date = toDate('1970-01-01')"
                )
            dates_csv = ",".join(f"toDate('{d}')" for d in batch_date)
            return client.query_df(
                f"SELECT * FROM {_BRONZE_DB}.{table} WHERE ingest_date IN ({dates_csv})"
            )
        return client.query_df(
            f"SELECT * FROM {_BRONZE_DB}.{table} WHERE ingest_date = toDate(%(d)s)",
            parameters={"d": batch_date},
        )
    finally:
        client.close()


def _column_schema(df: pd.DataFrame) -> dg.MetadataValue:
    return dg.MetadataValue.table_schema(
        dg.TableSchema(
            columns=[
                dg.TableColumn(name=col, type=_map_dtype(dtype))
                for col, dtype in df.dtypes.items()
            ]
        )
    )


